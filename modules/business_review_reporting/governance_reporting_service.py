# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         governance_reporting_service.py
# Path:         modules/business_review_reporting/governance_reporting_service.py
#
# Summary:      Provides implementation support for the business review reporting workflow.
# Purpose:      Supports the business review reporting layer inside the modular repository architecture.
# Scope:        internal
# Status:       stable
#
# Author(s):    Morteza Taleblou
# Website:      https://taleblou.ir/
# Repository:   https://github.com/taleblou/RetailOps-Data-AI-Platform
#
# License:      Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
# Copyright:    (c) 2025 Morteza Taleblou
#
# Notes:
#   - Main types: None.
#   - Key APIs: build_anomaly_investigation_report, get_anomaly_investigation_report, build_fulfillment_control_tower_report, get_fulfillment_control_tower_report, build_ai_governance_trust_report, get_ai_governance_trust_report, ...
#   - Dependencies: __future__, csv, collections, datetime, pathlib, typing, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from core.monitoring.service import get_or_create_monitoring_artifact
from modules.common.upload_utils import (
    canonical_value,
    iter_normalized_rows,
    parse_iso_date,
    read_json_or_none,
    resolve_uploaded_csv_path,
    to_float,
    to_text,
    utc_now_iso,
    write_json,
)
from modules.fulfillment_sla_intelligence.service import build_fulfillment_sla_artifact
from modules.ml_registry.service import run_model_registry
from modules.sales_anomaly_intelligence.service import build_sales_anomaly_artifact

GOVERNANCE_REPORTING_VERSION = "governance-reporting-v1"
GOVERNANCE_REPORTING_REFERENCE_DATE = date(2026, 3, 29)
GOVERNANCE_REPORT_INDEX = [
    {
        "report_name": "anomaly_investigation_pack",
        "endpoint": "/api/v1/business-reports/anomaly-investigation",
    },
    {
        "report_name": "fulfillment_control_tower_report",
        "endpoint": "/api/v1/business-reports/fulfillment-control-tower",
    },
    {
        "report_name": "ai_governance_and_trust_report",
        "endpoint": "/api/v1/business-reports/ai-governance-trust",
    },
    {
        "report_name": "data_quality_and_pipeline_reliability_report",
        "endpoint": "/api/v1/business-reports/data-quality-pipeline-reliability",
    },
]


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _parse_return_flag(row: dict[str, str]) -> bool:
    status = canonical_value(row, "returned", "is_returned", "return_flag").lower()
    if status in {"1", "true", "yes", "y", "returned"}:
        return True
    order_status = canonical_value(row, "order_status", "status").lower()
    if order_status in {"returned", "refund", "refunded", "exchange"}:
        return True
    returned_qty = to_float(canonical_value(row, "returned_qty", "return_quantity"), default=0.0)
    return returned_qty > 0.0


def _delay_state(row: dict[str, str]) -> tuple[bool, bool, float]:
    promised_date = parse_iso_date(canonical_value(row, "promised_date", "promise_date"))
    actual_delivery_date = parse_iso_date(
        canonical_value(row, "actual_delivery_date", "delivered_date", "delivery_date")
    )
    shipment_status = canonical_value(row, "shipment_status", "status").lower()
    if promised_date is None:
        return False, False, 0.0
    comparator = actual_delivery_date or GOVERNANCE_REPORTING_REFERENCE_DATE
    delay_days = float((comparator - promised_date).days)
    delayed = actual_delivery_date is not None and delay_days > 0
    open_breach = actual_delivery_date is None and delay_days > 0
    if shipment_status in {"late", "delayed"}:
        delayed = True
    return delayed, open_breach, max(delay_days, 0.0)


def _anomaly_severity(delta_ratio: float) -> str:
    magnitude = abs(delta_ratio)
    if magnitude >= 1.0:
        return "critical"
    if magnitude >= 0.6:
        return "high"
    if magnitude >= 0.35:
        return "watch"
    return "low"


