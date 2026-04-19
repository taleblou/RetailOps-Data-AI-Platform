# Project:      RetailOps Data & AI Platform
# Module:       modules.customer_cohort_intelligence
# File:         service.py
# Path:         modules/customer_cohort_intelligence/service.py
#
# Summary:      Implements the customer cohort intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for customer cohort intelligence workflows.
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
#   - Key APIs: build_cohort_artifact, get_cohort_artifact, get_cohort_detail
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

CUSTOMER_COHORT_VERSION = "customer_inventory-customer-cohort-intelligence-v1"


def _cohort_key(value: date | None) -> str:
    if value is None:
        return "unknown"
    return value.strftime("%Y-%m")


def build_cohort_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_customer_cohort_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    customer_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_ids": set(),
            "revenue": 0.0,
            "first_order_date": None,
            "last_order_date": None,
        }
    )

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
        current["order_ids"].add(order_id)
        current["revenue"] += revenue
        if order_date is not None:
            if current["first_order_date"] is None or order_date < current["first_order_date"]:
                current["first_order_date"] = order_date
            if current["last_order_date"] is None or order_date > current["last_order_date"]:
                current["last_order_date"] = order_date

    cohorts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "cohort_month": "unknown",
            "customer_count": 0,
            "repeat_customer_count": 0,
            "order_count": 0,
            "revenue": 0.0,
        }
    )
    repeat_customer_count = 0
    for item in customer_rollup.values():
        cohort_month = _cohort_key(item["first_order_date"])
        order_count = len(item["order_ids"])
        repeat_customer = order_count >= 2
        if repeat_customer:
            repeat_customer_count += 1
        cohort = cohorts[cohort_month]
        cohort["cohort_month"] = cohort_month
        cohort["customer_count"] += 1
        cohort["order_count"] += order_count
        cohort["revenue"] += float(item["revenue"])
        if repeat_customer:
            cohort["repeat_customer_count"] += 1

    cohort_rows = []
    for cohort in cohorts.values():
        customer_count = int(cohort["customer_count"])
        order_count = int(cohort["order_count"])
        revenue = round(float(cohort["revenue"]), 2)
        repeat_count = int(cohort["repeat_customer_count"])
        cohort_rows.append(
            {
                "cohort_month": str(cohort["cohort_month"]),
                "customer_count": customer_count,
                "repeat_customer_count": repeat_count,
                "repeat_customer_rate": round(repeat_count / customer_count, 4)
                if customer_count
                else 0.0,
                "order_count": order_count,
                "revenue": revenue,
                "average_orders_per_customer": round(order_count / customer_count, 2)
                if customer_count
                else 0.0,
                "average_revenue_per_customer": round(revenue / customer_count, 2)
                if customer_count
                else 0.0,
            }
        )
    cohort_rows.sort(key=lambda item: item["cohort_month"])
    largest = max(cohort_rows, key=lambda item: item["customer_count"], default=None)
    customer_count = len(customer_rollup)
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": CUSTOMER_COHORT_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": {
            "cohort_count": len(cohort_rows),
            "customer_count": customer_count,
            "repeat_customer_count": repeat_customer_count,
            "repeat_customer_rate": round(repeat_customer_count / customer_count, 4)
            if customer_count
            else 0.0,
            "largest_cohort_month": largest["cohort_month"] if largest is not None else "unknown",
            "largest_cohort_size": int(largest["customer_count"]) if largest is not None else 0,
        },
        "cohorts": cohort_rows,
    }
    return write_json(artifact_path, payload)


def get_cohort_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_cohort_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["cohorts"] = list(payload.get("cohorts", []))[:limit]
    return payload


def get_cohort_detail(
    upload_id: str,
    cohort_month: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_cohort_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = cohort_month.strip().lower()
    for item in payload.get("cohorts", []):
        if to_text(item.get("cohort_month")).lower() == target:
            return item
    raise FileNotFoundError(
        f"Customer cohort artifact does not contain cohort_month={cohort_month}."
    )
