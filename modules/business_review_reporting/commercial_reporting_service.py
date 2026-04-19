# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         commercial_reporting_service.py
# Path:         modules/business_review_reporting/commercial_reporting_service.py
#
# Summary:      Provides implementation support for the business review reporting workflow.
# Purpose:      Supports the business review reporting layer inside the modular repository architecture.
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
#   - Key APIs: get_supplier_procurement_pack, get_returns_profit_leakage_report, get_promotion_pricing_effectiveness_report, get_customer_cohort_retention_review
#   - Dependencies: __future__, collections, datetime, pathlib, typing, modules.common.upload_utils, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import Counter, defaultdict
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
from modules.customer_churn_intelligence.service import build_customer_churn_artifact
from modules.customer_cohort_intelligence.service import build_cohort_artifact
from modules.customer_intelligence.service import build_customer_intelligence_artifact
from modules.promotion_pricing_intelligence.service import build_promotion_pricing_artifact
from modules.returns_intelligence.service import get_or_create_returns_artifact
from modules.supplier_procurement_intelligence.service import build_supplier_procurement_artifact

COMMERCIAL_REPORTING_VERSION = "commercial-reporting-v1"
COMMERCIAL_REPORTING_REFERENCE_DATE = date(2026, 3, 29)
RETURN_STATUSES = {"returned", "return", "refunded", "refund", "exchange"}
TRUTHY_VALUES = {"1", "true", "yes", "y", "returned"}
COMMERCIAL_REPORT_INDEX = [
    {
        "report_name": "supplier_and_procurement_intelligence_pack",
        "endpoint": "/api/v1/business-reports/supplier-procurement-pack",
    },
    {
        "report_name": "returns_profit_leakage_report",
        "endpoint": "/api/v1/business-reports/returns-profit-leakage",
    },
    {
        "report_name": "promotion_and_pricing_effectiveness_analysis",
        "endpoint": "/api/v1/business-reports/promotion-pricing-effectiveness",
    },
    {
        "report_name": "customer_cohort_and_retention_review",
        "endpoint": "/api/v1/business-reports/customer-cohort-retention",
    },
]


def _artifact_meta(path: Path, upload_id: str, refresh: bool) -> dict[str, Any] | None:
    if refresh:
        return None
    cached = read_json_or_none(path)
    if cached is None:
        return None
    if cached.get("upload_id") != upload_id:
        return None
    return cached


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _dominant_label(labels: list[str]) -> str:
    if not labels:
        return "none"
    return Counter(labels).most_common(1)[0][0]


def _pressure_band(ratio: float) -> str:
    if ratio >= 0.35:
        return "critical"
    if ratio >= 0.2:
        return "high"
    if ratio >= 0.1:
        return "watch"
    return "healthy"


def _parse_return_flag(row: dict[str, str]) -> bool:
    status = canonical_value(row, "order_status", "status").lower()
    if status in RETURN_STATUSES:
        return True
    flag = canonical_value(
        row,
        "returned",
        "return_flag",
        "is_returned",
        "returned_within_30_days",
    ).lower()
    if flag in TRUTHY_VALUES:
        return True
    returned_qty = to_float(canonical_value(row, "returned_qty", "return_quantity"))
    return returned_qty > 0.0


def _estimate_return_cost(
    *,
    gross_revenue: float,
    discount_rate: float,
    shipment_delay_days: float,
    explicit_return_cost: float | None,
) -> float:
    if explicit_return_cost is not None and explicit_return_cost > 0:
        return round(explicit_return_cost, 2)
    cost_multiplier = 0.30 + (discount_rate * 0.45) + min(shipment_delay_days * 0.04, 0.2)
    return round(gross_revenue * max(cost_multiplier, 0.22), 2)


def _promo_dependency_band(share: float) -> str:
    if share >= 0.65:
        return "promo_heavy"
    if share >= 0.35:
        return "balanced"
    return "low_dependency"


def _effectiveness_band(uplift_proxy: float, margin_gap: float, discount_rate: float) -> str:
    if uplift_proxy >= 1.0 and margin_gap >= 0.0 and discount_rate <= 0.15:
        return "efficient"
    if uplift_proxy >= 0.95 and margin_gap >= -0.18:
        return "mixed"
    return "dilutive"


def _cohort_health_band(retained_60d_rate: float, at_risk_rate: float) -> str:
    if retained_60d_rate >= 0.45 and at_risk_rate <= 0.2:
        return "healthy"
    if retained_60d_rate >= 0.25 and at_risk_rate <= 0.4:
        return "watch"
    return "fragile"


