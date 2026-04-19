# Project:      RetailOps Data & AI Platform
# Module:       modules.basket_affinity_intelligence
# File:         service.py
# Path:         modules/basket_affinity_intelligence/service.py
#
# Summary:      Implements the basket affinity intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for basket affinity intelligence workflows.
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
#   - Key APIs: build_basket_affinity_artifact, get_basket_affinity_artifact, get_basket_pair
#   - Dependencies: __future__, collections, itertools, pathlib, typing, modules.common.upload_utils, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from modules.common.upload_utils import (
    canonical_value,
    iter_normalized_rows,
    read_json_or_none,
    resolve_uploaded_csv_path,
    to_text,
    utc_now_iso,
    write_json,
)

BASKET_AFFINITY_VERSION = "margin_and_assortment-basket-affinity-intelligence-v1"


def build_basket_affinity_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_basket_affinity_intelligence.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    order_items: dict[str, set[str]] = defaultdict(set)
    sku_orders: dict[str, set[str]] = defaultdict(set)
    pair_counts: dict[tuple[str, str], int] = defaultdict(int)

    for row in iter_normalized_rows(csv_path):
        order_id = canonical_value(row, "order_id")
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        if not order_id:
            continue
        order_items[order_id].add(sku)
        sku_orders[sku].add(order_id)

    multi_item_order_count = 0
    for order_id, skus in order_items.items():
        if len(skus) < 2:
            continue
        multi_item_order_count += 1
        for left, right in combinations(sorted(skus), 2):
            pair_counts[(left, right)] += 1

    order_count = len(order_items)
    pairs = []
    for (left, right), pair_order_count in pair_counts.items():
        left_orders = len(sku_orders[left])
        right_orders = len(sku_orders[right])
        support = round(pair_order_count / order_count, 4) if order_count else 0.0
        confidence = round(pair_order_count / left_orders, 4) if left_orders else 0.0
        right_support = right_orders / order_count if order_count else 0.0
        lift = round(confidence / right_support, 4) if right_support else 0.0
        pairs.append(
            {
                "left_sku": left,
                "right_sku": right,
                "pair_order_count": pair_order_count,
                "support": support,
                "confidence": confidence,
                "lift": lift,
            }
        )
    pairs.sort(
        key=lambda item: (item["lift"], item["pair_order_count"], item["support"]), reverse=True
    )
    strongest = (
        pairs[0]
        if pairs
        else {
            "support": 0.0,
            "confidence": 0.0,
        }
    )
    summary = {
        "order_count": order_count,
        "multi_item_order_count": multi_item_order_count,
        "pair_count": len(pairs),
        "strongest_pair_support": float(strongest["support"]),
        "strongest_pair_confidence": float(strongest["confidence"]),
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": BASKET_AFFINITY_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "pairs": pairs,
    }
    return write_json(artifact_path, payload)


def get_basket_affinity_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_basket_affinity_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["pairs"] = list(payload.get("pairs", []))[:limit]
    return payload


def get_basket_pair(
    upload_id: str,
    left_sku: str,
    right_sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_basket_affinity_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = tuple(sorted([left_sku.strip().lower(), right_sku.strip().lower()]))
    for item in payload.get("pairs", []):
        pair = tuple(
            sorted([to_text(item.get("left_sku")).lower(), to_text(item.get("right_sku")).lower()])
        )
        if pair == target:
            return item
    raise FileNotFoundError(
        f"Basket affinity artifact does not contain pair={left_sku}|{right_sku}."
    )
