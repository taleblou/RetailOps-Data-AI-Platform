# Project:      RetailOps Data & AI Platform
# Module:       modules.abc_xyz_intelligence
# File:         service.py
# Path:         modules/abc_xyz_intelligence/service.py
#
# Summary:      Implements the abc xyz intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for abc xyz intelligence workflows.
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
#   - Key APIs: build_abc_xyz_artifact, get_abc_xyz_artifact, get_abc_xyz_sku
#   - Dependencies: __future__, collections, datetime, math, pathlib, typing, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import defaultdict
from datetime import date
from math import sqrt
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

ABC_XYZ_INTELLIGENCE_VERSION = "customer_inventory-abc-xyz-intelligence-v1"


def _month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def _month_sequence(start: date, end: date) -> list[str]:
    year = start.year
    month = start.month
    out: list[str] = []
    while (year, month) <= (end.year, end.month):
        out.append(f"{year:04d}-{month:02d}")
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return out


def _coefficient_of_variation(values: list[float]) -> float:
    if not values:
        return 0.0
    mean_value = sum(values) / len(values)
    if mean_value <= 0:
        return 0.0
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return sqrt(variance) / mean_value


def _xyz_class(coefficient_variation: float) -> str:
    if coefficient_variation < 0.5:
        return "X"
    if coefficient_variation < 1.0:
        return "Y"
    return "Z"


def build_abc_xyz_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_abc_xyz_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    sku_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "sku": "unknown",
            "category": "uncategorized",
            "order_ids": set(),
            "quantity": 0.0,
            "revenue": 0.0,
            "monthly_quantity": defaultdict(float),
            "first_seen": None,
            "last_seen": None,
        }
    )
    latest_seen = date(2026, 3, 29)
    total_revenue = 0.0

    for row in iter_normalized_rows(csv_path):
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        order_id = canonical_value(row, "order_id") or f"synthetic-{sku}"
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        revenue = quantity * unit_price
        current = sku_rollup[sku]
        current["sku"] = sku
        current["category"] = category
        current["order_ids"].add(order_id)
        current["quantity"] = float(current["quantity"]) + quantity
        current["revenue"] = float(current["revenue"]) + revenue
        total_revenue += revenue
        if order_date is not None:
            latest_seen = max(latest_seen, order_date)
            month_key = _month_key(order_date)
            monthly_quantity = current["monthly_quantity"]
            monthly_quantity[month_key] += quantity
            if current["first_seen"] is None or order_date < current["first_seen"]:
                current["first_seen"] = order_date
            if current["last_seen"] is None or order_date > current["last_seen"]:
                current["last_seen"] = order_date

    skus = []
    for item in sku_rollup.values():
        first_seen = item["first_seen"] or latest_seen
        month_keys = _month_sequence(first_seen, latest_seen)
        monthly_quantity = item["monthly_quantity"]
        quantities = [float(monthly_quantity.get(month_key, 0.0)) for month_key in month_keys]
        coefficient_variation = round(_coefficient_of_variation(quantities), 4)
        skus.append(
            {
                "sku": str(item["sku"]),
                "category": str(item["category"]),
                "order_count": len(item["order_ids"]),
                "quantity": round(float(item["quantity"]), 2),
                "revenue": round(float(item["revenue"]), 2),
                "revenue_share": round(float(item["revenue"]) / total_revenue, 4)
                if total_revenue
                else 0.0,
                "demand_coefficient_variation": coefficient_variation,
            }
        )
    skus.sort(key=lambda item: (item["revenue"], item["order_count"]), reverse=True)

    cumulative_revenue_share = 0.0
    a_class_sku_count = 0
    z_class_sku_count = 0
    a_class_revenue_share = 0.0
    for item in skus:
        cumulative_revenue_share += float(item["revenue_share"])
        abc_class = "A"
        if cumulative_revenue_share > 0.95:
            abc_class = "C"
        elif cumulative_revenue_share > 0.8:
            abc_class = "B"
        xyz_class = _xyz_class(float(item["demand_coefficient_variation"]))
        item["abc_class"] = abc_class
        item["xyz_class"] = xyz_class
        item["combined_class"] = f"{abc_class}{xyz_class}"
        if abc_class == "A":
            a_class_sku_count += 1
            a_class_revenue_share += float(item["revenue_share"])
        if xyz_class == "Z":
            z_class_sku_count += 1

    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": ABC_XYZ_INTELLIGENCE_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": {
            "sku_count": len(skus),
            "a_class_sku_count": a_class_sku_count,
            "z_class_sku_count": z_class_sku_count,
            "a_class_revenue_share": round(a_class_revenue_share, 4),
            "high_variability_sku_count": z_class_sku_count,
        },
        "skus": skus,
    }
    return write_json(artifact_path, payload)


def get_abc_xyz_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_abc_xyz_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["skus"] = list(payload.get("skus", []))[:limit]
    return payload


def get_abc_xyz_sku(
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_abc_xyz_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = sku.strip().lower()
    for item in payload.get("skus", []):
        if to_text(item.get("sku")).lower() == target:
            return item
    raise FileNotFoundError(f"ABC XYZ artifact does not contain sku={sku}.")
