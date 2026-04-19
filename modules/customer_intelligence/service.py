# Project:      RetailOps Data & AI Platform
# Module:       modules.customer_intelligence
# File:         service.py
# Path:         modules/customer_intelligence/service.py
#
# Summary:      Implements the customer intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for customer intelligence workflows.
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
#   - Key APIs: build_customer_intelligence_artifact, get_customer_intelligence_artifact, get_customer_segment
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

CUSTOMER_INTELLIGENCE_VERSION = "commercial-suite-customer-intelligence-v1"


def _segment(order_count: int, revenue: float, recency_days: int) -> str:
    if order_count >= 4 and revenue >= 500 and recency_days <= 30:
        return "champion"
    if order_count >= 2 and recency_days <= 60:
        return "loyal"
    if order_count == 1 and recency_days <= 45:
        return "new"
    if recency_days > 90:
        return "at_risk"
    return "developing"


def build_customer_intelligence_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_customer_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    customer_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_ids": set(),
            "revenue": 0.0,
            "quantity": 0.0,
            "last_order_date": None,
        }
    )
    latest_seen = date(2026, 3, 29)
    total_revenue = 0.0
    total_orders = 0

    for row in iter_normalized_rows(csv_path):
        customer_id = canonical_value(row, "customer_id", "buyer_id", "client_id") or "guest"
        order_id = canonical_value(row, "order_id") or f"synthetic-{customer_id}"
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        revenue = quantity * unit_price
        current = customer_rollup[customer_id]
        if order_id not in current["order_ids"]:
            current["order_ids"].add(order_id)
            total_orders += 1
        current["revenue"] += revenue
        current["quantity"] += quantity
        if order_date is not None:
            latest_seen = max(latest_seen, order_date)
            if current["last_order_date"] is None or order_date > current["last_order_date"]:
                current["last_order_date"] = order_date
        total_revenue += revenue

    customers = []
    repeat_customers = 0
    for customer_id, item in customer_rollup.items():
        order_count = len(item["order_ids"])
        if order_count >= 2:
            repeat_customers += 1
        revenue = float(item["revenue"])
        recency_days = 0
        last_order_date = item["last_order_date"]
        if last_order_date is not None:
            recency_days = max((latest_seen - last_order_date).days, 0)
        average_order_value = revenue / order_count if order_count else 0.0
        segment = _segment(order_count, revenue, recency_days)
        expected_ltv = revenue * (1.6 if order_count >= 2 else 1.15)
        customers.append(
            {
                "customer_id": customer_id,
                "order_count": order_count,
                "total_revenue": round(revenue, 2),
                "average_order_value": round(average_order_value, 2),
                "total_quantity": round(float(item["quantity"]), 2),
                "recency_days": recency_days,
                "segment": segment,
                "expected_ltv": round(expected_ltv, 2),
            }
        )
    customers.sort(key=lambda item: (item["expected_ltv"], item["order_count"]), reverse=True)
    customer_count = len(customers)
    summary = {
        "customer_count": customer_count,
        "repeat_customer_count": repeat_customers,
        "repeat_customer_rate": round(repeat_customers / customer_count, 4)
        if customer_count
        else 0.0,
        "average_order_value": round(total_revenue / total_orders, 2) if total_orders else 0.0,
        "average_orders_per_customer": round(total_orders / customer_count, 2)
        if customer_count
        else 0.0,
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": CUSTOMER_INTELLIGENCE_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "customers": customers,
    }
    return write_json(artifact_path, payload)


def get_customer_intelligence_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_customer_intelligence_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["customers"] = list(payload.get("customers", []))[:limit]
    return payload


def get_customer_segment(
    upload_id: str,
    customer_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_customer_intelligence_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = customer_id.strip().lower()
    for item in payload.get("customers", []):
        if to_text(item.get("customer_id")).lower() == target:
            return item
    raise FileNotFoundError(
        f"Customer intelligence artifact does not contain customer_id={customer_id}."
    )
