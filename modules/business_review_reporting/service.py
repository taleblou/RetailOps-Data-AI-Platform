# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         service.py
# Path:         modules/business_review_reporting/service.py
#
# Summary:      Implements the business review reporting service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for business review reporting workflows.
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
#   - Key APIs: build_business_review_artifact, get_business_report_catalog, get_executive_business_review, get_store_performance_pack, get_category_merchandising_review, get_sku_deep_dive_report, ...
#   - Dependencies: __future__, collections, datetime, pathlib, typing, modules.assortment_intelligence.service, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from modules.assortment_intelligence.service import build_assortment_artifact
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
from modules.fulfillment_sla_intelligence.service import build_fulfillment_sla_artifact
from modules.inventory_aging_intelligence.service import build_inventory_aging_artifact
from modules.profitability_intelligence.service import build_profitability_artifact
from modules.promotion_pricing_intelligence.service import build_promotion_pricing_artifact
from modules.sales_anomaly_intelligence.service import build_sales_anomaly_artifact
from modules.seasonality_intelligence.service import build_seasonality_artifact

from .commercial_reporting_service import COMMERCIAL_REPORT_INDEX
from .decision_intelligence_service import DECISION_INTELLIGENCE_REPORT_INDEX
from .executive_scorecard_service import EXECUTIVE_SCORECARD_REPORT_INDEX
from .governance_reporting_service import GOVERNANCE_REPORT_INDEX
from .portfolio_reporting_service import PORTFOLIO_REPORT_INDEX
from .working_capital_reporting_service import WORKING_CAPITAL_REPORT_INDEX

BUSINESS_REVIEW_REPORTING_VERSION = "business-review-reporting-v1"
RETURN_STATUSES = {"returned", "return", "refunded", "refund", "exchange"}
TRUTHY_VALUES = {"1", "true", "yes", "y", "returned"}


def _parse_return_flag(normalized_row: dict[str, str]) -> bool:
    order_status = canonical_value(normalized_row, "order_status", "status").lower()
    if order_status in RETURN_STATUSES:
        return True
    return_flag = canonical_value(
        normalized_row,
        "returned",
        "return_flag",
        "is_returned",
        "returned_within_30_days",
    ).lower()
    if return_flag in TRUTHY_VALUES:
        return True
    returned_qty = to_float(canonical_value(normalized_row, "returned_qty", "return_quantity"))
    return returned_qty > 0.0


def _compute_delay_state(row: dict[str, str], reference_date: date) -> tuple[bool, bool, float]:
    promised_date = parse_iso_date(canonical_value(row, "promised_date", "promise_date"))
    actual_delivery_date = parse_iso_date(
        canonical_value(row, "actual_delivery_date", "delivered_date", "delivery_date")
    )
    shipment_status = canonical_value(row, "shipment_status", "status").lower()
    if promised_date is None:
        return False, False, 0.0
    comparator = actual_delivery_date or reference_date
    delay_days = float((comparator - promised_date).days)
    delayed = actual_delivery_date is not None and delay_days > 0
    open_breach = actual_delivery_date is None and delay_days > 0
    if shipment_status in {"late", "delayed"}:
        delayed = True
    return delayed, open_breach, max(delay_days, 0.0)


def _new_rollup(default_group: str = "unknown") -> dict[str, Any]:
    return {
        "group": default_group,
        "orders": set(),
        "customers": set(),
        "skus": set(),
        "stores": set(),
        "regions": set(),
        "quantity": 0.0,
        "revenue": 0.0,
        "gross_revenue": 0.0,
        "cost": 0.0,
        "discount_value": 0.0,
        "delayed_orders": set(),
        "open_breach_orders": set(),
        "returned_orders": set(),
        "promo_orders": set(),
        "first_order_date": None,
        "last_order_date": None,
        "on_hand_units": 0.0,
        "promo_codes": defaultdict(int),
    }


def _update_rollup(
    rollup: dict[str, Any],
    *,
    order_id: str,
    customer_id: str,
    sku: str,
    store_code: str,
    region: str,
    quantity: float,
    revenue: float,
    gross_revenue: float,
    cost: float,
    discount_value: float,
    delayed: bool,
    open_breach: bool,
    returned: bool,
    has_promo: bool,
    promo_code: str,
    order_date: date | None,
    on_hand_units: float,
) -> None:
    rollup["orders"].add(order_id)
    rollup["customers"].add(customer_id)
    rollup["skus"].add(sku)
    rollup["stores"].add(store_code)
    rollup["regions"].add(region)
    rollup["quantity"] = float(rollup["quantity"]) + quantity
    rollup["revenue"] = float(rollup["revenue"]) + revenue
    rollup["gross_revenue"] = float(rollup["gross_revenue"]) + gross_revenue
    rollup["cost"] = float(rollup["cost"]) + cost
    rollup["discount_value"] = float(rollup["discount_value"]) + discount_value
    rollup["on_hand_units"] = max(float(rollup["on_hand_units"]), on_hand_units)
    if delayed:
        rollup["delayed_orders"].add(order_id)
    if open_breach:
        rollup["open_breach_orders"].add(order_id)
    if returned:
        rollup["returned_orders"].add(order_id)
    if has_promo:
        rollup["promo_orders"].add(order_id)
        rollup["promo_codes"][promo_code] += 1
    if order_date is not None:
        first_date = rollup["first_order_date"]
        last_date = rollup["last_order_date"]
        if first_date is None or order_date < first_date:
            rollup["first_order_date"] = order_date
        if last_date is None or order_date > last_date:
            rollup["last_order_date"] = order_date