def get_supplier_procurement_pack(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_supplier_procurement_pack.json"
    cached = _artifact_meta(artifact_path, upload_id, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["rows"] = list(payload.get("rows", []))[:limit]
        return payload

    supplier_artifact = build_supplier_procurement_artifact(
        upload_id, uploads_dir, artifact_dir, refresh
    )
    supplier_rows = {
        to_text(item.get("supplier_id")): item
        for item in supplier_artifact.get("suppliers", [])
        if isinstance(item, dict)
    }
    supplier_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "supplier_id": "unknown",
            "supplier_name": "unknown",
            "line_count": 0,
            "promised_lines": 0,
            "on_time_lines": 0,
            "breach_lines": 0,
            "delayed_receipt_qty": 0.0,
            "spend_estimate": 0.0,
        }
    )

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
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
        unit_cost = max(
            to_float(canonical_value(row, "unit_cost", "cost", "cogs"), default=0.0),
            to_float(canonical_value(row, "unit_price", "price", "price_each"), default=0.0) * 0.65,
        )
        promised_date = parse_iso_date(
            canonical_value(row, "promised_date", "delivery_date", "received_date")
        )
        actual_date = parse_iso_date(
            canonical_value(row, "actual_delivery_date", "received_date", "delivery_date")
        )
        current = supplier_rollups[supplier_id]
        current["supplier_id"] = supplier_id
        current["supplier_name"] = supplier_name
        current["line_count"] += 1
        current["spend_estimate"] += ordered_qty * unit_cost
        if promised_date is not None:
            current["promised_lines"] += 1
            comparison_date = actual_date or COMMERCIAL_REPORTING_REFERENCE_DATE
            if comparison_date <= promised_date:
                current["on_time_lines"] += 1
            else:
                current["breach_lines"] += 1
                current["delayed_receipt_qty"] += max(received_qty, ordered_qty)

    rows: list[dict[str, Any]] = []
    risk_labels: list[str] = []
    total_spend_estimate = 0.0
    spend_at_risk = 0.0
    total_fill_rate = 0.0
    total_on_time = 0.0
    total_lead_time = 0.0
    high_risk_supplier_count = 0

    for supplier_id, metrics in supplier_rollups.items():
        base = supplier_rows.get(supplier_id, {})
        fill_rate = to_float(base.get("fill_rate"), default=0.0)
        average_lead_time = to_float(base.get("average_lead_time_days"), default=0.0)
        variability = to_float(base.get("lead_time_variability_days"), default=0.0)
        average_moq = to_float(base.get("average_moq"), default=0.0)
        risk_band = to_text(base.get("procurement_risk_band") or "medium")
        promised_lines = int(metrics["promised_lines"])
        on_time_rate = (
            _safe_rate(float(metrics["on_time_lines"]), float(promised_lines))
            if promised_lines
            else 0.0
        )
        sla_breach_rate = (
            _safe_rate(float(metrics["breach_lines"]), float(promised_lines))
            if promised_lines
            else 0.0
        )
        spend_estimate = round(float(metrics["spend_estimate"]), 2)
        delayed_receipt_qty = round(float(metrics["delayed_receipt_qty"]), 2)
        if risk_band == "high":
            high_risk_supplier_count += 1
            spend_at_risk += spend_estimate
        elif risk_band == "medium":
            spend_at_risk += round(spend_estimate * 0.5, 2)
        if sla_breach_rate >= 0.35:
            recommended_action = "open supplier recovery plan and expedite open purchase orders"
        elif fill_rate < 0.9:
            recommended_action = "tighten fill-rate SLA and rebalance demand allocation"
        else:
            recommended_action = to_text(
                base.get("recommended_action") or "keep standard procurement cadence"
            )
        risk_labels.append(risk_band)
        total_spend_estimate += spend_estimate
        total_fill_rate += fill_rate
        total_on_time += on_time_rate
        total_lead_time += average_lead_time
        rows.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": to_text(metrics.get("supplier_name") or supplier_id),
                "order_line_count": int(metrics["line_count"]),
                "fill_rate": round(fill_rate, 4),
                "on_time_delivery_rate": round(on_time_rate, 4),
                "sla_breach_rate": round(sla_breach_rate, 4),
                "average_lead_time_days": round(average_lead_time, 2),
                "lead_time_variability_days": round(variability, 2),
                "average_moq": round(average_moq, 2),
                "spend_estimate": spend_estimate,
                "delayed_receipt_qty": delayed_receipt_qty,
                "procurement_risk_band": risk_band,
                "recommended_action": recommended_action,
            }
        )

    rows.sort(
        key=lambda item: (
            item["procurement_risk_band"] != "high",
            item["on_time_delivery_rate"],
            -item["spend_estimate"],
        )
    )
    supplier_count = len(rows)
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": COMMERCIAL_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "supplier_and_procurement_intelligence_pack",
        "summary": {
            "supplier_count": supplier_count,
            "high_risk_supplier_count": high_risk_supplier_count,
            "total_spend_estimate": round(total_spend_estimate, 2),
            "average_fill_rate": round(total_fill_rate / supplier_count, 4)
            if supplier_count
            else 0.0,
            "average_on_time_delivery_rate": round(total_on_time / supplier_count, 4)
            if supplier_count
            else 0.0,
            "average_lead_time_days": round(total_lead_time / supplier_count, 2)
            if supplier_count
            else 0.0,
            "spend_at_risk": round(spend_at_risk, 2),
            "dominant_risk_band": _dominant_label(risk_labels),
        },
        "rows": rows,
    }
    payload = write_json(artifact_path, payload)
    payload = dict(payload)
    payload["rows"] = list(payload.get("rows", []))[:limit]
    return payload