def _fulfillment_priority(sla_band: str, delay_days: float, revenue_at_risk: float) -> str:
    if sla_band == "breach_risk" and (delay_days >= 3.0 or revenue_at_risk >= 250.0):
        return "critical"
    if sla_band == "delayed" and (delay_days >= 3.0 or revenue_at_risk >= 250.0):
        return "high"
    if sla_band in {"breach_risk", "delayed", "in_flight"}:
        return "watch"
    return "low"


def _governance_band(
    *, critical_alerts: int, total_alerts: int, avg_drift: float, avg_calibration: float
) -> str:
    if critical_alerts > 0 or avg_drift >= 0.25 or avg_calibration >= 0.12:
        return "restricted"
    if total_alerts > 0 or avg_drift >= 0.15 or avg_calibration >= 0.08:
        return "watch"
    return "trusted"


def _pipeline_band(*, critical_count: int, warning_count: int, freshness_days: float) -> str:
    if critical_count > 0 or freshness_days >= 14.0:
        return "fragile"
    if warning_count > 0 or freshness_days >= 7.0:
        return "watch"
    return "healthy"


def _monitoring_dependencies(artifact_dir: Path) -> dict[str, Path]:
    dependency_dir = artifact_dir / "dependencies"
    monitoring_dir = dependency_dir / "monitoring"
    return {
        "forecast_artifact_dir": dependency_dir / "forecasts",
        "shipment_artifact_dir": dependency_dir / "shipment_risk",
        "stockout_artifact_dir": dependency_dir / "stockout_risk",
        "serving_artifact_dir": dependency_dir / "serving",
        "registry_artifact_dir": dependency_dir / "model_registry",
        "monitoring_artifact_dir": monitoring_dir,
        "override_dir": monitoring_dir / "overrides",
    }


def _read_headers(csv_path: Path) -> list[str]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
    return [to_text(item) for item in header if to_text(item)]