def _margin_rate(revenue: float, cost: float) -> float:
    return round((revenue - cost) / revenue, 4) if revenue else 0.0


def _safe_rate(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / float(denominator), 4) if denominator else 0.0


def _performance_band(score: float) -> str:
    if score >= 2.5:
        return "leader"
    if score >= 1.0:
        return "solid"
    if score >= 0.0:
        return "watchlist"
    return "underperformer"


def _movement_signal(
    *,
    margin_rate: float,
    promo_dependency_rate: float,
    slow_mover_rate: float,
) -> str:
    if slow_mover_rate >= 0.45:
        return "slow_tail_pressure"
    if promo_dependency_rate >= 0.55:
        return "promo_led"
    if margin_rate >= 0.35:
        return "healthy_core"
    return "mixed"


def _sku_priority_score(
    *,
    margin_rate: float,
    days_since_last_sale: float,
    return_rate: float,
    open_breach_rate: float,
    delay_rate: float,
    promo_dependency_rate: float,
    days_of_cover: float | None,
) -> float:
    score = 0.0
    if margin_rate < 0.15:
        score += 1.5
    if return_rate >= 0.2:
        score += 1.4
    if open_breach_rate > 0:
        score += 1.2
    if delay_rate >= 0.2:
        score += 1.0
    if promo_dependency_rate >= 0.5:
        score += 0.6
    if days_since_last_sale >= 45:
        score += 1.2
    if days_of_cover is not None and days_of_cover >= 60:
        score += 0.8
    return round(score, 2)


def _priority_label(score: float) -> str:
    if score >= 3.5:
        return "critical"
    if score >= 2.0:
        return "high"
    if score >= 1.0:
        return "medium"
    return "low"


def _build_base_rollups(csv_path: Path) -> dict[str, Any]:
    store_rollups: dict[str, dict[str, Any]] = defaultdict(lambda: _new_rollup())
    region_rollups: dict[str, dict[str, Any]] = defaultdict(lambda: _new_rollup())
    category_rollups: dict[str, dict[str, Any]] = defaultdict(lambda: _new_rollup())
    sku_rollups: dict[str, dict[str, Any]] = defaultdict(lambda: _new_rollup())
    overall = _new_rollup("all")
    reference_date = date(2026, 3, 29)

    rows = list(iter_normalized_rows(csv_path))
    for row in rows:
        for candidate in [
            parse_iso_date(canonical_value(row, "order_date", "created_at", "date")),
            parse_iso_date(canonical_value(row, "promised_date", "promise_date")),
            parse_iso_date(
                canonical_value(
                    row,
                    "actual_delivery_date",
                    "delivered_date",
                    "delivery_date",
                )
            ),
        ]:
            if candidate is not None:
                reference_date = max(reference_date, candidate)

    for row in rows:
        order_id = canonical_value(row, "order_id") or "unknown-order"
        customer_id = canonical_value(row, "customer_id", "buyer_id", "client_id") or "guest"
        store_code = canonical_value(row, "store_code", "store", "store_id") or "unknown"
        region = canonical_value(row, "region", "shipping_region") or "unknown"
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        promo_code = (
            canonical_value(row, "promo_code", "coupon_code", "discount_code") or "no_promo"
        )
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"),
            default=0.0,
        )
        list_price = to_float(canonical_value(row, "list_price", "msrp"), default=unit_price)
        unit_cost = to_float(
            canonical_value(row, "unit_cost", "cost", "cogs", "cost_of_goods"),
            default=0.0,
        )
        on_hand_units = to_float(
            canonical_value(
                row,
                "on_hand_units",
                "inventory_on_hand",
                "current_inventory",
                "stock_on_hand",
                "available_stock",
                "on_hand_qty",
                "available_qty",
            ),
            default=0.0,
        )
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        revenue = round(quantity * unit_price, 2)
        gross_revenue = round(quantity * max(list_price, unit_price), 2)
        cost = round(quantity * unit_cost, 2)
        discount_value = round(max(gross_revenue - revenue, 0.0), 2)
        has_promo = promo_code != "no_promo" or discount_value > 0
        returned = _parse_return_flag(row)
        delayed, open_breach, _ = _compute_delay_state(row, reference_date)

        store_rollups[store_code]["group"] = store_code
        region_rollups[region]["group"] = region
        category_rollups[category]["group"] = category
        sku_rollups[sku]["group"] = sku
        sku_rollups[sku]["category"] = category

        for target in [
            overall,
            store_rollups[store_code],
            region_rollups[region],
            category_rollups[category],
            sku_rollups[sku],
        ]:
            _update_rollup(
                target,
                order_id=order_id,
                customer_id=customer_id,
                sku=sku,
                store_code=store_code,
                region=region,
                quantity=quantity,
                revenue=revenue,
                gross_revenue=gross_revenue,
                cost=cost,
                discount_value=discount_value,
                delayed=delayed,
                open_breach=open_breach,
                returned=returned,
                has_promo=has_promo,
                promo_code=promo_code,
                order_date=order_date,
                on_hand_units=on_hand_units,
            )

    return {
        "overall": overall,
        "stores": store_rollups,
        "regions": region_rollups,
        "categories": category_rollups,
        "skus": sku_rollups,
        "reference_date": reference_date,
    }


