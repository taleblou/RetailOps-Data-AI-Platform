# Project:      RetailOps Data & AI Platform
# Module:       modules.profitability_intelligence
# File:         service.py
# Path:         modules/profitability_intelligence/service.py
#
# Summary:      Implements the profitability intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for profitability intelligence workflows.
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
#   - Key APIs: build_profitability_artifact, get_profitability_artifact, get_profitability_sku
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

PROFITABILITY_INTELLIGENCE_VERSION = "margin_and_assortment-profitability-intelligence-v1"


def _margin_band(margin_rate: float) -> str:
    if margin_rate < 0:
        return "loss_making"
    if margin_rate < 0.15:
        return "thin"
    if margin_rate < 0.35:
        return "healthy"
    return "strong"


def build_profitability_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_profitability_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    sku_rollup: dict[str, dict[str, float | str]] = defaultdict(
        lambda: {
            "sku": "unknown",
            "category": "uncategorized",
            "quantity": 0.0,
            "revenue": 0.0,
            "cost": 0.0,
            "gross_list_revenue": 0.0,
            "cost_covered_quantity": 0.0,
        }
    )
    order_ids: set[str] = set()
    total_revenue = 0.0
    total_cost = 0.0
    covered_quantity = 0.0
    total_quantity = 0.0

    for row in iter_normalized_rows(csv_path):
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        order_id = canonical_value(row, "order_id") or f"synthetic-{sku}"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        list_price = to_float(canonical_value(row, "list_price", "msrp"), default=unit_price)
        unit_cost = to_float(
            canonical_value(row, "unit_cost", "cost", "cogs", "cost_of_goods"), default=0.0
        )
        revenue = max(quantity * unit_price, 0.0)
        cost = max(quantity * unit_cost, 0.0)
        gross_list_revenue = max(quantity * list_price, 0.0)
        current = sku_rollup[sku]
        current["sku"] = sku
        current["category"] = category
        current["quantity"] = float(current["quantity"]) + quantity
        current["revenue"] = float(current["revenue"]) + revenue
        current["cost"] = float(current["cost"]) + cost
        current["gross_list_revenue"] = float(current["gross_list_revenue"]) + gross_list_revenue
        if unit_cost > 0:
            current["cost_covered_quantity"] = float(current["cost_covered_quantity"]) + quantity
            covered_quantity += quantity
        total_revenue += revenue
        total_cost += cost
        total_quantity += quantity
        order_ids.add(order_id)

    skus = []
    loss_making_sku_count = 0
    for item in sku_rollup.values():
        revenue = round(float(item["revenue"]), 2)
        cost = round(float(item["cost"]), 2)
        gross_profit = round(revenue - cost, 2)
        margin_rate = round(gross_profit / revenue, 4) if revenue else 0.0
        list_revenue = float(item["gross_list_revenue"])
        discount_rate = round((list_revenue - revenue) / list_revenue, 4) if list_revenue else 0.0
        margin_band = _margin_band(margin_rate)
        if margin_band == "loss_making":
            loss_making_sku_count += 1
        skus.append(
            {
                "sku": str(item["sku"]),
                "category": str(item["category"]),
                "quantity": round(float(item["quantity"]), 2),
                "revenue": revenue,
                "cost": cost,
                "gross_profit": gross_profit,
                "gross_margin_rate": margin_rate,
                "discount_rate": discount_rate,
                "margin_band": margin_band,
            }
        )
    skus.sort(key=lambda item: (item["gross_profit"], item["revenue"]), reverse=True)
    summary = {
        "sku_count": len(skus),
        "order_count": len(order_ids),
        "revenue": round(total_revenue, 2),
        "gross_profit": round(total_revenue - total_cost, 2),
        "gross_margin_rate": round((total_revenue - total_cost) / total_revenue, 4)
        if total_revenue
        else 0.0,
        "margin_data_coverage": round(covered_quantity / total_quantity, 4)
        if total_quantity
        else 0.0,
        "loss_making_sku_count": loss_making_sku_count,
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PROFITABILITY_INTELLIGENCE_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "skus": skus,
    }
    return write_json(artifact_path, payload)


def get_profitability_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_profitability_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["skus"] = list(payload.get("skus", []))[:limit]
    return payload


def get_profitability_sku(
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_profitability_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = sku.strip().lower()
    for item in payload.get("skus", []):
        if to_text(item.get("sku")).lower() == target:
            return item
    raise FileNotFoundError(f"Profitability intelligence artifact does not contain sku={sku}.")
