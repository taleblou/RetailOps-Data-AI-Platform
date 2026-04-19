# Project:      RetailOps Data & AI Platform
# Module:       modules.seasonality_intelligence
# File:         service.py
# Path:         modules/seasonality_intelligence/service.py
#
# Summary:      Implements the seasonality intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for seasonality intelligence workflows.
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
#   - Key APIs: build_seasonality_artifact, get_seasonality_artifact, get_seasonality_sku
#   - Dependencies: __future__, collections, pathlib, typing, modules.common.upload_utils
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import Counter, defaultdict
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

SEASONALITY_VERSION = "risk_retention-seasonality-v1"


def _seasonality_band(peak_share: float, active_month_count: int) -> str:
    if active_month_count <= 2 and peak_share >= 0.45:
        return "strong_seasonal"
    if peak_share >= 0.35:
        return "moderate_seasonal"
    if active_month_count >= 4:
        return "steady"
    return "emerging"


def build_seasonality_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_seasonality_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    sku_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "category": "uncategorized",
            "total_revenue": 0.0,
            "month_revenue": defaultdict(float),
        }
    )

    for row in iter_normalized_rows(csv_path):
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        if order_date is None:
            continue
        sku = canonical_value(row, "sku", "product_id", "product_sku") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        revenue = round(quantity * unit_price, 2)
        order_month = order_date.strftime("%Y-%m")
        current = sku_rollup[sku]
        current["category"] = category
        current["total_revenue"] += revenue
        current["month_revenue"][order_month] += revenue

    if not sku_rollup:
        raise ValueError("Seasonality intelligence requires at least one valid order_date row.")

    skus = []
    peak_counter: Counter[str] = Counter()
    strong_seasonal_sku_count = 0
    moderate_seasonal_sku_count = 0
    steady_sku_count = 0

    for sku, item in sku_rollup.items():
        month_revenue = dict(item["month_revenue"])
        peak_month, peak_value = max(month_revenue.items(), key=lambda candidate: candidate[1])
        trough_month, _ = min(month_revenue.items(), key=lambda candidate: candidate[1])
        total_revenue = round(float(item["total_revenue"]), 2)
        peak_share = round(peak_value / total_revenue, 4) if total_revenue else 0.0
        active_month_count = len(month_revenue)
        seasonality_band = _seasonality_band(peak_share, active_month_count)
        if seasonality_band == "strong_seasonal":
            strong_seasonal_sku_count += 1
        elif seasonality_band == "moderate_seasonal":
            moderate_seasonal_sku_count += 1
        elif seasonality_band == "steady":
            steady_sku_count += 1
        peak_counter[peak_month] += 1
        skus.append(
            {
                "sku": sku,
                "category": str(item["category"]),
                "total_revenue": total_revenue,
                "active_month_count": active_month_count,
                "peak_month": peak_month,
                "peak_month_revenue_share": peak_share,
                "trough_month": trough_month,
                "seasonality_band": seasonality_band,
            }
        )

    skus.sort(
        key=lambda item: (item["peak_month_revenue_share"], item["total_revenue"]), reverse=True
    )
    summary = {
        "sku_count": len(skus),
        "strong_seasonal_sku_count": strong_seasonal_sku_count,
        "moderate_seasonal_sku_count": moderate_seasonal_sku_count,
        "steady_sku_count": steady_sku_count,
        "most_common_peak_month": peak_counter.most_common(1)[0][0] if peak_counter else "",
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": SEASONALITY_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "skus": skus,
    }
    return write_json(artifact_path, payload)


def get_seasonality_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_seasonality_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["skus"] = list(payload.get("skus", []))[:limit]
    return payload


def get_seasonality_sku(
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_seasonality_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = sku.strip().lower()
    for item in payload.get("skus", []):
        if to_text(item.get("sku")).lower() == target:
            return item
    raise FileNotFoundError(f"Seasonality artifact does not contain sku={sku}.")
