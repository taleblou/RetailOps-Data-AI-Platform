# Project:      RetailOps Data & AI Platform
# Module:       modules.payment_reconciliation
# File:         service.py
# Path:         modules/payment_reconciliation/service.py
#
# Summary:      Implements the payment reconciliation service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for payment reconciliation workflows.
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
#   - Key APIs: build_payment_reconciliation_artifact, get_payment_reconciliation_artifact, get_payment_reconciliation_order
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

PAYMENT_RECONCILIATION_VERSION = "commercial-suite-payment-reconciliation-v1"


def _status(order_amount: float, paid_amount: float, refund_amount: float) -> str:
    net_paid = paid_amount - refund_amount
    if paid_amount <= 0:
        return "missing_payment"
    variance = net_paid - order_amount
    if refund_amount > 0 and abs(variance) < 0.01:
        return "refunded"
    if abs(variance) < 0.01:
        return "matched"
    if variance < 0:
        return "underpaid"
    return "overpaid"


def build_payment_reconciliation_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_payment_reconciliation.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    orders: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_id": "",
            "payment_provider": "unknown",
            "order_amount": 0.0,
            "paid_amount": 0.0,
            "refund_amount": 0.0,
        }
    )

    for row in iter_normalized_rows(csv_path):
        order_id = canonical_value(row, "order_id") or "unknown"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        order_amount = to_float(
            canonical_value(row, "total_amount", "order_total"), default=quantity * unit_price
        )
        paid_amount = to_float(
            canonical_value(row, "paid_amount", "payment_amount"), default=order_amount
        )
        refund_amount = to_float(canonical_value(row, "refund_amount"), default=0.0)
        provider = canonical_value(row, "payment_provider", "payment_method") or "unknown"
        current = orders[order_id]
        current["order_id"] = order_id
        current["payment_provider"] = provider
        current["order_amount"] = max(float(current["order_amount"]), order_amount)
        current["paid_amount"] = max(float(current["paid_amount"]), paid_amount)
        current["refund_amount"] += refund_amount

    order_rows = []
    matched_orders = 0
    missing_payment_orders = 0
    refunded_orders = 0
    total_order_amount = 0.0
    total_paid_amount = 0.0
    total_refund_amount = 0.0
    for item in orders.values():
        order_amount = float(item["order_amount"])
        paid_amount = float(item["paid_amount"])
        refund_amount = float(item["refund_amount"])
        status = _status(order_amount, paid_amount, refund_amount)
        if status == "matched":
            matched_orders += 1
        if status == "missing_payment":
            missing_payment_orders += 1
        if status == "refunded":
            refunded_orders += 1
        total_order_amount += order_amount
        total_paid_amount += paid_amount
        total_refund_amount += refund_amount
        order_rows.append(
            {
                "order_id": str(item["order_id"]),
                "payment_provider": str(item["payment_provider"]),
                "order_amount": round(order_amount, 2),
                "paid_amount": round(paid_amount, 2),
                "refund_amount": round(refund_amount, 2),
                "variance_amount": round((paid_amount - refund_amount) - order_amount, 2),
                "reconciliation_status": status,
            }
        )
    order_rows.sort(key=lambda item: abs(item["variance_amount"]), reverse=True)
    summary = {
        "order_count": len(order_rows),
        "matched_orders": matched_orders,
        "missing_payment_orders": missing_payment_orders,
        "refunded_orders": refunded_orders,
        "total_order_amount": round(total_order_amount, 2),
        "total_paid_amount": round(total_paid_amount, 2),
        "total_refund_amount": round(total_refund_amount, 2),
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PAYMENT_RECONCILIATION_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "orders": order_rows,
    }
    return write_json(artifact_path, payload)


def get_payment_reconciliation_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_payment_reconciliation_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["orders"] = list(payload.get("orders", []))[:limit]
    return payload


def get_payment_reconciliation_order(
    upload_id: str,
    order_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_payment_reconciliation_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = order_id.strip().lower()
    for item in payload.get("orders", []):
        if to_text(item.get("order_id")).lower() == target:
            return item
    raise FileNotFoundError(
        f"Payment reconciliation artifact does not contain order_id={order_id}."
    )