def _build_supporting_artifacts(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool,
) -> dict[str, Any]:
    dependency_dir = artifact_dir / "dependencies"
    return {
        "profitability": build_profitability_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "profitability",
            refresh,
        ),
        "assortment": build_assortment_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "assortment",
            refresh,
        ),
        "inventory_aging": build_inventory_aging_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "inventory_aging",
            refresh,
        ),
        "promotion": build_promotion_pricing_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "promotion",
            refresh,
        ),
        "seasonality": build_seasonality_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "seasonality",
            refresh,
        ),
        "fulfillment": build_fulfillment_sla_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "fulfillment",
            refresh,
        ),
        "sales_anomaly": build_sales_anomaly_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "sales_anomaly",
            refresh,
        ),
        "cohort": build_cohort_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "cohort",
            refresh,
        ),
        "churn": build_customer_churn_artifact(
            upload_id,
            uploads_dir,
            dependency_dir / "churn",
            refresh,
        ),
    }


def _reporting_period(overall: dict[str, Any], reference_date: date) -> dict[str, Any]:
    start_date = overall.get("first_order_date")
    end_date = overall.get("last_order_date")
    if start_date is None:
        start_text = reference_date.isoformat()
    else:
        start_text = start_date.isoformat()
    if end_date is None:
        end_text = reference_date.isoformat()
        day_count = 0
    else:
        end_text = end_date.isoformat()
        day_count = max((end_date - (start_date or end_date)).days + 1, 1)
    return {
        "start_date": start_text,
        "end_date": end_text,
        "day_count": day_count,
    }