def build_anomaly_investigation_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = (
        artifact_dir / f"{upload_id}_governance_reporting_anomaly_investigation_report.json"
    )
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    anomaly_artifact = build_sales_anomaly_artifact(
        upload_id,
        uploads_dir,
        artifact_dir / "dependencies" / "sales_anomaly",
        refresh,
    )
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    day_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "orders": set(),
            "revenue": 0.0,
            "promo_orders": set(),
            "delayed_orders": set(),
            "returned_orders": set(),
            "category_revenue": defaultdict(float),
            "store_revenue": defaultdict(float),
        }
    )

    for row in iter_normalized_rows(csv_path):
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        if order_date is None:
            continue
        order_day = order_date.isoformat()
        order_id = canonical_value(row, "order_id") or f"synthetic-{order_day}"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        store_code = canonical_value(row, "store_code", "store", "store_id") or "unknown"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        revenue = round(quantity * unit_price, 2)
        promo_code = canonical_value(row, "promo_code", "coupon_code", "discount_code") or ""
        returned = _parse_return_flag(row)
        delayed, _, _ = _delay_state(row)
        current = day_rollups[order_day]
        current["orders"].add(order_id)
        current["revenue"] += revenue
        current["category_revenue"][category] += revenue
        current["store_revenue"][store_code] += revenue
        if promo_code and promo_code.lower() not in {"none", "no_promo"}:
            current["promo_orders"].add(order_id)
        if delayed:
            current["delayed_orders"].add(order_id)
        if returned:
            current["returned_orders"].add(order_id)

    findings: list[dict[str, Any]] = []
    critical_anomaly_count = 0
    highest_priority_date = ""
    highest_priority_score = -1.0
    for item in anomaly_artifact.get("days", []):
        anomaly_type = to_text(item.get("anomaly_type"))
        if anomaly_type == "normal":
            continue
        order_date = to_text(item.get("order_date"))
        rollup = day_rollups.get(order_date, {})
        order_count = len(rollup.get("orders", set()))
        revenue = round(to_float(item.get("revenue"), default=0.0), 2)
        baseline_revenue = round(to_float(item.get("baseline_revenue"), default=0.0), 2)
        estimated_revenue_gap = round(abs(revenue - baseline_revenue), 2)
        promo_order_share = _safe_rate(
            float(len(rollup.get("promo_orders", set()))),
            float(order_count),
        )
        delayed_order_rate = _safe_rate(
            float(len(rollup.get("delayed_orders", set()))),
            float(order_count),
        )
        return_rate = _safe_rate(
            float(len(rollup.get("returned_orders", set()))),
            float(order_count),
        )
        top_store = "unknown"
        if rollup.get("store_revenue"):
            top_store = max(
                rollup["store_revenue"].items(),
                key=lambda candidate: candidate[1],
            )[0]
        delta_ratio = round(to_float(item.get("delta_ratio"), default=0.0), 4)
        severity = _anomaly_severity(delta_ratio)
        if severity == "critical":
            critical_anomaly_count += 1
        if promo_order_share >= 0.45 and anomaly_type == "spike":
            likely_driver = "promotion intensity and price-led volume spike"
            recommended_action = "validate promo uplift quality and protect margin before reuse"
        elif delayed_order_rate >= 0.25:
            likely_driver = "fulfillment disruption or promise-date slippage"
            recommended_action = "cross-check late orders and open a fulfillment recovery review"
        elif return_rate >= 0.15:
            likely_driver = "returns pressure or post-purchase dissatisfaction"
            recommended_action = "inspect return reasons and isolate product or channel issues"
        else:
            likely_driver = f"commercial mix shift concentrated in {to_text(item.get('dominant_category')) or 'core demand'}"
            recommended_action = "review mix, price, and availability drivers behind the deviation"
        investigation_focus = f"Start with {top_store} and {to_text(item.get('dominant_category')) or 'uncategorized'} lines."
        priority_score = abs(delta_ratio) + delayed_order_rate + return_rate + promo_order_share
        if priority_score > highest_priority_score:
            highest_priority_score = priority_score
            highest_priority_date = order_date
        findings.append(
            {
                "order_date": order_date,
                "anomaly_type": anomaly_type,
                "severity": severity,
                "affected_order_count": order_count,
                "revenue": revenue,
                "baseline_revenue": baseline_revenue,
                "estimated_revenue_gap": estimated_revenue_gap,
                "delta_ratio": delta_ratio,
                "dominant_category": to_text(item.get("dominant_category") or "uncategorized"),
                "promo_order_share": round(promo_order_share, 4),
                "delayed_order_rate": round(delayed_order_rate, 4),
                "return_rate": round(return_rate, 4),
                "top_store": top_store,
                "likely_driver": likely_driver,
                "investigation_focus": investigation_focus,
                "recommended_action": recommended_action,
            }
        )

    findings.sort(
        key=lambda candidate: (
            candidate["severity"] != "critical",
            candidate["severity"] != "high",
            -abs(candidate["delta_ratio"]),
        )
    )
    summary = dict(anomaly_artifact.get("summary", {}))
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": GOVERNANCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "anomaly_investigation_pack",
        "summary": {
            "day_count": int(summary.get("day_count", 0)),
            "anomaly_count": int(summary.get("anomaly_count", len(findings))),
            "critical_anomaly_count": critical_anomaly_count,
            "spike_count": int(summary.get("spike_count", 0)),
            "drop_count": int(summary.get("drop_count", 0)),
            "largest_positive_delta_ratio": round(
                to_float(summary.get("largest_positive_delta_ratio"), default=0.0),
                4,
            ),
            "largest_negative_delta_ratio": round(
                to_float(summary.get("largest_negative_delta_ratio"), default=0.0),
                4,
            ),
            "highest_priority_date": highest_priority_date,
        },
        "findings": findings,
    }
    return write_json(artifact_path, payload)


