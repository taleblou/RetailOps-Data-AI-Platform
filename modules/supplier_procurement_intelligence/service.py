# Project:      RetailOps Data & AI Platform
# Module:       modules.supplier_procurement_intelligence
# File:         service.py
# Path:         modules/supplier_procurement_intelligence/service.py
#
# Summary:      Implements the supplier procurement intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for supplier procurement intelligence workflows.
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
#   - Key APIs: build_supplier_procurement_artifact, get_supplier_procurement_artifact, get_supplier_procurement_item
#   - Dependencies: __future__, math, collections, pathlib, typing, modules.common.upload_utils, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from modules.common.upload_utils import (
    canonical_value,
    days_between,
    iter_normalized_rows,
    read_json_or_none,
    resolve_uploaded_csv_path,
    to_float,
    to_text,
    utc_now_iso,
    write_json,
)

SUPPLIER_PROCUREMENT_VERSION = "commercial-suite-supplier-procurement-v1"


def _risk_band(fill_rate: float, lead_time: float, variability: float) -> str:
    if fill_rate < 0.85 or lead_time > 12 or variability > 4:
        return "high"
    if fill_rate < 0.94 or lead_time > 8 or variability > 2:
        return "medium"
    return "low"


def _recommended_action(risk_band: str) -> str:
    return {
        "high": "increase safety stock and review supplier SLA",
        "medium": "track weekly and validate open POs",
        "low": "keep standard procurement cadence",
    }[risk_band]


def build_supplier_procurement_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_supplier_procurement.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    supplier_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "supplier_id": "unknown",
            "supplier_name": "unknown",
            "rows": 0,
            "total_ordered_qty": 0.0,
            "total_received_qty": 0.0,
            "lead_times": [],
            "moqs": [],
        }
    )

    for row in iter_normalized_rows(csv_path):
        supplier_id = canonical_value(row, "supplier_id", "vendor_id") or "unknown"
        supplier_name = canonical_value(row, "supplier_name", "vendor_name") or supplier_id
        ordered_qty = max(
            to_float(canonical_value(row, "ordered_qty", "quantity", "qty"), default=0.0), 0.0
        )
        received_qty = max(
            to_float(canonical_value(row, "received_qty", "fulfilled_qty"), default=ordered_qty),
            0.0,
        )
        lead_time_days = to_float(
            canonical_value(row, "lead_time_days"),
            default=days_between(
                canonical_value(row, "promised_date", "po_date", "order_date"),
                canonical_value(row, "actual_delivery_date", "received_date", "delivery_date"),
                default=7.0,
            ),
        )
        moq = max(to_float(canonical_value(row, "supplier_moq", "moq"), default=1.0), 1.0)
        current = supplier_rollup[supplier_id]
        current["supplier_id"] = supplier_id
        current["supplier_name"] = supplier_name
        current["rows"] += 1
        current["total_ordered_qty"] += ordered_qty
        current["total_received_qty"] += received_qty
        current["lead_times"].append(lead_time_days)
        current["moqs"].append(moq)

    suppliers = []
    high_risk_suppliers = 0
    total_ordered = 0.0
    total_received = 0.0
    lead_time_values: list[float] = []
    fill_rates: list[float] = []
    for item in supplier_rollup.values():
        lead_times = [float(value) for value in item["lead_times"]]
        average_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0.0
        variance = (
            sum((value - average_lead_time) ** 2 for value in lead_times) / len(lead_times)
            if lead_times
            else 0.0
        )
        variability = math.sqrt(variance)
        fill_rate = (
            float(item["total_received_qty"]) / float(item["total_ordered_qty"])
            if float(item["total_ordered_qty"])
            else 0.0
        )
        risk_band = _risk_band(fill_rate, average_lead_time, variability)
        if risk_band == "high":
            high_risk_suppliers += 1
        total_ordered += float(item["total_ordered_qty"])
        total_received += float(item["total_received_qty"])
        lead_time_values.append(average_lead_time)
        fill_rates.append(fill_rate)
        suppliers.append(
            {
                "supplier_id": str(item["supplier_id"]),
                "supplier_name": str(item["supplier_name"]),
                "rows": int(item["rows"]),
                "total_ordered_qty": round(float(item["total_ordered_qty"]), 2),
                "total_received_qty": round(float(item["total_received_qty"]), 2),
                "fill_rate": round(fill_rate, 4),
                "average_lead_time_days": round(average_lead_time, 2),
                "lead_time_variability_days": round(variability, 2),
                "average_moq": round(sum(item["moqs"]) / len(item["moqs"]), 2),
                "procurement_risk_band": risk_band,
                "recommended_action": _recommended_action(risk_band),
            }
        )
    suppliers.sort(
        key=lambda item: (item["procurement_risk_band"], -item["total_ordered_qty"]), reverse=True
    )
    summary = {
        "supplier_count": len(suppliers),
        "total_ordered_qty": round(total_ordered, 2),
        "total_received_qty": round(total_received, 2),
        "average_fill_rate": round(sum(fill_rates) / len(fill_rates), 4) if fill_rates else 0.0,
        "average_lead_time_days": round(sum(lead_time_values) / len(lead_time_values), 2)
        if lead_time_values
        else 0.0,
        "high_risk_suppliers": high_risk_suppliers,
    }
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": SUPPLIER_PROCUREMENT_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "summary": summary,
        "suppliers": suppliers,
    }
    return write_json(artifact_path, payload)


def get_supplier_procurement_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_supplier_procurement_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    payload = dict(payload)
    payload["suppliers"] = list(payload.get("suppliers", []))[:limit]
    return payload


def get_supplier_procurement_item(
    upload_id: str,
    supplier_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_supplier_procurement_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = supplier_id.strip().lower()
    for item in payload.get("suppliers", []):
        if to_text(item.get("supplier_id")).lower() == target:
            return item
    raise FileNotFoundError(
        f"Supplier procurement artifact does not contain supplier_id={supplier_id}."
    )