def get_returns_profit_leakage_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_returns_profit_leakage_report.json"
    cached = _artifact_meta(artifact_path, upload_id, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["categories"] = list(payload.get("categories", []))[:limit]
        return payload

    returns_artifact = get_or_create_returns_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    expected_by_order = {
        to_text(item.get("order_id")): item
        for item in returns_artifact.get("scores", [])
        if isinstance(item, dict)
    }
    category_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_ids": set(),
            "returned_order_ids": set(),
            "expected_return_cost": 0.0,
            "actual_return_cost": 0.0,
            "delayed_return_cost": 0.0,
            "discount_linked_return_cost": 0.0,
            "net_revenue": 0.0,
        }
    )
    waterfall_totals = {
        "expected_return_cost": 0.0,
        "actual_return_cost": 0.0,
        "delay_linked_return_cost": 0.0,
        "discount_linked_return_cost": 0.0,
        "open_risk_exposure": 0.0,
    }

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    for row in iter_normalized_rows(csv_path):
        order_id = canonical_value(row, "order_id") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = max(
            to_float(canonical_value(row, "unit_price", "price", "price_each"), default=0.0), 0.0
        )
        list_price = max(
            to_float(canonical_value(row, "list_price", "msrp"), default=unit_price), unit_price
        )
        gross_revenue = max(list_price * quantity, 0.0)
        net_revenue = max(unit_price * quantity, 0.0)
        if gross_revenue > 0:
            discount_rate = max(0.0, min(1.0, 1.0 - (net_revenue / gross_revenue)))
        else:
            discount_rate = 0.0
        promised_date = parse_iso_date(canonical_value(row, "promised_date", "promise_date"))
        actual_delivery_date = parse_iso_date(
            canonical_value(row, "actual_delivery_date", "delivered_date", "delivery_date")
        )
        comparison_date = actual_delivery_date or COMMERCIAL_REPORTING_REFERENCE_DATE
        shipment_delay_days = 0.0
        if promised_date is not None:
            shipment_delay_days = max(float((comparison_date - promised_date).days), 0.0)
        explicit_return_cost_text = canonical_value(row, "return_cost", "actual_return_cost")
        explicit_return_cost = (
            to_float(explicit_return_cost_text, default=0.0) if explicit_return_cost_text else None
        )
        returned = _parse_return_flag(row)
        expected_item = expected_by_order.get(order_id, {})
        expected_return_cost = max(
            to_float(expected_item.get("expected_return_cost"), default=0.0), 0.0
        )
        actual_return_cost = 0.0
        if returned:
            actual_return_cost = _estimate_return_cost(
                gross_revenue=gross_revenue,
                discount_rate=discount_rate,
                shipment_delay_days=shipment_delay_days,
                explicit_return_cost=explicit_return_cost,
            )
        else:
            open_probability = to_float(expected_item.get("return_probability"), default=0.0)
            waterfall_totals["open_risk_exposure"] += round(
                expected_return_cost * open_probability, 2
            )
        current = category_rollups[category]
        current["order_ids"].add(order_id)
        current["expected_return_cost"] += expected_return_cost
        current["actual_return_cost"] += actual_return_cost
        current["net_revenue"] += net_revenue
        if returned:
            current["returned_order_ids"].add(order_id)
        if returned and shipment_delay_days > 0:
            current["delayed_return_cost"] += actual_return_cost
        if returned and discount_rate >= 0.15:
            current["discount_linked_return_cost"] += actual_return_cost
        waterfall_totals["expected_return_cost"] += expected_return_cost
        waterfall_totals["actual_return_cost"] += actual_return_cost
        if returned and shipment_delay_days > 0:
            waterfall_totals["delay_linked_return_cost"] += actual_return_cost
        if returned and discount_rate >= 0.15:
            waterfall_totals["discount_linked_return_cost"] += actual_return_cost

    categories: list[dict[str, Any]] = []
    high_loss_category_count = 0
    total_orders = 0
    total_returned_orders = 0
    for category, metrics in category_rollups.items():
        order_count = len(metrics["order_ids"])
        returned_order_count = len(metrics["returned_order_ids"])
        total_orders += order_count
        total_returned_orders += returned_order_count
        expected_return_cost = round(float(metrics["expected_return_cost"]), 2)
        actual_return_cost = round(float(metrics["actual_return_cost"]), 2)
        delayed_return_cost = round(float(metrics["delayed_return_cost"]), 2)
        discount_linked_return_cost = round(float(metrics["discount_linked_return_cost"]), 2)
        net_revenue = round(float(metrics["net_revenue"]), 2)
        leakage_rate = _safe_rate(actual_return_cost, net_revenue)
        return_rate = (
            _safe_rate(float(returned_order_count), float(order_count)) if order_count else 0.0
        )
        leakage_band = _pressure_band(leakage_rate)
        if leakage_band in {"critical", "high"}:
            high_loss_category_count += 1
        if leakage_rate >= 0.2:
            recommended_action = "tighten return policy and review merchandising economics"
        elif delayed_return_cost >= max(actual_return_cost * 0.35, 1.0):
            recommended_action = "fix fulfillment promise accuracy and carrier handoff"
        elif discount_linked_return_cost >= max(actual_return_cost * 0.3, 1.0):
            recommended_action = "rework discount depth and post-promo QA"
        else:
            recommended_action = "monitor return drivers and keep targeted controls"
        categories.append(
            {
                "category": category,
                "order_count": order_count,
                "returned_order_count": returned_order_count,
                "return_rate": round(return_rate, 4),
                "expected_return_cost": expected_return_cost,
                "actual_return_cost": actual_return_cost,
                "delayed_return_cost": delayed_return_cost,
                "discount_linked_return_cost": discount_linked_return_cost,
                "net_revenue": net_revenue,
                "leakage_rate": round(leakage_rate, 4),
                "leakage_band": leakage_band,
                "recommended_action": recommended_action,
            }
        )

    categories.sort(
        key=lambda item: (
            item["actual_return_cost"],
            item["expected_return_cost"],
            item["net_revenue"],
        ),
        reverse=True,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": COMMERCIAL_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "returns_profit_leakage_report",
        "summary": {
            "total_orders": total_orders,
            "returned_order_count": total_returned_orders,
            "total_expected_return_cost": round(float(waterfall_totals["expected_return_cost"]), 2),
            "total_actual_return_cost": round(float(waterfall_totals["actual_return_cost"]), 2),
            "delay_linked_return_cost": round(
                float(waterfall_totals["delay_linked_return_cost"]), 2
            ),
            "discount_linked_return_cost": round(
                float(waterfall_totals["discount_linked_return_cost"]), 2
            ),
            "high_loss_category_count": high_loss_category_count,
            "leakage_pressure_band": _pressure_band(
                _safe_rate(
                    float(waterfall_totals["actual_return_cost"]),
                    sum(item["net_revenue"] for item in categories),
                )
            ),
        },
        "waterfall": [
            {
                "component": "expected_return_cost",
                "amount": round(float(waterfall_totals["expected_return_cost"]), 2),
                "rationale": "Model-estimated gross profit leakage from return risk across scored orders.",
            },
            {
                "component": "actual_return_cost",
                "amount": round(float(waterfall_totals["actual_return_cost"]), 2),
                "rationale": "Observed return leakage estimated from actual returned orders and shipment conditions.",
            },
            {
                "component": "delay_linked_return_cost",
                "amount": round(float(waterfall_totals["delay_linked_return_cost"]), 2),
                "rationale": "Returned orders where fulfillment delay amplified the cost burden.",
            },
            {
                "component": "discount_linked_return_cost",
                "amount": round(float(waterfall_totals["discount_linked_return_cost"]), 2),
                "rationale": "Returned orders with discount-heavy economics that weakened profit quality.",
            },
            {
                "component": "open_risk_exposure",
                "amount": round(float(waterfall_totals["open_risk_exposure"]), 2),
                "rationale": "Open expected exposure still sitting in non-returned but high-risk scored orders.",
            },
        ],
        "categories": categories,
    }
    payload = write_json(artifact_path, payload)
    payload = dict(payload)
    payload["categories"] = list(payload.get("categories", []))[:limit]
    return payload