def get_anomaly_investigation_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_anomaly_investigation_report(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["findings"] = list(payload.get("findings", []))[:limit]
    return payload


def build_fulfillment_control_tower_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = (
        artifact_dir / f"{upload_id}_governance_reporting_fulfillment_control_tower_report.json"
    )
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    fulfillment_artifact = build_fulfillment_sla_artifact(
        upload_id,
        uploads_dir,
        artifact_dir / "dependencies" / "fulfillment",
        refresh,
    )
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    order_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "customer_id": "guest",
            "store_code": "unknown",
            "region": "unknown",
            "carrier": "unknown",
            "shipment_status": "unknown",
            "revenue_at_risk": 0.0,
        }
    )
    for row in iter_normalized_rows(csv_path):
        order_id = canonical_value(row, "order_id") or "unknown-order"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        current = order_rollups[order_id]
        current["customer_id"] = (
            canonical_value(row, "customer_id", "buyer_id") or current["customer_id"]
        )
        current["store_code"] = canonical_value(row, "store_code", "store") or current["store_code"]
        current["region"] = canonical_value(row, "region", "shipping_region") or current["region"]
        current["carrier"] = (
            canonical_value(row, "carrier", "shipping_carrier") or current["carrier"]
        )
        current["shipment_status"] = (
            canonical_value(row, "shipment_status", "status") or current["shipment_status"]
        )
        current["revenue_at_risk"] += round(quantity * unit_price, 2)

    carrier_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_count": 0,
            "delayed": 0,
            "breach": 0,
            "on_time": 0,
            "delay_days_total": 0.0,
            "delay_samples": 0,
        }
    )
    open_orders: list[dict[str, Any]] = []
    delayed_order_count = 0
    breach_risk_order_count = 0
    on_time_order_count = 0
    average_delay_samples = 0
    total_delay_days = 0.0
    revenue_at_risk = 0.0
    critical_order_count = 0

    for item in fulfillment_artifact.get("orders", []):
        order_id = to_text(item.get("order_id") or "unknown-order")
        enriched = order_rollups.get(order_id, {})
        carrier = to_text(item.get("carrier") or enriched.get("carrier") or "unknown")
        sla_band = to_text(item.get("sla_band") or "unknown")
        delay_days = round(to_float(item.get("delay_days"), default=0.0), 2)
        current_revenue = round(to_float(enriched.get("revenue_at_risk"), default=0.0), 2)
        priority_band = _fulfillment_priority(sla_band, delay_days, current_revenue)
        if priority_band == "critical":
            critical_order_count += 1
        if sla_band == "delayed":
            delayed_order_count += 1
            total_delay_days += delay_days
            average_delay_samples += 1
        if sla_band == "breach_risk":
            breach_risk_order_count += 1
            total_delay_days += delay_days
            average_delay_samples += 1
        if sla_band == "on_time":
            on_time_order_count += 1
        if sla_band in {"delayed", "breach_risk", "in_flight"}:
            revenue_at_risk += current_revenue
            if sla_band == "breach_risk":
                root_signal = "promised date breached without delivery confirmation"
            elif delay_days >= 3.0:
                root_signal = "multi-day delivery overrun"
            else:
                root_signal = "active fulfillment queue pressure"
            open_orders.append(
                {
                    "order_id": order_id,
                    "customer_id": to_text(enriched.get("customer_id") or "guest"),
                    "store_code": to_text(enriched.get("store_code") or "unknown"),
                    "region": to_text(item.get("region") or enriched.get("region") or "unknown"),
                    "carrier": carrier,
                    "shipment_status": to_text(
                        item.get("shipment_status") or enriched.get("shipment_status") or "unknown"
                    ),
                    "promised_date": to_text(item.get("promised_date")),
                    "actual_delivery_date": to_text(item.get("actual_delivery_date")),
                    "delay_days": delay_days,
                    "revenue_at_risk": current_revenue,
                    "priority_band": priority_band,
                    "sla_band": sla_band,
                    "root_signal": root_signal,
                    "recommended_action": to_text(item.get("recommended_action")),
                }
            )
        current_carrier = carrier_rollups[carrier]
        current_carrier["order_count"] += 1
        if sla_band == "delayed":
            current_carrier["delayed"] += 1
        if sla_band == "breach_risk":
            current_carrier["breach"] += 1
        if sla_band == "on_time":
            current_carrier["on_time"] += 1
        if delay_days > 0.0:
            current_carrier["delay_days_total"] += delay_days
            current_carrier["delay_samples"] += 1

    carrier_scores: list[dict[str, Any]] = []
    worst_carrier = ""
    worst_carrier_score = -1.0
    for carrier, metrics in carrier_rollups.items():
        order_count = int(metrics["order_count"])
        average_delay_days = (
            round(
                metrics["delay_days_total"] / metrics["delay_samples"],
                2,
            )
            if metrics["delay_samples"]
            else 0.0
        )
        on_time_rate = _safe_rate(float(metrics["on_time"]), float(order_count))
        escalation_rate = _safe_rate(
            float(metrics["delayed"] + metrics["breach"]),
            float(order_count),
        )
        if metrics["breach"] > 0:
            recommended_action = "escalate carrier and rebalance open promises"
        elif escalation_rate >= 0.3:
            recommended_action = "review lane capacity and update ETA governance"
        else:
            recommended_action = "keep standard monitoring cadence"
        carrier_scores.append(
            {
                "carrier": carrier,
                "order_count": order_count,
                "delayed_order_count": int(metrics["delayed"]),
                "open_breach_count": int(metrics["breach"]),
                "on_time_rate": round(on_time_rate, 4),
                "average_delay_days": average_delay_days,
                "escalation_rate": round(escalation_rate, 4),
                "recommended_action": recommended_action,
            }
        )
        current_score = escalation_rate + average_delay_days / 10.0
        if current_score > worst_carrier_score:
            worst_carrier_score = current_score
            worst_carrier = carrier

    open_orders.sort(
        key=lambda item: (
            item["priority_band"] != "critical",
            item["priority_band"] != "high",
            -item["revenue_at_risk"],
            -item["delay_days"],
        )
    )
    carrier_scores.sort(key=lambda item: (-item["open_breach_count"], item["on_time_rate"]))
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": GOVERNANCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "fulfillment_control_tower_report",
        "summary": {
            "open_order_count": len(open_orders),
            "delayed_order_count": delayed_order_count,
            "breach_risk_order_count": breach_risk_order_count,
            "on_time_order_count": on_time_order_count,
            "average_delay_days": round(
                total_delay_days / average_delay_samples,
                2,
            )
            if average_delay_samples
            else 0.0,
            "revenue_at_risk": round(revenue_at_risk, 2),
            "critical_order_count": critical_order_count,
            "worst_carrier": worst_carrier,
        },
        "carrier_scores": carrier_scores,
        "open_orders": open_orders,
    }
    return write_json(artifact_path, payload)


