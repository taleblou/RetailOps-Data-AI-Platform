# Project:      RetailOps Data & AI Platform
# Module:       modules.inventory_aging_intelligence
# File:         service.py
# Path:         modules/inventory_aging_intelligence/service.py
#
# Summary:      Implements the inventory aging intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for inventory aging intelligence workflows.
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
#   - Key APIs: build_inventory_aging_artifact, get_inventory_aging_artifact, get_inventory_aging_sku
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

INVENTORY_AGING_VERSION = "customer_inventory-inventory-aging-intelligence-v1"


def _aging_band(days_since_last_sale: int, on_hand_units: float) -> str:
    if days_since_last_sale >= 90 and on_hand_units > 0:
        return "critical"
    if days_since_last_sale >= 45:
        return "stale"
    if days_since_last_sale >= 21:
        return "watch"
    return "active"


def build_inventory_aging_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_inventory_aging_intelligence.json"
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
            "quantity_sold": 0.0,
            "revenue": 0.0,
            "first_sale_date": None,
            "last_sale_date": None,
            "on_hand_units": 0.0,
            "has_inventory": False,
        }
    )
    latest_seen = date(2026, 3, 29)

    for row in iter_normalized_rows(csv_path):
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        order_id = canonical_value(row, "order_id") or f"synthetic-{sku}"
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        on_hand_units = to_float(
            canonical_value(
                row,
                "on_hand_units",
                "inventory_on_hand",
                "current_inventory",
                "stock_on_hand",
                "available_stock",
            ),
            default=0.0,
        )
        revenue = quantity * unit_price
        current = sku_rollup[sku]
        current["sku"] = sku
        current["category"] = category
        current["quantity_sold"] = float(current["quantity_sold"]) + quantity
        current["revenue"] = float(current["revenue"]) + revenue
        current["order_ids"].add(order_id)
        if order_date is not None:
            latest_seen = max(latest_seen, order_date)
            if current["first_sale_date"] is None or order_date < current["first_sale_date"]:
                current["first_sale_date"] = order_date
            if current["last_sale_date"] is None or order_date > current["last_sale_date"]:
                current["last_sale_date"] = order_date
        if on_hand_units > 0:
            current["on_hand_units"] = on_hand_units
            current["has_inventory"] = True

    skus = []
    stale_sku_count = 0
    critical_aging_count = 0
    inventory_coverage_count = 0
    total_days_since_last_sale = 0
    for item in sku_rollup.values():
        first_sale_date = item["first_sale_date"]
        last_sale_date = item["last_sale_date"]
        active_days = 1
        if first_sale_date is not None and last_sale_date is not None:
            active_days = max((latest_seen - first_sale_date).days + 1, 1)
        days_since_last_sale = 0
        if last_sale_date is not None:
            days_since_last_sale = max((latest_seen - last_sale_date).days, 0)
        total_days_since_last_sale += days_since_last_sale
        quantity_sold = round(float(item["quantity_sold"]), 2)
        average_daily_units = round(quantity_sold / active_days, 4) if active_days else 0.0
        on_hand_units = round(float(item["on_hand_units"]), 2)
        days_of_cover = None
        if item["has_inventory"]:
            inventory_coverage_count += 1
            if average_daily_units > 0:
                days_of_cover = round(on_hand_units / average_daily_units, 2)
        aging_band = _aging_band(days_since_last_sale, on_hand_units)
        if aging_band in {"stale", "critical"}:
            stale_sku_count += 1
        if aging_band == "critical":
            critical_aging_count += 1
        skus.append(
            {
                "sku": str(item["sku"]),
                "category": str(item["category"]),
                "order_count": len(item["order_ids"]),
                "quantity_sold": quantity_sold,
                "revenue": round(float(item["revenue"]), 2),
                "on_hand_units": on_hand_units,
                "days_since_last_sale": days_since_last_sale,
                "average_daily_units": average_daily_units,
                "days_of_cover": days_of_cover,
                "aging_band": aging_band,
            }
        )
    skus.sort(key=lambda item: (item["days_since_last_sale"], item["on_hand_units"]), reverse=True)
    sku_count = len(skus)
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": INVENTORY_AGING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": {
            "sku_count": sku_count,
            "stale_sku_count": stale_sku_count,
            "critical_aging_count": critical_aging_count,
            "inventory_coverage_rate": round(inventory_coverage_count / sku_count, 4)
            if sku_count
            else 0.0,
            "average_days_since_last_sale": round(total_days_since_last_sale / sku_count, 2)
            if sku_count
            else 0.0,
        },
        "skus": skus,
    }
    return write_json(artifact_path, payload)


def get_inventory_aging_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_inventory_aging_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["skus"] = list(payload.get("skus", []))[:limit]
    return payload


def get_inventory_aging_sku(
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_inventory_aging_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = sku.strip().lower()
    for item in payload.get("skus", []):
        if to_text(item.get("sku")).lower() == target:
            return item
    raise FileNotFoundError(f"Inventory aging artifact does not contain sku={sku}.")
