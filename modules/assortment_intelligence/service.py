# Project:      RetailOps Data & AI Platform
# Module:       modules.assortment_intelligence
# File:         service.py
# Path:         modules/assortment_intelligence/service.py
#
# Summary:      Implements the assortment intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for assortment intelligence workflows.
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
#   - Key APIs: build_assortment_artifact, get_assortment_artifact, get_assortment_sku
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
    read_json_or_none,
    resolve_uploaded_csv_path,
    to_float,
    to_text,
    utc_now_iso,
    write_json,
)

ASSORTMENT_INTELLIGENCE_VERSION = "margin_and_assortment-assortment-intelligence-v1"


def _movement_class(order_count: int, revenue_share: float, quantity: float) -> str:
    if revenue_share >= 0.2 or order_count >= 5:
        return "hero"
    if quantity <= 1 or order_count <= 1:
        return "slow_mover"
    if revenue_share >= 0.08:
        return "core"
    return "long_tail"


def build_assortment_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_assortment_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    sku_rollup: dict[str, dict[str, float | int | str | set[str]]] = defaultdict(
        lambda: {
            "sku": "unknown",
            "category": "uncategorized",
            "order_ids": set(),
            "quantity": 0.0,
            "revenue": 0.0,
        }
    )
    categories: set[str] = set()
    order_ids: set[str] = set()
    total_revenue = 0.0

    for row in iter_normalized_rows(csv_path):
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        order_id = canonical_value(row, "order_id") or f"synthetic-{sku}"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        revenue = max(quantity * unit_price, 0.0)
        current = sku_rollup[sku]
        current["sku"] = sku
        current["category"] = category
        current["quantity"] = float(current["quantity"]) + quantity
        current["revenue"] = float(current["revenue"]) + revenue
        current["order_ids"].add(order_id)
        categories.add(category)
        order_ids.add(order_id)
        total_revenue += revenue

    skus = []
    slow_mover_count = 0
    for item in sku_rollup.values():
        quantity = round(float(item["quantity"]), 2)
        revenue = round(float(item["revenue"]), 2)
        item_order_count = len(item["order_ids"])
        revenue_share = round(revenue / total_revenue, 4) if total_revenue else 0.0
        average_unit_price = round(revenue / quantity, 2) if quantity else 0.0
        movement_class = _movement_class(item_order_count, revenue_share, quantity)
        if movement_class == "slow_mover":
            slow_mover_count += 1
        skus.append(
            {
                "sku": str(item["sku"]),
                "category": str(item["category"]),
                "order_count": item_order_count,
                "quantity": quantity,
                "revenue": revenue,
                "average_unit_price": average_unit_price,
                "revenue_share": revenue_share,
                "movement_class": movement_class,
            }
        )
    skus.sort(key=lambda item: (item["revenue"], item["order_count"]), reverse=True)
    hero_share = 0.0
    long_tail_share = 0.0
    for item in skus:
        if item["movement_class"] == "hero":
            hero_share += float(item["revenue_share"])
        if item["movement_class"] in {"slow_mover", "long_tail"}:
            long_tail_share += float(item["revenue_share"])
    summary = {
        "sku_count": len(skus),
        "category_count": len(categories),
        "order_count": len(order_ids),
        "long_tail_revenue_share": round(long_tail_share, 4),
        "hero_sku_share": round(hero_share, 4),
        "slow_mover_count": slow_mover_count,
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": ASSORTMENT_INTELLIGENCE_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "skus": skus,
    }
    return write_json(artifact_path, payload)


def get_assortment_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_assortment_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["skus"] = list(payload.get("skus", []))[:limit]
    return payload


def get_assortment_sku(
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_assortment_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = sku.strip().lower()
    for item in payload.get("skus", []):
        if to_text(item.get("sku")).lower() == target:
            return item
    raise FileNotFoundError(f"Assortment intelligence artifact does not contain sku={sku}.")
