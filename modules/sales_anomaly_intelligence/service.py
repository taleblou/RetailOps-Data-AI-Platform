# Project:      RetailOps Data & AI Platform
# Module:       modules.sales_anomaly_intelligence
# File:         service.py
# Path:         modules/sales_anomaly_intelligence/service.py
#
# Summary:      Implements the sales anomaly intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for sales anomaly intelligence workflows.
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
#   - Key APIs: build_sales_anomaly_artifact, get_sales_anomaly_artifact, get_sales_anomaly_day
#   - Dependencies: __future__, collections, pathlib, typing, modules.common.upload_utils
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import defaultdict
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

SALES_ANOMALY_VERSION = "risk_retention-sales-anomaly-v1"


def build_sales_anomaly_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_sales_anomaly_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    day_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_ids": set(),
            "quantity": 0.0,
            "revenue": 0.0,
            "category_revenue": defaultdict(float),
        }
    )

    for row in iter_normalized_rows(csv_path):
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        if order_date is None:
            continue
        order_day = order_date.isoformat()
        order_id = canonical_value(row, "order_id") or f"synthetic-{order_day}"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        revenue = round(quantity * unit_price, 2)
        current = day_rollup[order_day]
        current["order_ids"].add(order_id)
        current["quantity"] += quantity
        current["revenue"] += revenue
        current["category_revenue"][category] += revenue

    if not day_rollup:
        raise ValueError("Sales anomaly intelligence requires at least one valid order_date row.")

    average_revenue = sum(float(item["revenue"]) for item in day_rollup.values()) / len(day_rollup)
    days = []
    spike_count = 0
    drop_count = 0
    largest_positive_delta_ratio = 0.0
    largest_negative_delta_ratio = 0.0

    for order_day, item in sorted(day_rollup.items()):
        revenue = round(float(item["revenue"]), 2)
        delta_ratio = round((revenue / average_revenue) - 1.0, 4) if average_revenue else 0.0
        anomaly_type = "normal"
        if delta_ratio >= 0.5:
            anomaly_type = "spike"
            spike_count += 1
        elif delta_ratio <= -0.4:
            anomaly_type = "drop"
            drop_count += 1
        dominant_category = "uncategorized"
        if item["category_revenue"]:
            dominant_category = max(
                item["category_revenue"].items(),
                key=lambda candidate: candidate[1],
            )[0]
        largest_positive_delta_ratio = max(largest_positive_delta_ratio, delta_ratio)
        largest_negative_delta_ratio = min(largest_negative_delta_ratio, delta_ratio)
        days.append(
            {
                "order_date": order_day,
                "revenue": revenue,
                "order_count": len(item["order_ids"]),
                "quantity": round(float(item["quantity"]), 2),
                "dominant_category": dominant_category,
                "baseline_revenue": round(average_revenue, 2),
                "delta_ratio": delta_ratio,
                "anomaly_type": anomaly_type,
            }
        )

    days.sort(key=lambda item: (abs(item["delta_ratio"]), item["revenue"]), reverse=True)
    summary = {
        "day_count": len(day_rollup),
        "anomaly_count": spike_count + drop_count,
        "spike_count": spike_count,
        "drop_count": drop_count,
        "largest_positive_delta_ratio": round(largest_positive_delta_ratio, 4),
        "largest_negative_delta_ratio": round(largest_negative_delta_ratio, 4),
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": SALES_ANOMALY_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "days": days,
    }
    return write_json(artifact_path, payload)


def get_sales_anomaly_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 90,
) -> dict[str, Any]:
    payload = build_sales_anomaly_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["days"] = list(payload.get("days", []))[:limit]
    return payload


def get_sales_anomaly_day(
    upload_id: str,
    order_date: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_sales_anomaly_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    for item in payload.get("days", []):
        if to_text(item.get("order_date")) == order_date:
            return item
    raise FileNotFoundError(f"Sales anomaly artifact does not contain order_date={order_date}.")
