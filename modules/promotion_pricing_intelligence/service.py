# Project:      RetailOps Data & AI Platform
# Module:       modules.promotion_pricing_intelligence
# File:         service.py
# Path:         modules/promotion_pricing_intelligence/service.py
#
# Summary:      Implements the promotion pricing intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for promotion pricing intelligence workflows.
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
#   - Key APIs: build_promotion_pricing_artifact, get_promotion_pricing_artifact, get_promotion_pricing_sku
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

PROMOTION_PRICING_VERSION = "commercial-suite-promotion-pricing-v1"


def build_promotion_pricing_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_promotion_pricing.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    sku_rollup: dict[tuple[str, str, str], dict[str, float | str | int]] = defaultdict(
        lambda: {
            "sku": "",
            "category": "uncategorized",
            "promo_code": "no_promo",
            "rows": 0,
            "quantity": 0.0,
            "gross_revenue": 0.0,
            "net_revenue": 0.0,
            "discount_value": 0.0,
        }
    )
    total_rows = 0
    promoted_rows = 0
    gross_revenue = 0.0
    net_revenue = 0.0
    discount_value = 0.0
    promo_counts: dict[str, int] = defaultdict(int)

    for row in iter_normalized_rows(csv_path):
        total_rows += 1
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        promo_code = (
            canonical_value(row, "promo_code", "coupon_code", "discount_code") or "no_promo"
        )
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        list_price = to_float(canonical_value(row, "list_price", "msrp"), default=unit_price)
        discount_amount = to_float(
            canonical_value(row, "discount_amount", "discount_value"),
            default=max(list_price - unit_price, 0.0),
        )
        gross = max(list_price * quantity, 0.0)
        discount = max(discount_amount * quantity, 0.0)
        net = max(gross - discount, unit_price * quantity)
        key = (sku, category, promo_code)
        current = sku_rollup[key]
        current["sku"] = sku
        current["category"] = category
        current["promo_code"] = promo_code
        current["rows"] = int(current["rows"]) + 1
        current["quantity"] = float(current["quantity"]) + quantity
        current["gross_revenue"] = float(current["gross_revenue"]) + gross
        current["net_revenue"] = float(current["net_revenue"]) + net
        current["discount_value"] = float(current["discount_value"]) + discount
        gross_revenue += gross
        net_revenue += net
        discount_value += discount
        if promo_code != "no_promo" or discount > 0:
            promoted_rows += 1
            promo_counts[promo_code] += 1

    sku_rows = []
    for item in sku_rollup.values():
        gross = float(item["gross_revenue"])
        net = float(item["net_revenue"])
        discount = float(item["discount_value"])
        sku_rows.append(
            {
                "sku": str(item["sku"]),
                "category": str(item["category"]),
                "promo_code": str(item["promo_code"]),
                "rows": int(item["rows"]),
                "quantity": round(float(item["quantity"]), 2),
                "gross_revenue": round(gross, 2),
                "net_revenue": round(net, 2),
                "discount_value": round(discount, 2),
                "discount_rate": round(discount / gross, 4) if gross else 0.0,
                "price_realization": round(net / gross, 4) if gross else 0.0,
            }
        )
    sku_rows.sort(key=lambda item: (item["discount_value"], item["gross_revenue"]), reverse=True)

    summary = {
        "total_rows": total_rows,
        "promoted_rows": promoted_rows,
        "promo_revenue_share": round(net_revenue / gross_revenue, 4) if gross_revenue else 0.0,
        "average_discount_rate": round(discount_value / gross_revenue, 4) if gross_revenue else 0.0,
        "gross_revenue": round(gross_revenue, 2),
        "net_revenue": round(net_revenue, 2),
        "discount_value": round(discount_value, 2),
        "top_promo_code": max(promo_counts, key=promo_counts.get) if promo_counts else "no_promo",
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PROMOTION_PRICING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "skus": sku_rows,
    }
    return write_json(artifact_path, payload)


def get_promotion_pricing_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_promotion_pricing_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["skus"] = list(payload.get("skus", []))[:limit]
    return payload


def get_promotion_pricing_sku(
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_promotion_pricing_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    normalized = sku.strip().lower()
    for item in payload.get("skus", []):
        if to_text(item.get("sku")).lower() == normalized:
            return item
    raise FileNotFoundError(f"Promotion pricing artifact does not contain sku={sku}.")