def get_promotion_pricing_effectiveness_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_promotion_pricing_effectiveness_report.json"
    cached = _artifact_meta(artifact_path, upload_id, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["promotions"] = list(payload.get("promotions", []))[:limit]
        payload["categories"] = list(payload.get("categories", []))[:limit]
        return payload

    build_promotion_pricing_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    promo_rollups: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "promo_code": "no_promo",
            "category": "uncategorized",
            "order_ids": set(),
            "skus": set(),
            "gross_revenue": 0.0,
            "net_revenue": 0.0,
            "discount_value": 0.0,
            "quantity": 0.0,
            "cost": 0.0,
        }
    )
    category_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_ids": set(),
            "promo_order_ids": set(),
            "gross_revenue": 0.0,
            "net_revenue": 0.0,
            "promo_gross_revenue": 0.0,
            "promo_net_revenue": 0.0,
            "promo_discount_value": 0.0,
            "promo_quantity": 0.0,
            "promo_cost": 0.0,
            "non_promo_order_ids": set(),
            "non_promo_quantity": 0.0,
            "non_promo_net_revenue": 0.0,
            "non_promo_cost": 0.0,
        }
    )

    for row in iter_normalized_rows(csv_path):
        order_id = canonical_value(row, "order_id") or "unknown"
        sku = canonical_value(row, "sku", "product_id") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        raw_promo_code = canonical_value(row, "promo_code", "coupon_code", "discount_code")
        normalized_promo_code = raw_promo_code.strip().lower()
        promo_code = raw_promo_code or "no_promo"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = max(
            to_float(canonical_value(row, "unit_price", "price", "price_each"), default=0.0), 0.0
        )
        list_price = max(
            to_float(canonical_value(row, "list_price", "msrp"), default=unit_price), unit_price
        )
        unit_cost = max(
            to_float(canonical_value(row, "unit_cost", "cost", "cogs"), default=0.0), 0.0
        )
        gross_revenue = max(list_price * quantity, 0.0)
        net_revenue = max(unit_price * quantity, 0.0)
        discount_value = max(gross_revenue - net_revenue, 0.0)
        is_named_promo = normalized_promo_code not in {"", "none", "no_promo", "null", "na"}
        is_promo = is_named_promo or discount_value >= gross_revenue * 0.15
        if not is_named_promo:
            promo_code = "no_promo"
        category_current = category_rollups[category]
        category_current["order_ids"].add(order_id)
        category_current["gross_revenue"] += gross_revenue
        category_current["net_revenue"] += net_revenue
        if is_promo:
            key = (promo_code, category)
            current = promo_rollups[key]
            current["promo_code"] = promo_code
            current["category"] = category
            current["order_ids"].add(order_id)
            current["skus"].add(sku)
            current["gross_revenue"] += gross_revenue
            current["net_revenue"] += net_revenue
            current["discount_value"] += discount_value
            current["quantity"] += quantity
            current["cost"] += unit_cost * quantity
            category_current["promo_order_ids"].add(order_id)
            category_current["promo_gross_revenue"] += gross_revenue
            category_current["promo_net_revenue"] += net_revenue
            category_current["promo_discount_value"] += discount_value
            category_current["promo_quantity"] += quantity
            category_current["promo_cost"] += unit_cost * quantity
        else:
            category_current["non_promo_order_ids"].add(order_id)
            category_current["non_promo_quantity"] += quantity
            category_current["non_promo_net_revenue"] += net_revenue
            category_current["non_promo_cost"] += unit_cost * quantity

    promotions: list[dict[str, Any]] = []
    categories: list[dict[str, Any]] = []
    uplift_values: list[float] = []
    strong_promo_count = 0
    weak_promo_count = 0
    promo_order_count = 0
    promo_revenue = 0.0
    total_discount_value = 0.0

    for (promo_code, category), metrics in promo_rollups.items():
        category_base = category_rollups[category]
        gross_revenue = round(float(metrics["gross_revenue"]), 2)
        net_revenue = round(float(metrics["net_revenue"]), 2)
        discount_value = round(float(metrics["discount_value"]), 2)
        cost = float(metrics["cost"])
        promoted_order_count = len(metrics["order_ids"])
        promo_order_count += promoted_order_count
        promo_revenue += net_revenue
        total_discount_value += discount_value
        discount_rate = _safe_rate(discount_value, gross_revenue)
        price_realization = _safe_rate(net_revenue, gross_revenue)
        promo_margin_rate = _safe_rate(net_revenue - cost, net_revenue)
        non_promo_margin_rate = _safe_rate(
            float(category_base["non_promo_net_revenue"]) - float(category_base["non_promo_cost"]),
            float(category_base["non_promo_net_revenue"]),
        )
        promo_avg_units_per_order = _safe_rate(
            float(metrics["quantity"]), float(promoted_order_count)
        )
        non_promo_avg_units_per_order = _safe_rate(
            float(category_base["non_promo_quantity"]),
            float(len(category_base["non_promo_order_ids"])),
        )
        if non_promo_avg_units_per_order > 0:
            uplift_proxy = round(promo_avg_units_per_order / non_promo_avg_units_per_order, 4)
        else:
            uplift_proxy = 1.0
        uplift_values.append(uplift_proxy)
        margin_gap = round(promo_margin_rate - non_promo_margin_rate, 4)
        effectiveness_band = _effectiveness_band(uplift_proxy, margin_gap, discount_rate)
        if effectiveness_band == "efficient":
            strong_promo_count += 1
        if effectiveness_band == "dilutive":
            weak_promo_count += 1
        if effectiveness_band == "efficient":
            recommended_action = (
                "scale this mechanic selectively and protect inventory availability"
            )
        elif effectiveness_band == "mixed":
            recommended_action = "tighten targeting and cap discount depth"
        else:
            recommended_action = "retire or redesign this promotion before the next cycle"
        promotions.append(
            {
                "promo_code": promo_code,
                "category": category,
                "promoted_order_count": promoted_order_count,
                "sku_count": len(metrics["skus"]),
                "gross_revenue": gross_revenue,
                "net_revenue": net_revenue,
                "discount_value": discount_value,
                "discount_rate": round(discount_rate, 4),
                "price_realization": round(price_realization, 4),
                "promo_margin_rate": round(promo_margin_rate, 4),
                "non_promo_margin_rate": round(non_promo_margin_rate, 4),
                "margin_gap": margin_gap,
                "uplift_proxy": uplift_proxy,
                "effectiveness_band": effectiveness_band,
                "recommended_action": recommended_action,
            }
        )

    for category, metrics in category_rollups.items():
        total_orders = len(metrics["order_ids"])
        promo_order_share = _safe_rate(float(len(metrics["promo_order_ids"])), float(total_orders))
        promo_revenue_share = _safe_rate(
            float(metrics["promo_net_revenue"]), float(metrics["net_revenue"])
        )
        promo_discount_rate = _safe_rate(
            float(metrics["promo_discount_value"]), float(metrics["promo_gross_revenue"])
        )
        promo_margin_rate = _safe_rate(
            float(metrics["promo_net_revenue"]) - float(metrics["promo_cost"]),
            float(metrics["promo_net_revenue"]),
        )
        non_promo_margin_rate = _safe_rate(
            float(metrics["non_promo_net_revenue"]) - float(metrics["non_promo_cost"]),
            float(metrics["non_promo_net_revenue"]),
        )
        promo_margin_gap = round(promo_margin_rate - non_promo_margin_rate, 4)
        dependency_band = _promo_dependency_band(promo_revenue_share)
        if dependency_band == "promo_heavy":
            recommended_action = (
                "reduce dependency with cleaner base pricing and targeted campaigns"
            )
        elif promo_margin_gap < -0.12:
            recommended_action = "rebuild promo economics before the next merchandising event"
        else:
            recommended_action = "keep promo use selective and monitor price realization"
        categories.append(
            {
                "category": category,
                "promo_order_share": round(promo_order_share, 4),
                "promo_revenue_share": round(promo_revenue_share, 4),
                "promo_discount_rate": round(promo_discount_rate, 4),
                "promo_margin_gap": promo_margin_gap,
                "promo_dependency_band": dependency_band,
                "recommended_action": recommended_action,
            }
        )

    promotions.sort(
        key=lambda item: (
            item["effectiveness_band"] == "dilutive",
            item["discount_value"],
            -item["net_revenue"],
        ),
        reverse=True,
    )
    categories.sort(
        key=lambda item: (
            item["promo_dependency_band"] == "promo_heavy",
            item["promo_revenue_share"],
            -item["promo_margin_gap"],
        ),
        reverse=True,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": COMMERCIAL_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "promotion_and_pricing_effectiveness_analysis",
        "summary": {
            "promoted_order_count": promo_order_count,
            "promo_code_count": len(promotions),
            "promo_revenue": round(promo_revenue, 2),
            "discount_value": round(total_discount_value, 2),
            "average_discount_rate": round(
                _safe_rate(total_discount_value, promo_revenue + total_discount_value), 4
            ),
            "average_uplift_proxy": round(sum(uplift_values) / len(uplift_values), 4)
            if uplift_values
            else 0.0,
            "strong_promo_count": strong_promo_count,
            "weak_promo_count": weak_promo_count,
        },
        "promotions": promotions,
        "categories": categories,
    }
    payload = write_json(artifact_path, payload)
    payload = dict(payload)
    payload["promotions"] = list(payload.get("promotions", []))[:limit]
    payload["categories"] = list(payload.get("categories", []))[:limit]
    return payload


