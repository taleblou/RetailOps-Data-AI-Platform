# Project:      RetailOps Data & AI Platform
# Module:       modules.customer_churn_intelligence
# File:         service.py
# Path:         modules/customer_churn_intelligence/service.py
#
# Summary:      Implements the customer churn intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for customer churn intelligence workflows.
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
#   - Key APIs: build_customer_churn_artifact, get_customer_churn_artifact, get_customer_churn_detail
#   - Dependencies: __future__, collections, datetime, pathlib, typing, modules.common.upload_utils, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

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
    to_float,
    to_text,
    utc_now_iso,
    write_json,
)

CUSTOMER_CHURN_VERSION = "risk_retention-customer-churn-v1"
REFERENCE_DATE = date(2026, 3, 29)


def _risk_band(recency_days: int, average_gap_days: float, order_count: int) -> str:
    if order_count <= 1 and recency_days <= 45:
        return "new"
    if recency_days >= 120:
        return "lost"
    if recency_days >= 90:
        return "high"
    if average_gap_days > 0 and recency_days >= average_gap_days * 2.5:
        return "high"
    if recency_days >= 45:
        return "medium"
    return "low"


def _recommended_action(risk_band: str) -> str:
    if risk_band == "lost":
        return "launch win-back offer and manual outreach"
    if risk_band == "high":
        return "send retention campaign within 7 days"
    if risk_band == "medium":
        return "trigger reminder journey and monitor next order"
    if risk_band == "new":
        return "support second-order conversion journey"
    return "maintain loyalty touchpoints"


def build_customer_churn_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_customer_churn_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    customer_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_ids": set(),
            "order_dates": [],
            "revenue": 0.0,
        }
    )
    latest_seen = REFERENCE_DATE

    for row in iter_normalized_rows(csv_path):
        customer_id = canonical_value(row, "customer_id", "buyer_id", "client_id") or "guest"
        order_id = canonical_value(row, "order_id") or f"synthetic-{customer_id}"
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        revenue = round(quantity * unit_price, 2)
        current = customer_rollup[customer_id]
        if order_id not in current["order_ids"]:
            current["order_ids"].add(order_id)
            if order_date is not None:
                current["order_dates"].append(order_date)
                latest_seen = max(latest_seen, order_date)
        current["revenue"] += revenue

    customers = []
    high_risk_customer_count = 0
    lost_customer_count = 0
    total_recency_days = 0.0
    total_churn_score = 0.0

    for customer_id, item in customer_rollup.items():
        order_dates = sorted(set(item["order_dates"]))
        first_order_date = order_dates[0] if order_dates else latest_seen
        last_order_date = order_dates[-1] if order_dates else latest_seen
        order_count = len(item["order_ids"])
        recency_days = max((latest_seen - last_order_date).days, 0)
        gaps = [
            max((order_dates[index] - order_dates[index - 1]).days, 0)
            for index in range(1, len(order_dates))
        ]
        average_gap_days = round(sum(gaps) / len(gaps), 2) if gaps else 0.0
        risk_band = _risk_band(recency_days, average_gap_days, order_count)
        if risk_band in {"high", "lost"}:
            high_risk_customer_count += 1
        if risk_band == "lost":
            lost_customer_count += 1
        gap_divisor = average_gap_days if average_gap_days > 0 else max(30.0, recency_days or 1.0)
        churn_score = min(1.0, round(recency_days / gap_divisor / 2.0, 4))
        total_recency_days += recency_days
        total_churn_score += churn_score
        customers.append(
            {
                "customer_id": customer_id,
                "order_count": order_count,
                "total_revenue": round(float(item["revenue"]), 2),
                "first_order_date": first_order_date.isoformat(),
                "last_order_date": last_order_date.isoformat(),
                "recency_days": recency_days,
                "average_gap_days": average_gap_days,
                "churn_score": churn_score,
                "churn_risk_band": risk_band,
                "recommended_action": _recommended_action(risk_band),
            }
        )

    customers.sort(
        key=lambda item: (
            item["churn_score"],
            item["recency_days"],
            item["total_revenue"],
        ),
        reverse=True,
    )
    customer_count = len(customers)
    summary = {
        "customer_count": customer_count,
        "high_risk_customer_count": high_risk_customer_count,
        "lost_customer_count": lost_customer_count,
        "average_recency_days": round(total_recency_days / customer_count, 2)
        if customer_count
        else 0.0,
        "average_churn_score": round(total_churn_score / customer_count, 4)
        if customer_count
        else 0.0,
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": CUSTOMER_CHURN_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "customers": customers,
    }
    return write_json(artifact_path, payload)


def get_customer_churn_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_customer_churn_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["customers"] = list(payload.get("customers", []))[:limit]
    return payload


def get_customer_churn_detail(
    upload_id: str,
    customer_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_customer_churn_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = customer_id.strip().lower()
    for item in payload.get("customers", []):
        if to_text(item.get("customer_id")).lower() == target:
            return item
    raise FileNotFoundError(f"Customer churn artifact does not contain customer_id={customer_id}.")