def get_fulfillment_control_tower_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_fulfillment_control_tower_report(
        upload_id,
        uploads_dir,
        artifact_dir,
        refresh,
    )
    payload = dict(payload)
    payload["open_orders"] = list(payload.get("open_orders", []))[:limit]
    return payload


def build_ai_governance_trust_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = (
        artifact_dir / f"{upload_id}_governance_reporting_ai_governance_trust_report.json"
    )
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    paths = _monitoring_dependencies(artifact_dir)
    monitoring_artifact = get_or_create_monitoring_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=paths["forecast_artifact_dir"],
        shipment_artifact_dir=paths["shipment_artifact_dir"],
        stockout_artifact_dir=paths["stockout_artifact_dir"],
        serving_artifact_dir=paths["serving_artifact_dir"],
        registry_artifact_dir=paths["registry_artifact_dir"],
        artifact_dir=paths["monitoring_artifact_dir"],
        override_dir=paths["override_dir"],
        refresh=refresh,
    )
    registry_payload = run_model_registry(
        artifact_dir=paths["registry_artifact_dir"],
        refresh=refresh,
    ).to_dict()
    registry_details = list(registry_payload.get("registry_details") or [])
    ml_checks = list(monitoring_artifact.get("ml_checks") or [])
    alerts = list(monitoring_artifact.get("alerts") or [])
    dashboard_metrics = list(monitoring_artifact.get("dashboard_metrics") or [])

    registries: list[dict[str, Any]] = []
    calibration_errors: list[float] = []
    drift_scores: list[float] = []
    promotion_ready_registry_count = 0
    for registry in registry_details:
        aliases = registry.get("aliases") or {}
        versions = list(registry.get("versions") or [])
        champion_version = to_text(aliases.get("champion"))
        challenger_version = to_text(aliases.get("challenger"))
        shadow_version = to_text(aliases.get("shadow"))
        champion = next(
            (item for item in versions if to_text(item.get("model_version")) == champion_version),
            {},
        )
        challenger = next(
            (item for item in versions if to_text(item.get("model_version")) == challenger_version),
            {},
        )
        contract = registry.get("evaluation_contract") or {}
        primary_metric = to_text(contract.get("primary_metric") or "score")
        optimization_direction = to_text(contract.get("optimization_direction") or "min")
        calibration_error = round(to_float(champion.get("calibration_error"), default=0.0), 4)
        drift_score = round(to_float(champion.get("drift_score"), default=0.0), 4)
        calibration_errors.append(calibration_error)
        drift_scores.append(drift_score)
        promotion_eligible = bool(challenger.get("promotion_eligible", False))
        if promotion_eligible:
            promotion_ready_registry_count += 1
        active_alert_count = 0
        max_calibration = to_float(contract.get("max_calibration_error"), default=0.08)
        max_drift = to_float(contract.get("max_drift_score"), default=0.25)
        if calibration_error > max_calibration:
            active_alert_count += 1
        if drift_score > max_drift:
            active_alert_count += 1
        if not bool(champion.get("evaluation_passed", False)):
            active_alert_count += 1
        if active_alert_count >= 2:
            trust_band = "fragile"
            recommended_action = (
                "limit automation and schedule model review with rollback readiness"
            )
        elif active_alert_count == 1:
            trust_band = "watch"
            recommended_action = "review guardrails and compare champion with challenger"
        else:
            trust_band = "trusted"
            recommended_action = "keep champion in service and monitor standard drift cadence"
        registries.append(
            {
                "registry_name": to_text(registry.get("registry_name")),
                "champion_version": champion_version,
                "challenger_version": challenger_version,
                "shadow_version": shadow_version,
                "primary_metric": primary_metric,
                "optimization_direction": optimization_direction,
                "champion_metric_value": round(
                    to_float((champion.get("metrics") or {}).get(primary_metric), default=0.0),
                    4,
                ),
                "baseline_metric_value": round(
                    to_float(
                        (champion.get("baseline_metrics") or {}).get(primary_metric), default=0.0
                    ),
                    4,
                ),
                "calibration_error": calibration_error,
                "drift_score": drift_score,
                "promotion_eligible": promotion_eligible,
                "active_alert_count": active_alert_count,
                "trust_band": trust_band,
                "recommended_action": recommended_action,
            }
        )

    registries.sort(
        key=lambda item: (
            item["trust_band"] != "fragile",
            item["trust_band"] != "watch",
            -item["active_alert_count"],
        )
    )
    avg_calibration = (
        round(sum(calibration_errors) / len(calibration_errors), 4) if calibration_errors else 0.0
    )
    avg_drift = round(sum(drift_scores) / len(drift_scores), 4) if drift_scores else 0.0
    critical_alerts = sum(1 for item in alerts if to_text(item.get("severity")) == "critical")
    governance_band = _governance_band(
        critical_alerts=critical_alerts,
        total_alerts=len(alerts),
        avg_drift=avg_drift,
        avg_calibration=avg_calibration,
    )
    alert_highlights = [
        {
            "category": to_text(item.get("category")),
            "check_name": to_text(item.get("check_name")),
            "severity": to_text(item.get("severity")),
            "metric_name": to_text(item.get("metric_name")),
            "metric_value": round(to_float(item.get("metric_value"), default=0.0), 4),
            "threshold_value": round(to_float(item.get("threshold_value"), default=0.0), 4),
            "message": to_text(item.get("message")),
            "recommended_action": to_text(item.get("recommended_action")),
        }
        for item in ml_checks
        if to_text(item.get("status")) != "pass"
    ]
    metric_rows = [
        {
            "metric_name": to_text(item.get("metric_name")),
            "value": round(to_float(item.get("value"), default=0.0), 4),
            "unit": to_text(item.get("unit")),
            "status": to_text(item.get("status")),
            "description": to_text(item.get("description")),
        }
        for item in dashboard_metrics
    ]
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": GOVERNANCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "ai_governance_and_trust_report",
        "summary": {
            "registry_count": len(registries),
            "champion_registry_count": sum(1 for item in registries if item["champion_version"]),
            "promotion_ready_registry_count": promotion_ready_registry_count,
            "total_alerts": len(alerts),
            "critical_alerts": critical_alerts,
            "override_count": int(
                (monitoring_artifact.get("override_summary") or {}).get("total_overrides", 0)
            ),
            "retrain_recommended": bool(
                (monitoring_artifact.get("summary") or {}).get("retrain_recommended", False)
            ),
            "disable_prediction_recommended": bool(
                (monitoring_artifact.get("summary") or {}).get(
                    "disable_prediction_recommended",
                    False,
                )
            ),
            "average_calibration_error": avg_calibration,
            "average_drift_score": avg_drift,
            "governance_band": governance_band,
        },
        "registries": registries,
        "alert_highlights": alert_highlights,
        "dashboard_metrics": metric_rows,
    }
    return write_json(artifact_path, payload)