def get_customer_cohort_retention_review(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_customer_cohort_retention_review.json"
    cached = _artifact_meta(artifact_path, upload_id, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["cohorts"] = list(payload.get("cohorts", []))[:limit]
        payload["focus_customers"] = list(payload.get("focus_customers", []))[: min(limit, 10)]
        return payload

    cohort_artifact = build_cohort_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    customer_artifact = build_customer_intelligence_artifact(
        upload_id, uploads_dir, artifact_dir, refresh
    )
    churn_artifact = build_customer_churn_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    customer_segments = {
        to_text(item.get("customer_id")): item
        for item in customer_artifact.get("customers", [])
        if isinstance(item, dict)
    }
    churn_rows = {
        to_text(item.get("customer_id")): item
        for item in churn_artifact.get("customers", [])
        if isinstance(item, dict)
    }
    customer_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "dates": [],
            "order_ids": set(),
            "revenue": 0.0,
        }
    )
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    for row in iter_normalized_rows(csv_path):
        customer_id = canonical_value(row, "customer_id", "buyer_id", "client_id") or "guest"
        order_id = canonical_value(row, "order_id") or f"synthetic-{customer_id}"
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = max(
            to_float(canonical_value(row, "unit_price", "price", "price_each"), default=0.0), 0.0
        )
        current = customer_rollups[customer_id]
        current["order_ids"].add(order_id)
        current["revenue"] += quantity * unit_price
        if order_date is not None:
            current["dates"].append(order_date)

    cohort_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "customer_count": 0,
            "repeat_customer_count": 0,
            "retained_60d_count": 0,
            "at_risk_customer_count": 0,
            "lost_customer_count": 0,
            "revenue": 0.0,
        }
    )
    focus_customers: list[dict[str, Any]] = []
    strongest_cohort_month = "unknown"
    weakest_cohort_month = "unknown"
    cohort_scores: list[tuple[str, float]] = []

    for customer_id, metrics in customer_rollups.items():
        dates = sorted(set(metrics["dates"]))
        if dates:
            first_order_date = dates[0]
            retained_60d = any(
                (item - first_order_date).days <= 60 and item != first_order_date for item in dates
            )
            cohort_month = first_order_date.strftime("%Y-%m")
        else:
            retained_60d = False
            cohort_month = "unknown"
        order_count = len(metrics["order_ids"])
        repeat_customer = order_count >= 2
        churn_item = churn_rows.get(customer_id, {})
        churn_band = to_text(churn_item.get("churn_risk_band") or "low")
        cohort_current = cohort_rollups[cohort_month]
        cohort_current["customer_count"] += 1
        cohort_current["revenue"] += float(metrics["revenue"])
        if repeat_customer:
            cohort_current["repeat_customer_count"] += 1
        if retained_60d:
            cohort_current["retained_60d_count"] += 1
        if churn_band in {"high", "lost"}:
            cohort_current["at_risk_customer_count"] += 1
        if churn_band == "lost":
            cohort_current["lost_customer_count"] += 1

    for customer_id, churn_item in churn_rows.items():
        segment_item = customer_segments.get(customer_id, {})
        cohort_month = "unknown"
        dates = sorted(set(customer_rollups.get(customer_id, {}).get("dates", [])))
        if dates:
            cohort_month = dates[0].strftime("%Y-%m")
        focus_customers.append(
            {
                "customer_id": customer_id,
                "cohort_month": cohort_month,
                "segment": to_text(segment_item.get("segment") or "unknown"),
                "churn_risk_band": to_text(churn_item.get("churn_risk_band") or "low"),
                "recency_days": int(to_float(churn_item.get("recency_days"), default=0.0)),
                "total_revenue": round(to_float(churn_item.get("total_revenue"), default=0.0), 2),
                "recommended_action": to_text(
                    churn_item.get("recommended_action") or "maintain loyalty touchpoints"
                ),
            }
        )

    cohorts: list[dict[str, Any]] = []
    total_customers = 0
    total_repeat_customers = 0
    total_retained_60d = 0
    total_high_risk = 0
    total_lost = 0
    for cohort_month, metrics in sorted(cohort_rollups.items()):
        customer_count = int(metrics["customer_count"])
        repeat_count = int(metrics["repeat_customer_count"])
        retained_60d_count = int(metrics["retained_60d_count"])
        at_risk_count = int(metrics["at_risk_customer_count"])
        lost_count = int(metrics["lost_customer_count"])
        revenue = round(float(metrics["revenue"]), 2)
        repeat_rate = (
            _safe_rate(float(repeat_count), float(customer_count)) if customer_count else 0.0
        )
        retained_60d_rate = (
            _safe_rate(float(retained_60d_count), float(customer_count)) if customer_count else 0.0
        )
        at_risk_rate = (
            _safe_rate(float(at_risk_count), float(customer_count)) if customer_count else 0.0
        )
        health_band = _cohort_health_band(retained_60d_rate, at_risk_rate)
        if health_band == "healthy":
            recommended_action = (
                "keep the loyalty playbook and mine this cohort for expansion offers"
            )
        elif health_band == "watch":
            recommended_action = "tighten second-order journeys and watch recency carefully"
        else:
            recommended_action = "launch retention recovery and win-back sequence immediately"
        cohorts.append(
            {
                "cohort_month": cohort_month,
                "customer_count": customer_count,
                "repeat_customer_count": repeat_count,
                "repeat_customer_rate": round(repeat_rate, 4),
                "retained_60d_count": retained_60d_count,
                "retained_60d_rate": round(retained_60d_rate, 4),
                "at_risk_customer_count": at_risk_count,
                "lost_customer_count": lost_count,
                "revenue": revenue,
                "average_revenue_per_customer": round(_safe_rate(revenue, float(customer_count)), 2)
                if customer_count
                else 0.0,
                "cohort_health_band": health_band,
                "recommended_action": recommended_action,
            }
        )
        cohort_scores.append((cohort_month, retained_60d_rate - at_risk_rate))
        total_customers += customer_count
        total_repeat_customers += repeat_count
        total_retained_60d += retained_60d_count
        total_high_risk += at_risk_count
        total_lost += lost_count

    if cohort_scores:
        strongest_cohort_month = max(cohort_scores, key=lambda item: item[1])[0]
        weakest_cohort_month = min(cohort_scores, key=lambda item: item[1])[0]
    focus_customers.sort(
        key=lambda item: (
            item["churn_risk_band"] not in {"lost", "high"},
            -item["recency_days"],
            item["total_revenue"],
        )
    )
    summary_from_artifact = cohort_artifact.get("summary", {})
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": COMMERCIAL_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "customer_cohort_and_retention_review",
        "summary": {
            "cohort_count": int(summary_from_artifact.get("cohort_count", len(cohorts))),
            "customer_count": total_customers,
            "repeat_customer_rate": round(
                _safe_rate(float(total_repeat_customers), float(total_customers)), 4
            )
            if total_customers
            else 0.0,
            "retained_60d_rate": round(
                _safe_rate(float(total_retained_60d), float(total_customers)), 4
            )
            if total_customers
            else 0.0,
            "high_risk_customer_count": total_high_risk,
            "lost_customer_count": total_lost,
            "retention_pressure_band": _pressure_band(
                _safe_rate(float(total_high_risk), float(total_customers))
            ),
            "strongest_cohort_month": strongest_cohort_month,
            "weakest_cohort_month": weakest_cohort_month,
        },
        "cohorts": cohorts,
        "focus_customers": focus_customers[:10],
    }
    payload = write_json(artifact_path, payload)
    payload = dict(payload)
    payload["cohorts"] = list(payload.get("cohorts", []))[:limit]
    payload["focus_customers"] = list(payload.get("focus_customers", []))[: min(limit, 10)]
    return payload
