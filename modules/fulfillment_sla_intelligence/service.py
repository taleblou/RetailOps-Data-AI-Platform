from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from modules.common.upload_utils import (
    canonical_value,
    iter_normalized_rows,
    parse_iso_date,
    read_json_or_none,
    resolve_uploaded_csv_path,
    to_text,
    utc_now_iso,
    write_json,
)

PHASE24_FULFILLMENT_SLA_VERSION = "phase24-fulfillment-sla-v1"
REFERENCE_DATE = date(2026, 3, 29)


def _sla_band(delay_days: float, actual_delivery_date: str, shipment_status: str) -> str:
    normalized_status = shipment_status.lower()
    if actual_delivery_date and delay_days <= 0:
        return "on_time"
    if actual_delivery_date and delay_days > 0:
        return "delayed"
    if "delivered" in normalized_status:
        return "delivered_unknown_sla"
    if delay_days > 0:
        return "breach_risk"
    return "in_flight"


def _recommended_action(sla_band: str) -> str:
    if sla_band == "delayed":
        return "open carrier escalation and customer communication"
    if sla_band == "breach_risk":
        return "prioritize order and update ETA"
    if sla_band == "delivered_unknown_sla":
        return "backfill proof-of-delivery timestamp"
    return "monitor standard workflow"


def build_fulfillment_sla_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_fulfillment_sla_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    order_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "carrier": "unknown",
            "region": "unknown",
            "shipment_status": "unknown",
            "promised_date": None,
            "actual_delivery_date": None,
        }
    )
    latest_seen = REFERENCE_DATE

    for row in iter_normalized_rows(csv_path):
        order_id = canonical_value(row, "order_id") or "unknown-order"
        promised_date = parse_iso_date(canonical_value(row, "promised_date", "promise_date"))
        actual_delivery_date = parse_iso_date(
            canonical_value(row, "actual_delivery_date", "delivered_date", "delivery_date")
        )
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        for candidate in [promised_date, actual_delivery_date, order_date]:
            if candidate is not None:
                latest_seen = max(latest_seen, candidate)
        current = order_rollup[order_id]
        current["carrier"] = canonical_value(row, "carrier", "shipping_carrier") or str(
            current["carrier"]
        )
        current["region"] = canonical_value(row, "region", "shipping_region") or str(
            current["region"]
        )
        current["shipment_status"] = canonical_value(row, "shipment_status", "status") or str(
            current["shipment_status"]
        )
        if promised_date is not None:
            current["promised_date"] = promised_date
        if actual_delivery_date is not None:
            current["actual_delivery_date"] = actual_delivery_date

    orders = []
    delayed_order_count = 0
    delivered_order_count = 0
    open_breach_risk_count = 0
    on_time_order_count = 0
    total_delay_days = 0.0
    delayed_days_samples = 0

    for order_id, item in order_rollup.items():
        promised_date = item["promised_date"]
        actual_delivery_date = item["actual_delivery_date"]
        shipment_status = str(item["shipment_status"])
        delay_days = 0.0
        if promised_date is not None:
            comparator = actual_delivery_date or latest_seen
            delay_days = float((comparator - promised_date).days)
        normalized_actual = actual_delivery_date.isoformat() if actual_delivery_date else ""
        normalized_promised = promised_date.isoformat() if promised_date else ""
        sla_band = _sla_band(delay_days, normalized_actual, shipment_status)
        if normalized_actual:
            delivered_order_count += 1
        if sla_band == "on_time":
            on_time_order_count += 1
        if sla_band == "delayed":
            delayed_order_count += 1
            total_delay_days += delay_days
            delayed_days_samples += 1
        if sla_band == "breach_risk":
            open_breach_risk_count += 1
        orders.append(
            {
                "order_id": order_id,
                "carrier": str(item["carrier"]),
                "region": str(item["region"]),
                "shipment_status": shipment_status,
                "promised_date": normalized_promised,
                "actual_delivery_date": normalized_actual,
                "delay_days": round(delay_days, 2),
                "sla_band": sla_band,
                "recommended_action": _recommended_action(sla_band),
            }
        )

    orders.sort(key=lambda item: (item["delay_days"], item["sla_band"]), reverse=True)
    summary = {
        "order_count": len(orders),
        "delivered_order_count": delivered_order_count,
        "delayed_order_count": delayed_order_count,
        "open_breach_risk_count": open_breach_risk_count,
        "on_time_rate": round(on_time_order_count / delivered_order_count, 4)
        if delivered_order_count
        else 0.0,
        "average_delay_days": round(total_delay_days / delayed_days_samples, 2)
        if delayed_days_samples
        else 0.0,
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PHASE24_FULFILLMENT_SLA_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "orders": orders,
    }
    return write_json(artifact_path, payload)


def get_fulfillment_sla_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_fulfillment_sla_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["orders"] = list(payload.get("orders", []))[:limit]
    return payload


def get_fulfillment_sla_order(
    upload_id: str,
    order_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_fulfillment_sla_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = order_id.strip().lower()
    for item in payload.get("orders", []):
        if to_text(item.get("order_id")).lower() == target:
            return item
    raise FileNotFoundError(f"Fulfillment SLA artifact does not contain order_id={order_id}.")