def _top_watchlist_skus(
    *,
    sku_rollups: dict[str, dict[str, Any]],
    inventory_by_sku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    items = []
    reference_date = date(2026, 3, 29)
    for sku, rollup in sku_rollups.items():
        revenue = round(float(rollup["revenue"]), 2)
        cost = round(float(rollup["cost"]), 2)
        margin_rate = _margin_rate(revenue, cost)
        order_count = len(rollup["orders"])
        delay_rate = _safe_rate(len(rollup["delayed_orders"]), order_count)
        open_breach_rate = _safe_rate(len(rollup["open_breach_orders"]), order_count)
        return_rate = _safe_rate(len(rollup["returned_orders"]), order_count)
        promo_dependency_rate = _safe_rate(len(rollup["promo_orders"]), order_count)
        inventory_item = inventory_by_sku.get(sku, {})
        days_since_last_sale = float(inventory_item.get("days_since_last_sale") or 0.0)
        days_of_cover = inventory_item.get("days_of_cover")
        if isinstance(days_of_cover, str) and not days_of_cover:
            days_of_cover = None
        score = _sku_priority_score(
            margin_rate=margin_rate,
            days_since_last_sale=days_since_last_sale,
            return_rate=return_rate,
            open_breach_rate=open_breach_rate,
            delay_rate=delay_rate,
            promo_dependency_rate=promo_dependency_rate,
            days_of_cover=days_of_cover if isinstance(days_of_cover, int | float) else None,
        )
        priority = _priority_label(score)
        if rollup.get("last_order_date") is not None:
            reference_date = max(reference_date, rollup["last_order_date"])
        items.append(
            {
                "sku": sku,
                "category": str(rollup.get("category") or "uncategorized"),
                "priority": priority,
                "priority_score": score,
                "revenue": revenue,
                "gross_margin_rate": margin_rate,
                "days_since_last_sale": days_since_last_sale,
                "return_rate": return_rate,
                "delay_rate": delay_rate,
                "recommended_action": (
                    "reduce exposure, clear stale stock, and review service failures"
                    if priority in {"critical", "high"}
                    else "monitor weekly"
                ),
            }
        )
    items.sort(
        key=lambda item: (item["priority_score"], item["revenue"]),
        reverse=True,
    )
    return items[:5]


def _build_executive_review(
    *,
    overall: dict[str, Any],
    supporting: dict[str, Any],
    sku_rollups: dict[str, dict[str, Any]],
    reference_date: date,
) -> dict[str, Any]:
    profitability_summary = supporting["profitability"]["summary"]
    assortment_summary = supporting["assortment"]["summary"]
    aging_summary = supporting["inventory_aging"]["summary"]
    fulfillment_summary = supporting["fulfillment"]["summary"]
    churn_summary = supporting["churn"]["summary"]
    cohort_summary = supporting["cohort"]["summary"]
    anomaly_summary = supporting["sales_anomaly"]["summary"]
    inventory_by_sku = {
        str(item.get("sku")): item for item in supporting["inventory_aging"].get("skus", [])
    }
    watchlist = _top_watchlist_skus(
        sku_rollups=sku_rollups,
        inventory_by_sku=inventory_by_sku,
    )

    total_revenue = round(float(overall["revenue"]), 2)
    total_cost = round(float(overall["cost"]), 2)
    gross_profit = round(total_revenue - total_cost, 2)
    total_orders = len(overall["orders"])
    metric_cards = [
        {
            "label": "Total revenue",
            "value": total_revenue,
            "context": "commercial output across the reporting period",
        },
        {
            "label": "Gross margin rate",
            "value": round(float(profitability_summary.get("gross_margin_rate", 0.0)), 4),
            "context": "profitability quality after estimated cost coverage",
        },
        {
            "label": "On-time rate",
            "value": round(float(fulfillment_summary.get("on_time_rate", 0.0)), 4),
            "context": "delivered orders that met promise date",
        },
        {
            "label": "Repeat customer rate",
            "value": round(float(cohort_summary.get("repeat_customer_rate", 0.0)), 4),
            "context": "customers with at least two orders",
        },
        {
            "label": "Stale SKU count",
            "value": int(aging_summary.get("stale_sku_count", 0)),
            "context": "SKUs with aging pressure from inventory review",
        },
    ]

    top_risks = []
    if int(fulfillment_summary.get("open_breach_risk_count", 0)) > 0:
        top_risks.append(
            {
                "title": "Open fulfillment breach risk",
                "impact": int(fulfillment_summary["open_breach_risk_count"]),
                "rationale": "orders are already past promise date without a delivery confirmation",
                "recommended_action": "prioritize the queue and update customer ETA today",
            }
        )
    if int(aging_summary.get("critical_aging_count", 0)) > 0:
        top_risks.append(
            {
                "title": "Critical aging inventory",
                "impact": int(aging_summary["critical_aging_count"]),
                "rationale": "inventory is staying on hand without recent sell-through",
                "recommended_action": "freeze replenishment and plan markdown or bundle cleanup",
            }
        )
    if int(churn_summary.get("high_risk_customer_count", 0)) > 0:
        top_risks.append(
            {
                "title": "At-risk customers",
                "impact": int(churn_summary["high_risk_customer_count"]),
                "rationale": "customer recency has moved beyond the expected reorder cycle",
                "recommended_action": "launch a targeted retention or win-back journey",
            }
        )
    if int(anomaly_summary.get("anomaly_count", 0)) > 0:
        top_risks.append(
            {
                "title": "Sales anomalies detected",
                "impact": int(anomaly_summary["anomaly_count"]),
                "rationale": (
                    "recent daily revenue has moved materially above or below the baseline"
                ),
                "recommended_action": (
                    "review campaign, stock, and fulfillment causes before the next cycle"
                ),
            }
        )
    if int(profitability_summary.get("loss_making_sku_count", 0)) > 0:
        top_risks.append(
            {
                "title": "Loss-making SKUs",
                "impact": int(profitability_summary["loss_making_sku_count"]),
                "rationale": "estimated cost exceeds realized revenue on part of the assortment",
                "recommended_action": "review pricing floors, supplier cost, and portfolio role",
            }
        )

    top_actions = [
        {
            "title": "Work the SKU watchlist",
            "owner": "merchandising and operations",
            "expected_outcome": "reduce trapped capital and avoid avoidable service failures",
        },
        {
            "title": "Protect on-time delivery",
            "owner": "fulfillment",
            "expected_outcome": "recover customer trust before more orders breach promise date",
        },
        {
            "title": "Defend repeat revenue",
            "owner": "CRM",
            "expected_outcome": (
                "retain the highest-risk customers while their recency window is still recoverable"
            ),
        },
    ]

    return {
        "report_name": "executive_business_review",
        "headline": (
            f"Revenue reached {total_revenue:.2f} with gross profit {gross_profit:.2f}. "
            "Margin quality is "
            f"{_margin_rate(total_revenue, total_cost):.1%} and on-time delivery is "
            f"{float(fulfillment_summary.get('on_time_rate', 0.0)):.1%}."
        ),
        "reporting_period": _reporting_period(overall, reference_date),
        "metric_cards": metric_cards,
        "commercial_summary": {
            "total_orders": total_orders,
            "total_customers": len(overall["customers"]),
            "total_units": round(float(overall["quantity"]), 2),
            "gross_profit": gross_profit,
            "avg_order_value": round(total_revenue / total_orders, 2) if total_orders else 0.0,
            "repeat_customer_rate": round(
                float(cohort_summary.get("repeat_customer_rate", 0.0)),
                4,
            ),
        },
        "inventory_summary": {
            "sku_count": int(profitability_summary.get("sku_count", 0)),
            "slow_mover_count": int(assortment_summary.get("slow_mover_count", 0)),
            "long_tail_revenue_share": round(
                float(assortment_summary.get("long_tail_revenue_share", 0.0)),
                4,
            ),
            "stale_sku_count": int(aging_summary.get("stale_sku_count", 0)),
            "critical_aging_count": int(aging_summary.get("critical_aging_count", 0)),
        },
        "fulfillment_summary": {
            "delayed_order_count": int(fulfillment_summary.get("delayed_order_count", 0)),
            "open_breach_risk_count": int(fulfillment_summary.get("open_breach_risk_count", 0)),
            "on_time_rate": round(float(fulfillment_summary.get("on_time_rate", 0.0)), 4),
            "average_delay_days": round(
                float(fulfillment_summary.get("average_delay_days", 0.0)),
                2,
            ),
        },
        "customer_summary": {
            "customer_count": int(churn_summary.get("customer_count", 0)),
            "high_risk_customer_count": int(churn_summary.get("high_risk_customer_count", 0)),
            "lost_customer_count": int(churn_summary.get("lost_customer_count", 0)),
            "repeat_customer_count": int(cohort_summary.get("repeat_customer_count", 0)),
        },
        "top_risks": top_risks,
        "top_actions": top_actions,
        "watchlist_skus": watchlist,
    }


def _build_performance_pack(
    *,
    rollups: dict[str, dict[str, Any]],
    grouping_dimension: str,
) -> dict[str, Any]:
    rows = []
    total_revenue = sum(float(item["revenue"]) for item in rollups.values())
    average_revenue = total_revenue / len(rollups) if rollups else 0.0
    average_margin_rate = (
        sum(_margin_rate(float(item["revenue"]), float(item["cost"])) for item in rollups.values())
        / len(rollups)
        if rollups
        else 0.0
    )
    average_on_time_rate = (
        sum(
            1.0
            - _safe_rate(
                len(item["delayed_orders"]) + len(item["open_breach_orders"]),
                len(item["orders"]),
            )
            for item in rollups.values()
        )
        / len(rollups)
        if rollups
        else 0.0
    )
    for group_name, item in rollups.items():
        revenue = round(float(item["revenue"]), 2)
        cost = round(float(item["cost"]), 2)
        gross_profit = round(revenue - cost, 2)
        order_count = len(item["orders"])
        delayed_order_count = len(item["delayed_orders"])
        open_breach_order_count = len(item["open_breach_orders"])
        returned_order_count = len(item["returned_orders"])
        margin_rate = _margin_rate(revenue, cost)
        on_time_rate = round(
            1.0 - _safe_rate(delayed_order_count + open_breach_order_count, order_count),
            4,
        )
        return_rate = _safe_rate(returned_order_count, order_count)
        promo_dependency_rate = _safe_rate(len(item["promo_orders"]), order_count)
        score = 0.0
        score += 1.0 if revenue >= average_revenue else -0.5
        score += 1.0 if margin_rate >= average_margin_rate else -1.0
        score += 1.0 if on_time_rate >= average_on_time_rate else -1.0
        score += 0.5 if return_rate <= 0.08 else -0.5
        band = _performance_band(score)
        if band == "leader":
            recommended_action = "protect the operating playbook and replicate it to weaker groups"
        elif band == "underperformer":
            recommended_action = "review margin, availability, and service execution immediately"
        else:
            recommended_action = "monitor weekly and close the largest gap versus the average"
        rows.append(
            {
                grouping_dimension: group_name,
                "order_count": order_count,
                "customer_count": len(item["customers"]),
                "sku_count": len(item["skus"]),
                "units": round(float(item["quantity"]), 2),
                "revenue": revenue,
                "gross_profit": gross_profit,
                "gross_margin_rate": margin_rate,
                "avg_order_value": round(revenue / order_count, 2) if order_count else 0.0,
                "on_time_rate": on_time_rate,
                "delayed_order_count": delayed_order_count,
                "open_breach_order_count": open_breach_order_count,
                "return_rate": return_rate,
                "promo_dependency_rate": promo_dependency_rate,
                "performance_band": band,
                "recommended_action": recommended_action,
            }
        )
    rows.sort(key=lambda item: (item["revenue"], item["gross_profit"]), reverse=True)
    summary = {
        "grouping_dimension": grouping_dimension,
        "group_count": len(rows),
        "leader_count": sum(1 for item in rows if item["performance_band"] == "leader"),
        "underperformer_count": sum(
            1 for item in rows if item["performance_band"] == "underperformer"
        ),
        "average_on_time_rate": round(average_on_time_rate, 4),
        "average_margin_rate": round(average_margin_rate, 4),
        "top_group": rows[0][grouping_dimension] if rows else "unknown",
    }
    return {
        "report_name": f"{grouping_dimension}_performance_pack",
        "summary": summary,
        "rows": rows,
    }


def _build_category_review(
    *,
    category_rollups: dict[str, dict[str, Any]],
    assortment: dict[str, Any],
    promotion: dict[str, Any],
) -> dict[str, Any]:
    hero_counts: dict[str, int] = defaultdict(int)
    slow_counts: dict[str, int] = defaultdict(int)
    for item in assortment.get("skus", []):
        category = to_text(item.get("category")) or "uncategorized"
        if to_text(item.get("movement_class")) == "hero":
            hero_counts[category] += 1
        if to_text(item.get("movement_class")) == "slow_mover":
            slow_counts[category] += 1

    promo_by_category: dict[str, dict[str, float]] = defaultdict(
        lambda: {"gross_revenue": 0.0, "net_revenue": 0.0, "discount_value": 0.0}
    )
    for item in promotion.get("skus", []):
        category = to_text(item.get("category")) or "uncategorized"
        promo_by_category[category]["gross_revenue"] += float(item.get("gross_revenue") or 0.0)
        promo_by_category[category]["net_revenue"] += float(item.get("net_revenue") or 0.0)
        promo_by_category[category]["discount_value"] += float(item.get("discount_value") or 0.0)

    categories = []
    for category, item in category_rollups.items():
        revenue = round(float(item["revenue"]), 2)
        cost = round(float(item["cost"]), 2)
        order_count = len(item["orders"])
        sku_count = len(item["skus"])
        margin_rate = _margin_rate(revenue, cost)
        promo_dependency_rate = _safe_rate(len(item["promo_orders"]), order_count)
        slow_mover_rate = _safe_rate(slow_counts[category], sku_count)
        movement_signal = _movement_signal(
            margin_rate=margin_rate,
            promo_dependency_rate=promo_dependency_rate,
            slow_mover_rate=slow_mover_rate,
        )
        if movement_signal == "slow_tail_pressure":
            recommended_action = "trim the tail, rebalance facings, and reduce reorder exposure"
        elif movement_signal == "promo_led":
            recommended_action = "review pricing architecture and reduce dependence on discounting"
        elif movement_signal == "healthy_core":
            recommended_action = "protect availability and use this category as a growth anchor"
        else:
            recommended_action = "review mix, price, and SKU role before the next reset"
        categories.append(
            {
                "category": category,
                "sku_count": sku_count,
                "order_count": order_count,
                "units": round(float(item["quantity"]), 2),
                "revenue": revenue,
                "gross_profit": round(revenue - cost, 2),
                "gross_margin_rate": margin_rate,
                "discount_rate": round(
                    _safe_rate(
                        promo_by_category[category]["discount_value"],
                        promo_by_category[category]["gross_revenue"],
                    ),
                    4,
                ),
                "promo_dependency_rate": promo_dependency_rate,
                "return_rate": _safe_rate(len(item["returned_orders"]), order_count),
                "delayed_order_rate": _safe_rate(
                    len(item["delayed_orders"]) + len(item["open_breach_orders"]),
                    order_count,
                ),
                "hero_sku_count": hero_counts[category],
                "slow_mover_sku_count": slow_counts[category],
                "movement_signal": movement_signal,
                "recommended_action": recommended_action,
            }
        )
    categories.sort(key=lambda item: (item["revenue"], item["gross_profit"]), reverse=True)
    summary = {
        "category_count": len(categories),
        "promo_led_category_count": sum(
            1 for item in categories if item["movement_signal"] == "promo_led"
        ),
        "slow_tail_category_count": sum(
            1 for item in categories if item["movement_signal"] == "slow_tail_pressure"
        ),
        "healthy_core_category_count": sum(
            1 for item in categories if item["movement_signal"] == "healthy_core"
        ),
        "top_category": categories[0]["category"] if categories else "unknown",
    }
    return {
        "report_name": "category_and_merchandising_review",
        "summary": summary,
        "categories": categories,
    }


def _build_sku_deep_dives(
    *,
    sku_rollups: dict[str, dict[str, Any]],
    supporting: dict[str, Any],
    reference_date: date,
) -> dict[str, Any]:
    profitability_by_sku = {
        to_text(item.get("sku")): item for item in supporting["profitability"].get("skus", [])
    }
    assortment_by_sku = {
        to_text(item.get("sku")): item for item in supporting["assortment"].get("skus", [])
    }
    aging_by_sku = {
        to_text(item.get("sku")): item for item in supporting["inventory_aging"].get("skus", [])
    }
    seasonality_by_sku = {
        to_text(item.get("sku")): item for item in supporting["seasonality"].get("skus", [])
    }

    details: dict[str, Any] = {}
    for sku, item in sku_rollups.items():
        revenue = round(float(item["revenue"]), 2)
        cost = round(float(item["cost"]), 2)
        order_count = len(item["orders"])
        customer_count = len(item["customers"])
        gross_profit = round(revenue - cost, 2)
        margin_rate = _margin_rate(revenue, cost)
        promo_dependency_rate = _safe_rate(len(item["promo_orders"]), order_count)
        return_rate = _safe_rate(len(item["returned_orders"]), order_count)
        delay_rate = _safe_rate(len(item["delayed_orders"]), order_count)
        open_breach_rate = _safe_rate(len(item["open_breach_orders"]), order_count)
        inventory_item = aging_by_sku.get(sku, {})
        days_since_last_sale = float(inventory_item.get("days_since_last_sale") or 0.0)
        days_of_cover = inventory_item.get("days_of_cover")
        if not isinstance(days_of_cover, int | float):
            days_of_cover = None
        priority_score = _sku_priority_score(
            margin_rate=margin_rate,
            days_since_last_sale=days_since_last_sale,
            return_rate=return_rate,
            open_breach_rate=open_breach_rate,
            delay_rate=delay_rate,
            promo_dependency_rate=promo_dependency_rate,
            days_of_cover=days_of_cover,
        )
        priority = _priority_label(priority_score)
        risk_flags = []
        if margin_rate < 0.15:
            risk_flags.append("thin_margin")
        if return_rate >= 0.2:
            risk_flags.append("high_return_exposure")
        if open_breach_rate > 0:
            risk_flags.append("open_fulfillment_breach")
        if delay_rate >= 0.2:
            risk_flags.append("late_delivery_history")
        if days_since_last_sale >= 45:
            risk_flags.append("stale_velocity")
        if promo_dependency_rate >= 0.5:
            risk_flags.append("promo_dependency")

        actions = []
        if "thin_margin" in risk_flags:
            actions.append("review price floor, supplier cost, and channel role")
        if "stale_velocity" in risk_flags:
            actions.append("pause reorder and plan markdown, bundle, or liquidation path")
        if "open_fulfillment_breach" in risk_flags or "late_delivery_history" in risk_flags:
            actions.append("work carrier and queue discipline before the next demand peak")
        if "high_return_exposure" in risk_flags:
            actions.append("review product content, sizing, and promotion targeting")
        if not actions:
            actions.append("keep standard replenishment and weekly monitoring cadence")

        details[sku] = {
            "report_name": "sku_deep_dive_report",
            "sku": sku,
            "category": to_text(item.get("category")) or "uncategorized",
            "priority": priority,
            "priority_score": priority_score,
            "commercial_metrics": {
                "order_count": order_count,
                "customer_count": customer_count,
                "units": round(float(item["quantity"]), 2),
                "revenue": revenue,
                "gross_profit": gross_profit,
                "gross_margin_rate": margin_rate,
                "average_unit_price": round(revenue / float(item["quantity"]), 2)
                if float(item["quantity"])
                else 0.0,
            },
            "inventory_metrics": {
                "on_hand_units": round(float(item.get("on_hand_units") or 0.0), 2),
                "days_since_last_sale": days_since_last_sale,
                "days_of_cover": days_of_cover,
                "movement_class": to_text(assortment_by_sku.get(sku, {}).get("movement_class")),
                "seasonality_band": to_text(
                    seasonality_by_sku.get(sku, {}).get("seasonality_band")
                ),
            },
            "operational_metrics": {
                "delay_rate": delay_rate,
                "open_breach_rate": open_breach_rate,
                "return_rate": return_rate,
                "promo_dependency_rate": promo_dependency_rate,
                "store_count": len(item["stores"]),
                "region_count": len(item["regions"]),
            },
            "risk_flags": risk_flags,
            "recommended_actions": actions,
            "supporting_signals": {
                "profitability": profitability_by_sku.get(sku, {}),
                "assortment": assortment_by_sku.get(sku, {}),
                "inventory_aging": inventory_item,
                "seasonality": seasonality_by_sku.get(sku, {}),
            },
        }
    return details


def build_business_review_artifact(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_business_review_reporting.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    rollups = _build_base_rollups(csv_path)
    supporting = _build_supporting_artifacts(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    overall = rollups["overall"]
    reference_date = rollups["reference_date"]
    executive_review = _build_executive_review(
        overall=overall,
        supporting=supporting,
        sku_rollups=rollups["skus"],
        reference_date=reference_date,
    )
    performance_by_store = _build_performance_pack(
        rollups=rollups["stores"],
        grouping_dimension="store_code",
    )
    performance_by_region = _build_performance_pack(
        rollups=rollups["regions"],
        grouping_dimension="region",
    )
    category_review = _build_category_review(
        category_rollups=rollups["categories"],
        assortment=supporting["assortment"],
        promotion=supporting["promotion"],
    )
    sku_deep_dives = _build_sku_deep_dives(
        sku_rollups=rollups["skus"],
        supporting=supporting,
        reference_date=reference_date,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": BUSINESS_REVIEW_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_index": [
            {
                "report_name": "executive_business_review",
                "endpoint": "/api/v1/business-reports/executive-review",
            },
            {
                "report_name": "store_performance_pack",
                "endpoint": "/api/v1/business-reports/store-performance?group_by=store",
            },
            {
                "report_name": "region_performance_pack",
                "endpoint": "/api/v1/business-reports/store-performance?group_by=region",
            },
            {
                "report_name": "category_and_merchandising_review",
                "endpoint": "/api/v1/business-reports/category-merchandising",
            },
            {
                "report_name": "sku_deep_dive_report",
                "endpoint": "/api/v1/business-reports/skus/{sku}/deep-dive",
            },
            *WORKING_CAPITAL_REPORT_INDEX,
            *COMMERCIAL_REPORT_INDEX,
            *GOVERNANCE_REPORT_INDEX,
            *DECISION_INTELLIGENCE_REPORT_INDEX,
            *PORTFOLIO_REPORT_INDEX,
            *EXECUTIVE_SCORECARD_REPORT_INDEX,
        ],
        "executive_review": executive_review,
        "performance_by_store": performance_by_store,
        "performance_by_region": performance_by_region,
        "category_review": category_review,
        "sku_deep_dives": sku_deep_dives,
    }
    return write_json(artifact_path, payload)


def get_business_report_catalog(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_business_review_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    report_index = list(payload.get("report_index", []))
    existing_endpoints = {
        to_text(item.get("endpoint")) for item in report_index if isinstance(item, dict)
    }
    for item in [
        *WORKING_CAPITAL_REPORT_INDEX,
        *COMMERCIAL_REPORT_INDEX,
        *GOVERNANCE_REPORT_INDEX,
        *DECISION_INTELLIGENCE_REPORT_INDEX,
        *PORTFOLIO_REPORT_INDEX,
        *EXECUTIVE_SCORECARD_REPORT_INDEX,
    ]:
        if item["endpoint"] not in existing_endpoints:
            report_index.append(item)
    return {
        "upload_id": payload["upload_id"],
        "generated_at": payload["generated_at"],
        "model_version": payload["model_version"],
        "artifact_path": payload["artifact_path"],
        "report_index": report_index,
    }


def get_executive_business_review(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_business_review_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    response = dict(payload["executive_review"])
    response.update(
        {
            "upload_id": payload["upload_id"],
            "generated_at": payload["generated_at"],
            "model_version": payload["model_version"],
            "artifact_path": payload["artifact_path"],
        }
    )
    return response


def get_store_performance_pack(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    group_by: str = "store",
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_business_review_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    if group_by == "region":
        report = dict(payload["performance_by_region"])
    else:
        report = dict(payload["performance_by_store"])
    report["rows"] = list(report.get("rows", []))[:limit]
    report.update(
        {
            "upload_id": payload["upload_id"],
            "generated_at": payload["generated_at"],
            "model_version": payload["model_version"],
            "artifact_path": payload["artifact_path"],
        }
    )
    return report


def get_category_merchandising_review(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    payload = build_business_review_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    report = dict(payload["category_review"])
    report["categories"] = list(report.get("categories", []))[:limit]
    report.update(
        {
            "upload_id": payload["upload_id"],
            "generated_at": payload["generated_at"],
            "model_version": payload["model_version"],
            "artifact_path": payload["artifact_path"],
        }
    )
    return report


def get_sku_deep_dive_report(
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = build_business_review_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    target = sku.strip().lower()
    for candidate_sku, item in payload["sku_deep_dives"].items():
        if candidate_sku.lower() == target:
            response = dict(item)
            response.update(
                {
                    "upload_id": payload["upload_id"],
                    "generated_at": payload["generated_at"],
                    "model_version": payload["model_version"],
                    "artifact_path": payload["artifact_path"],
                }
            )
            return response
    raise FileNotFoundError(f"Business review reporting does not contain sku={sku}.")