def get_ai_governance_trust_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    payload = build_ai_governance_trust_report(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["alert_highlights"] = list(payload.get("alert_highlights", []))[:limit]
    return payload


def build_data_quality_pipeline_reliability_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = (
        artifact_dir / f"{upload_id}_governance_reporting_data_quality_pipeline_reliability.json"
    )
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    paths = _monitoring_dependencies(artifact_dir)
    monitoring_artifact = get_or_create_monitoring_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=paths["forecast_artifact_dir"],
        shipment_artifact_dir=paths["shipment_artifact_dir"],
        stockout_artifact_dir=paths["stockout_artifact_dir"],
        serving_artifact_dir=paths["serving_artifact_dir"],
        registry_artifact_dir=paths["registry_artifact_dir"],
        artifact_dir=paths["monitoring_artifact_dir"],
        override_dir=paths["override_dir"],
        refresh=refresh,
    )
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    headers = _read_headers(csv_path)
    data_checks = list(monitoring_artifact.get("data_checks") or [])
    alerts = list(monitoring_artifact.get("alerts") or [])
    summary = monitoring_artifact.get("summary") or {}

    latest_event_date = ""
    freshness_days = 0.0
    check_rows: list[dict[str, Any]] = []
    warning_count = 0
    critical_count = 0
    for item in data_checks:
        status = to_text(item.get("status"))
        if status == "warn":
            warning_count += 1
        if status == "critical":
            critical_count += 1
        metadata = item.get("metadata") or {}
        if to_text(item.get("check_name")) == "freshness":
            latest_event_date = to_text(metadata.get("latest_event_date"))
            freshness_days = round(to_float(item.get("metric_value"), default=0.0), 2)
        evidence_parts = []
        if metadata.get("source_row_count") is not None:
            evidence_parts.append(f"rows={int(to_float(metadata.get('source_row_count')))}")
        if metadata.get("source_file_count") is not None:
            evidence_parts.append(f"files={int(to_float(metadata.get('source_file_count')))}")
        checked_columns = metadata.get("checked_columns") or []
        if checked_columns:
            evidence_parts.append(
                "checked_columns=" + ", ".join(str(item) for item in checked_columns[:6])
            )
        if metadata.get("latest_event_date"):
            evidence_parts.append(f"latest_event_date={metadata.get('latest_event_date')}")
        check_rows.append(
            {
                "check_name": to_text(item.get("check_name")),
                "status": status,
                "metric_name": to_text(item.get("metric_name")),
                "metric_value": round(to_float(item.get("metric_value"), default=0.0), 4),
                "threshold_value": round(to_float(item.get("threshold_value"), default=0.0), 4),
                "message": to_text(item.get("message")),
                "recommended_action": to_text(item.get("recommended_action")),
                "evidence": "; ".join(evidence_parts) or "no extra evidence captured",
            }
        )

    pipeline_band = _pipeline_band(
        critical_count=critical_count,
        warning_count=warning_count,
        freshness_days=freshness_days,
    )
    source_row_count = int(to_float(summary.get("source_row_count"), default=0.0))
    source_file_count = int(to_float(summary.get("source_file_count"), default=0.0))
    model_coverage = round(to_float(summary.get("model_coverage"), default=0.0), 4)
    api_latency_ms = round(to_float(summary.get("api_latency_ms"), default=0.0), 2)
    stage_rows = [
        {
            "stage_name": "source_ingestion",
            "status": "critical"
            if critical_count > 0
            else ("warn" if warning_count > 0 else "pass"),
            "detail": (
                f"{source_file_count} source file(s), {source_row_count} rows, latest event {latest_event_date or 'unknown'}."
            ),
            "recommended_action": "rerun extract and confirm source freshness before downstream jobs",
        },
        {
            "stage_name": "canonical_validation",
            "status": "critical"
            if critical_count > 0
            else ("warn" if warning_count > 0 else "pass"),
            "detail": (
                f"Header scan found {len(headers)} columns and {len(check_rows)} active quality checks."
            ),
            "recommended_action": "fix mappings, null spikes, and out-of-range fields before feature builds",
        },
        {
            "stage_name": "model_scoring_readiness",
            "status": (
                "critical"
                if bool(summary.get("disable_prediction_recommended", False))
                else ("warn" if model_coverage < 0.7 else "pass")
            ),
            "detail": (
                f"Model coverage={model_coverage:.4f}, disable_prediction_recommended="
                f"{bool(summary.get('disable_prediction_recommended', False))}."
            ),
            "recommended_action": "close data gaps before publishing automated operational actions",
        },
        {
            "stage_name": "report_delivery",
            "status": "warn" if api_latency_ms > 220.0 else "pass",
            "detail": f"Estimated API latency={api_latency_ms:.2f} ms from monitoring dashboard.",
            "recommended_action": "review serving footprint if control-tower reports become slow",
        },
    ]
    alert_rows = [
        {
            "category": to_text(item.get("category")),
            "severity": to_text(item.get("severity")),
            "check_name": to_text(item.get("check_name")),
            "message": to_text(item.get("message")),
            "recommended_action": to_text(item.get("recommended_action")),
        }
        for item in alerts
        if to_text(item.get("category")) == "data_quality"
    ]
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": GOVERNANCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "data_quality_and_pipeline_reliability_report",
        "summary": {
            "source_file_count": source_file_count,
            "source_row_count": source_row_count,
            "warning_check_count": warning_count,
            "critical_check_count": critical_count,
            "freshness_days": freshness_days,
            "latest_event_date": latest_event_date,
            "pipeline_reliability_band": pipeline_band,
            "schema_coverage_note": (
                f"Header scan found {len(headers)} column(s): " + ", ".join(headers[:8])
            ),
        },
        "data_checks": check_rows,
        "pipeline_stages": stage_rows,
        "alert_highlights": alert_rows,
    }
    return write_json(artifact_path, payload)


def get_data_quality_pipeline_reliability_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    payload = build_data_quality_pipeline_reliability_report(
        upload_id,
        uploads_dir,
        artifact_dir,
        refresh,
    )
    payload = dict(payload)
    payload["alert_highlights"] = list(payload.get("alert_highlights", []))[:limit]
    return payload
