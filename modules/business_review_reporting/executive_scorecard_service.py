# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         executive_scorecard_service.py
# Path:         modules/business_review_reporting/executive_scorecard_service.py
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
#   - Key APIs: list_executive_scorecard_reports, get_operating_executive_scorecard, get_internal_benchmarking_report, get_markdown_clearance_optimization_report, get_demand_supply_risk_matrix_report, get_customer_journey_friction_report, ...
#   - Dependencies: __future__, collections, pathlib, statistics, typing, modules.abc_xyz_intelligence.service, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from modules.abc_xyz_intelligence.service import build_abc_xyz_artifact
from modules.assortment_intelligence.service import build_assortment_artifact
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
from modules.customer_churn_intelligence.service import build_customer_churn_artifact
from modules.customer_cohort_intelligence.service import build_cohort_artifact
from modules.fulfillment_sla_intelligence.service import build_fulfillment_sla_artifact
from modules.payment_reconciliation.service import build_payment_reconciliation_artifact
from modules.promotion_pricing_intelligence.service import build_promotion_pricing_artifact
from modules.supplier_procurement_intelligence.service import build_supplier_procurement_artifact

from .portfolio_reporting_service import (
    _abc_lookup,
    _customer_lookup,
    _forecast_lookup,
    _inventory_lookup,
    _load_portfolio_dependencies,
    _profitability_lookup,
    _reorder_lookup,
    _returns_lookup,
    _stockout_lookup,
)

EXECUTIVE_SCORECARD_REPORTING_VERSION = "executive-scorecard-reporting-v1"
EXECUTIVE_SCORECARD_REPORT_INDEX = [
    {
        "report_name": "operating_executive_scorecard_report",
        "endpoint": "/api/v1/business-reports/operating-executive-scorecard",
    },
    {
        "report_name": "internal_benchmarking_report",
        "endpoint": "/api/v1/business-reports/internal-benchmarking",
    },
    {
        "report_name": "markdown_clearance_optimization_report",
        "endpoint": "/api/v1/business-reports/markdown-clearance-optimization",
    },
    {
        "report_name": "demand_supply_risk_matrix_report",
        "endpoint": "/api/v1/business-reports/demand-supply-risk-matrix",
    },
    {
        "report_name": "customer_journey_friction_report",
        "endpoint": "/api/v1/business-reports/customer-journey-friction",
    },
    {
        "report_name": "cash_conversion_risk_report",
        "endpoint": "/api/v1/business-reports/cash-conversion-risk",
    },
]


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _cache_path(artifact_dir: Path, upload_id: str, report_slug: str) -> Path:
    return artifact_dir / f"{upload_id}_{report_slug}.json"


def _read_cached(artifact_path: Path, refresh: bool) -> dict[str, Any] | None:
    if refresh:
        return None
    return read_json_or_none(artifact_path)


def _executive_scorecard_dependency_dirs(artifact_dir: Path) -> dict[str, Path]:
    dependency_dir = artifact_dir / "dependencies_executive_scorecards"
    return {
        "portfolio_reporting": dependency_dir / "portfolio_reporting_base",
        "abc_xyz": dependency_dir / "abc_xyz",
        "assortment": dependency_dir / "assortment",
        "churn": dependency_dir / "customer_churn",
        "cohort": dependency_dir / "customer_cohort",
        "fulfillment": dependency_dir / "fulfillment_sla",
        "payment": dependency_dir / "payment_reconciliation",
        "promotion": dependency_dir / "promotion_pricing",
        "supplier": dependency_dir / "supplier_procurement",
    }


def _load_executive_scorecard_dependencies(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool,
) -> dict[str, Any]:
    dirs = _executive_scorecard_dependency_dirs(artifact_dir)
    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["portfolio_reporting"],
        refresh=refresh,
    )
    dependencies.update(
        {
            "abc_xyz": build_abc_xyz_artifact(upload_id, uploads_dir, dirs["abc_xyz"], refresh),
            "assortment": build_assortment_artifact(
                upload_id, uploads_dir, dirs["assortment"], refresh
            ),
            "churn": build_customer_churn_artifact(upload_id, uploads_dir, dirs["churn"], refresh),
            "cohort": build_cohort_artifact(upload_id, uploads_dir, dirs["cohort"], refresh),
            "fulfillment": build_fulfillment_sla_artifact(
                upload_id, uploads_dir, dirs["fulfillment"], refresh
            ),
            "payment": build_payment_reconciliation_artifact(
                upload_id, uploads_dir, dirs["payment"], refresh
            ),
            "promotion": build_promotion_pricing_artifact(
                upload_id, uploads_dir, dirs["promotion"], refresh
            ),
            "supplier": build_supplier_procurement_artifact(
                upload_id, uploads_dir, dirs["supplier"], refresh
            ),
        }
    )
    return dependencies


def _store_category_rollups(csv_path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    store_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_ids": set(),
            "customers": set(),
            "revenue": 0.0,
            "cost": 0.0,
            "returned_orders": set(),
            "delayed_orders": set(),
        }
    )
    category_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "order_ids": set(),
            "customers": set(),
            "revenue": 0.0,
            "cost": 0.0,
            "returned_orders": set(),
            "delayed_orders": set(),
        }
    )
    for row in iter_normalized_rows(csv_path):
        order_id = canonical_value(row, "order_id") or "unknown-order"
        store_code = canonical_value(row, "store_code", "store", "store_id") or "unknown"
        category = canonical_value(row, "category", "product_category") or "uncategorized"
        customer_id = canonical_value(row, "customer_id", "buyer_id", "client_id") or "guest"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        unit_cost = to_float(
            canonical_value(row, "unit_cost", "cost_each", "cost"), default=unit_price * 0.55
        )
        revenue = quantity * unit_price
        cost = quantity * unit_cost
        shipment_status = canonical_value(row, "shipment_status", "status").lower()
        promised_date = canonical_value(row, "promised_date", "promise_date")
        actual_date = canonical_value(
            row, "actual_delivery_date", "delivered_date", "delivery_date"
        )
        returned = (
            to_float(
                canonical_value(row, "refund_amount", "return_qty", "returned_qty"), default=0.0
            )
            > 0
        )
        if canonical_value(row, "returned", "return_flag", "is_returned").lower() in {
            "1",
            "true",
            "yes",
            "y",
        }:
            returned = True
        delayed = bool(
            promised_date and actual_date and actual_date > promised_date
        ) or shipment_status in {"delayed", "late"}
        for rollup in (store_rollups[store_code], category_rollups[category]):
            rollup["order_ids"].add(order_id)
            rollup["customers"].add(customer_id)
            rollup["revenue"] += revenue
            rollup["cost"] += cost
            if returned:
                rollup["returned_orders"].add(order_id)
            if delayed:
                rollup["delayed_orders"].add(order_id)
    return {"stores": store_rollups, "categories": category_rollups}


def _benchmark_rows(rollups: dict[str, dict[str, Any]], entity_type: str) -> list[dict[str, Any]]:
    if not rollups:
        return []
    revenue_values = [float(item["revenue"]) for item in rollups.values()]
    margin_values = [
        _safe_rate(float(item["revenue"]) - float(item["cost"]), float(item["revenue"]))
        for item in rollups.values()
    ]
    service_values = [
        1.0 - _safe_rate(len(item["delayed_orders"]), len(item["order_ids"]))
        for item in rollups.values()
    ]
    revenue_baseline = median(revenue_values) if revenue_values else 1.0
    margin_baseline = median(margin_values) if margin_values else 0.2
    service_baseline = median(service_values) if service_values else 0.9
    rows: list[dict[str, Any]] = []
    for entity_id, item in rollups.items():
        revenue = round(float(item["revenue"]), 2)
        gross_margin_rate = _safe_rate(
            float(item["revenue"]) - float(item["cost"]), float(item["revenue"])
        )
        service_level = round(
            1.0 - _safe_rate(len(item["delayed_orders"]), len(item["order_ids"])), 4
        )
        return_rate = _safe_rate(len(item["returned_orders"]), len(item["order_ids"]))
        revenue_index = round(revenue / revenue_baseline, 2) if revenue_baseline else 0.0
        margin_index = round(gross_margin_rate / margin_baseline, 2) if margin_baseline else 0.0
        service_index = round(service_level / service_baseline, 2) if service_baseline else 0.0
        composite_score = round(
            (revenue_index * 0.4)
            + (margin_index * 0.3)
            + (service_index * 0.2)
            + ((1 - return_rate) * 0.1),
            2,
        )
        improvement_focus = "protect service"
        if gross_margin_rate < margin_baseline:
            improvement_focus = "rebuild margin"
        elif return_rate > 0.12:
            improvement_focus = "reduce returns"
        elif service_level < service_baseline:
            improvement_focus = "recover SLA discipline"
        rows.append(
            {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "revenue": revenue,
                "gross_margin_rate": round(gross_margin_rate, 4),
                "service_level": service_level,
                "return_rate": round(return_rate, 4),
                "revenue_index": revenue_index,
                "margin_index": margin_index,
                "service_index": service_index,
                "composite_score": composite_score,
                "improvement_focus": improvement_focus,
            }
        )
    rows.sort(key=lambda item: item["composite_score"], reverse=True)
    total = len(rows)
    for idx, row in enumerate(rows):
        percentile = idx / max(total, 1)
        quartile = "Q1"
        if percentile >= 0.75:
            quartile = "Q4"
        elif percentile >= 0.5:
            quartile = "Q3"
        elif percentile >= 0.25:
            quartile = "Q2"
        row["quartile"] = quartile
    return rows


def _sku_supplier_lookup(csv_path: Path) -> dict[str, dict[str, str]]:
    mapping: dict[str, Counter[str]] = defaultdict(Counter)
    name_map: dict[str, Counter[str]] = defaultdict(Counter)
    for row in iter_normalized_rows(csv_path):
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        supplier_id = canonical_value(row, "supplier_id", "vendor_id") or "unknown"
        supplier_name = canonical_value(row, "supplier_name", "vendor_name") or supplier_id
        mapping[sku][supplier_id] += 1
        name_map[sku][supplier_name] += 1
    return {
        sku: {
            "supplier_id": counts.most_common(1)[0][0],
            "supplier_name": name_map[sku].most_common(1)[0][0],
        }
        for sku, counts in mapping.items()
        if counts
    }


def _supplier_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("supplier_id")): item
        for item in artifact.get("suppliers", [])
        if isinstance(item, dict) and to_text(item.get("supplier_id"))
    }


def _seasonality_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in artifact.get("skus", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _promotion_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, float | str]] = defaultdict(
        lambda: {
            "discount_rate": 0.0,
            "gross_revenue": 0.0,
            "rows": 0.0,
            "category": "uncategorized",
        }
    )
    for item in artifact.get("skus", []):
        if not isinstance(item, dict):
            continue
        sku = to_text(item.get("sku"))
        if not sku:
            continue
        current = grouped[sku]
        gross = to_float(item.get("gross_revenue"))
        current["discount_rate"] = float(current["discount_rate"]) + (
            to_float(item.get("discount_rate")) * gross
        )
        current["gross_revenue"] = float(current["gross_revenue"]) + gross
        current["rows"] = float(current["rows"]) + 1.0
        current["category"] = to_text(item.get("category")) or str(current["category"])
    return {
        sku: {
            "discount_rate": round(
                float(values["discount_rate"]) / float(values["gross_revenue"]),
                4,
            )
            if float(values["gross_revenue"])
            else 0.0,
            "category": str(values["category"]),
        }
        for sku, values in grouped.items()
    }


def _customer_issue_rollup(csv_path: Path) -> dict[str, dict[str, Any]]:
    customer_rollup: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "orders": set(),
            "revenue": 0.0,
            "payment_issue_count": 0,
            "fulfillment_issue_count": 0,
            "return_issue_count": 0,
        }
    )
    payment_status_by_order: dict[str, str] = {}
    delayed_by_order: dict[str, bool] = {}
    return_by_order: dict[str, bool] = {}
    customer_by_order: dict[str, str] = {}
    revenue_by_order: dict[str, float] = defaultdict(float)
    for row in iter_normalized_rows(csv_path):
        order_id = canonical_value(row, "order_id") or "unknown-order"
        customer_id = canonical_value(row, "customer_id", "buyer_id", "client_id") or "guest"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=1.0), 0.0)
        unit_price = to_float(
            canonical_value(row, "unit_price", "price", "price_each"), default=0.0
        )
        revenue_by_order[order_id] += quantity * unit_price
        customer_by_order[order_id] = customer_id
        paid_amount = to_float(
            canonical_value(row, "paid_amount", "payment_amount"), default=quantity * unit_price
        )
        refund_amount = to_float(canonical_value(row, "refund_amount"), default=0.0)
        total_amount = to_float(
            canonical_value(row, "total_amount", "order_total"), default=quantity * unit_price
        )
        payment_issue = (
            paid_amount <= 0 or abs((paid_amount - refund_amount) - total_amount) >= 0.01
        )
        payment_status_by_order[order_id] = payment_issue
        shipment_status = canonical_value(row, "shipment_status", "status").lower()
        promised_date = canonical_value(row, "promised_date", "promise_date")
        actual_date = canonical_value(
            row, "actual_delivery_date", "delivered_date", "delivery_date"
        )
        delayed = bool(
            promised_date and actual_date and actual_date > promised_date
        ) or shipment_status in {"delayed", "late"}
        delayed_by_order[order_id] = delayed_by_order.get(order_id, False) or delayed
        returned = refund_amount > 0 or canonical_value(
            row, "returned", "return_flag", "is_returned"
        ).lower() in {
            "1",
            "true",
            "yes",
            "y",
        }
        return_by_order[order_id] = return_by_order.get(order_id, False) or returned
    for order_id, customer_id in customer_by_order.items():
        current = customer_rollup[customer_id]
        current["orders"].add(order_id)
        current["revenue"] += revenue_by_order[order_id]
        current["payment_issue_count"] += 1 if payment_status_by_order.get(order_id) else 0
        current["fulfillment_issue_count"] += 1 if delayed_by_order.get(order_id) else 0
        current["return_issue_count"] += 1 if return_by_order.get(order_id) else 0
    return customer_rollup


def list_executive_scorecard_reports() -> list[dict[str, str]]:
    return list(EXECUTIVE_SCORECARD_REPORT_INDEX)


def get_operating_executive_scorecard(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = _cache_path(artifact_dir, upload_id, "operating_executive_scorecard")
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        return cached
    deps = _load_executive_scorecard_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    profitability_summary = deps["profitability"]["summary"]
    promotion_summary = deps["promotion"]["summary"]
    fulfillment_summary = deps["fulfillment"]["summary"]
    inventory_summary = deps["inventory"]["summary"]
    stockout_summary = deps["stockout"]["summary"]
    payment_summary = deps["payment"]["summary"]
    churn_summary = deps["churn"]["summary"]
    cohort_summary = deps["cohort"]["summary"]
    returns_rows = deps["returns"].get("scores", [])
    total_return_cost = round(
        sum(to_float(item.get("expected_return_cost")) for item in returns_rows), 2
    )

    pillars = [
        {
            "pillar_name": "commercial",
            "score": _clamp_score(
                (profitability_summary.get("gross_margin_rate", 0.0) / 0.4) * 70
                + (1 - promotion_summary.get("average_discount_rate", 0.0)) * 30
            ),
            "target_score": 85.0,
            "leading_metric_name": "gross_margin_rate",
            "leading_metric_value": round(
                to_float(profitability_summary.get("gross_margin_rate")), 4
            ),
            "watchout": "discount leakage is suppressing realized margin"
            if to_float(promotion_summary.get("average_discount_rate")) > 0.18
            else "commercial margin is broadly stable",
            "recommended_action": "tighten discount guardrails on low-margin SKUs",
        },
        {
            "pillar_name": "service",
            "score": _clamp_score(
                to_float(fulfillment_summary.get("on_time_rate")) * 100
                - to_float(fulfillment_summary.get("average_delay_days")) * 2
            ),
            "target_score": 90.0,
            "leading_metric_name": "on_time_rate",
            "leading_metric_value": round(to_float(fulfillment_summary.get("on_time_rate")), 4),
            "watchout": "open breach risk is still elevated"
            if to_float(fulfillment_summary.get("open_breach_risk_count")) > 0
            else "service flow is under control",
            "recommended_action": "review carrier escalation queue and breach-risk orders",
        },
        {
            "pillar_name": "inventory",
            "score": _clamp_score(
                100
                - (to_float(stockout_summary.get("high_risk_sku_count")) * 8)
                - (to_float(inventory_summary.get("critical_aging_count")) * 6)
            ),
            "target_score": 82.0,
            "leading_metric_name": "high_risk_sku_count",
            "leading_metric_value": round(to_float(stockout_summary.get("high_risk_sku_count")), 2),
            "watchout": "capital is split between stockout risk and stale inventory"
            if to_float(inventory_summary.get("critical_aging_count")) > 0
            else "inventory posture is reasonably balanced",
            "recommended_action": "rebalance replenishment and markdowns around highest-risk SKUs",
        },
        {
            "pillar_name": "customer",
            "score": _clamp_score(
                to_float(cohort_summary.get("repeat_customer_rate")) * 55
                + (
                    1
                    - _safe_rate(
                        to_float(churn_summary.get("high_risk_customer_count")),
                        to_float(churn_summary.get("customer_count")),
                    )
                )
                * 45
            ),
            "target_score": 80.0,
            "leading_metric_name": "repeat_customer_rate",
            "leading_metric_value": round(to_float(cohort_summary.get("repeat_customer_rate")), 4),
            "watchout": "high-risk churn pool needs recovery plays"
            if to_float(churn_summary.get("high_risk_customer_count")) > 0
            else "retention health is stable",
            "recommended_action": "trigger targeted save offers for high-risk customers",
        },
        {
            "pillar_name": "cash",
            "score": _clamp_score(
                (
                    1
                    - _safe_rate(
                        to_float(payment_summary.get("missing_payment_orders"))
                        + to_float(payment_summary.get("refunded_orders")),
                        to_float(payment_summary.get("order_count")),
                    )
                )
                * 70
                + (
                    1
                    - _safe_rate(total_return_cost, to_float(profitability_summary.get("revenue")))
                )
                * 30
            ),
            "target_score": 88.0,
            "leading_metric_name": "cash_exception_rate",
            "leading_metric_value": round(
                _safe_rate(
                    to_float(payment_summary.get("missing_payment_orders"))
                    + to_float(payment_summary.get("refunded_orders")),
                    to_float(payment_summary.get("order_count")),
                ),
                4,
            ),
            "watchout": "refunds and payment exceptions are slowing cash conversion"
            if (
                to_float(payment_summary.get("refunded_orders"))
                + to_float(payment_summary.get("missing_payment_orders"))
            )
            > 0
            else "cash capture is clean",
            "recommended_action": "resolve unmatched payments and reduce avoidable returns",
        },
    ]
    for pillar in pillars:
        pillar["gap_to_target"] = round(float(pillar["target_score"]) - float(pillar["score"]), 1)
    overall_score = (
        round(sum(float(item["score"]) for item in pillars) / len(pillars), 1) if pillars else 0.0
    )
    ranked = sorted(pillars, key=lambda item: float(item["score"]), reverse=True)
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": EXECUTIVE_SCORECARD_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "operating_executive_scorecard_report",
        "summary": {
            "pillar_count": len(pillars),
            "overall_score": overall_score,
            "top_pillar": ranked[0]["pillar_name"] if ranked else "",
            "weakest_pillar": ranked[-1]["pillar_name"] if ranked else "",
            "pillars_below_target": sum(
                1 for item in pillars if float(item["score"]) < float(item["target_score"])
            ),
            "critical_alert_count": sum(1 for item in pillars if float(item["score"]) < 70.0),
        },
        "pillars": pillars,
    }
    return write_json(artifact_path, payload)


def get_internal_benchmarking_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 10,
) -> dict[str, Any]:
    artifact_path = _cache_path(artifact_dir, upload_id, "internal_benchmarking")
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["store_benchmarks"] = list(payload.get("store_benchmarks", []))[:limit]
        payload["category_benchmarks"] = list(payload.get("category_benchmarks", []))[:limit]
        return payload
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    rollups = _store_category_rollups(csv_path)
    store_rows = _benchmark_rows(rollups["stores"], "store")
    category_rows = _benchmark_rows(rollups["categories"], "category")
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": EXECUTIVE_SCORECARD_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "internal_benchmarking_report",
        "summary": {
            "store_count": len(store_rows),
            "category_count": len(category_rows),
            "top_store": store_rows[0]["entity_id"] if store_rows else "",
            "lowest_store": store_rows[-1]["entity_id"] if store_rows else "",
            "top_category": category_rows[0]["entity_id"] if category_rows else "",
            "widest_gap_points": round(
                (store_rows[0]["composite_score"] - store_rows[-1]["composite_score"]), 2
            )
            if len(store_rows) >= 2
            else 0.0,
        },
        "store_benchmarks": store_rows,
        "category_benchmarks": category_rows,
    }
    write_json(artifact_path, payload)
    payload["store_benchmarks"] = list(store_rows)[:limit]
    payload["category_benchmarks"] = list(category_rows)[:limit]
    return payload


def get_markdown_clearance_optimization_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 12,
) -> dict[str, Any]:
    artifact_path = _cache_path(artifact_dir, upload_id, "markdown_clearance_optimization")
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["candidates"] = list(payload.get("candidates", []))[:limit]
        return payload
    deps = _load_executive_scorecard_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    abc_lookup = _abc_lookup(deps["abc_xyz"])
    profitability_lookup = _profitability_lookup(deps["profitability"])
    inventory_lookup = _inventory_lookup(deps["inventory"])
    stockout_lookup = _stockout_lookup(deps["stockout"])
    seasonality_lookup = _seasonality_lookup(deps["seasonality"])
    candidates: list[dict[str, Any]] = []
    category_counter: Counter[str] = Counter()
    expected_cash_release = 0.0
    for sku, inventory_item in inventory_lookup.items():
        profitability_item = profitability_lookup.get(sku, {})
        abc_item = abc_lookup.get(sku, {})
        stockout_item = stockout_lookup.get(sku, {})
        seasonality_item = seasonality_lookup.get(sku, {})
        quantity = max(to_float(profitability_item.get("quantity")), 1.0)
        unit_cost = to_float(profitability_item.get("cost")) / quantity if quantity else 0.0
        on_hand_units = to_float(inventory_item.get("on_hand_units"))
        cash_release = round(on_hand_units * unit_cost, 2)
        stockout_probability = to_float(stockout_item.get("stockout_probability"))
        days_of_cover = to_float(inventory_item.get("days_of_cover"))
        gross_margin_rate = to_float(profitability_item.get("gross_margin_rate"))
        aging_band = to_text(inventory_item.get("aging_band")) or "active"
        combined_class = to_text(abc_item.get("combined_class")) or "CZ"
        seasonality_band = to_text(seasonality_item.get("seasonality_band")) or "steady"
        priority_score = 0.0
        if aging_band == "critical":
            priority_score += 3.0
        elif aging_band == "stale":
            priority_score += 2.2
        elif aging_band == "watch":
            priority_score += 1.0
        if days_of_cover >= 60:
            priority_score += 2.0
        elif days_of_cover >= 35:
            priority_score += 1.2
        if stockout_probability <= 0.15:
            priority_score += 1.4
        if combined_class.startswith("C"):
            priority_score += 1.0
        if seasonality_band in {"steady", "emerging"}:
            priority_score += 0.7
        if gross_margin_rate < 0.12:
            priority_score += 0.8
        if priority_score < 2.4:
            continue
        suggested_markdown_rate = 0.1
        if priority_score >= 6.0:
            suggested_markdown_rate = 0.35
        elif priority_score >= 4.5:
            suggested_markdown_rate = 0.25
        elif priority_score >= 3.5:
            suggested_markdown_rate = 0.18
        clearance_priority = "medium"
        if priority_score >= 6.0:
            clearance_priority = "critical"
        elif priority_score >= 4.2:
            clearance_priority = "high"
        category = (
            to_text(inventory_item.get("category") or profitability_item.get("category"))
            or "uncategorized"
        )
        category_counter[category] += 1
        expected_cash_release += cash_release
        candidates.append(
            {
                "sku": sku,
                "category": category,
                "aging_band": aging_band,
                "combined_class": combined_class,
                "seasonality_band": seasonality_band,
                "days_of_cover": round(days_of_cover, 2),
                "gross_margin_rate": round(gross_margin_rate, 4),
                "stockout_probability": round(stockout_probability, 4),
                "suggested_markdown_rate": round(suggested_markdown_rate, 4),
                "expected_cash_release": cash_release,
                "clearance_priority": clearance_priority,
                "rationale": "aged inventory with low stockout pressure and limited portfolio importance",
            }
        )
    candidates.sort(
        key=lambda item: (
            {"critical": 3, "high": 2, "medium": 1}.get(item["clearance_priority"], 0),
            item["expected_cash_release"],
        ),
        reverse=True,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": EXECUTIVE_SCORECARD_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "markdown_clearance_optimization_report",
        "summary": {
            "sku_count": len(inventory_lookup),
            "clearance_candidate_count": len(candidates),
            "critical_candidate_count": sum(
                1 for item in candidates if item["clearance_priority"] == "critical"
            ),
            "expected_cash_release": round(expected_cash_release, 2),
            "top_clearance_category": category_counter.most_common(1)[0][0]
            if category_counter
            else "",
        },
        "candidates": candidates,
    }
    write_json(artifact_path, payload)
    payload["candidates"] = list(candidates)[:limit]
    return payload


def get_demand_supply_risk_matrix_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 15,
) -> dict[str, Any]:
    artifact_path = _cache_path(artifact_dir, upload_id, "demand_supply_risk_matrix")
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["focus_skus"] = list(payload.get("focus_skus", []))[:limit]
        return payload
    deps = _load_executive_scorecard_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    supplier_per_sku = _sku_supplier_lookup(csv_path)
    supplier_lookup = _supplier_lookup(deps["supplier"])
    seasonality_lookup = _seasonality_lookup(deps["seasonality"])
    stockout_lookup = _stockout_lookup(deps["stockout"])
    reorder_lookup = _reorder_lookup(deps["reorder"])
    forecast_lookup = _forecast_lookup(deps["forecast"])
    inventory_lookup = _inventory_lookup(deps["inventory"])
    abc_lookup = _abc_lookup(deps["abc_xyz"])
    risk_zone_rows: list[dict[str, Any]] = []
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "sku_count": 0,
            "forecast_share": 0.0,
            "stockout_sum": 0.0,
            "urgency_sum": 0.0,
        }
    )
    focus_rows: list[dict[str, Any]] = []
    all_forecast = sum(forecast_lookup.values()) or 1.0
    for sku, stockout_item in stockout_lookup.items():
        reorder_item = reorder_lookup.get(sku, {})
        forecast_30d = round(forecast_lookup.get(sku, 0.0), 2)
        supplier_info = supplier_per_sku.get(sku, {})
        supplier_item = supplier_lookup.get(to_text(supplier_info.get("supplier_id")), {})
        supplier_risk_band = to_text(supplier_item.get("risk_band")) or "medium"
        supplier_name = (
            to_text(supplier_info.get("supplier_name"))
            or to_text(supplier_item.get("supplier_name"))
            or "unknown"
        )
        seasonality_band = (
            to_text(seasonality_lookup.get(sku, {}).get("seasonality_band")) or "steady"
        )
        stockout_probability = to_float(stockout_item.get("stockout_probability"))
        inventory_item = inventory_lookup.get(sku, {})
        days_of_cover = to_float(
            inventory_item.get("days_of_cover") or stockout_item.get("days_of_cover")
        )
        reorder_urgency_score = to_float(reorder_item.get("reorder_urgency_score"))
        category = (
            to_text(stockout_item.get("category") or abc_lookup.get(sku, {}).get("category"))
            or "uncategorized"
        )
        forecast_share = forecast_30d / all_forecast if all_forecast else 0.0
        risk_zone = "balanced"
        recommended_action = "keep normal review rhythm"
        if stockout_probability >= 0.55 and supplier_risk_band == "high":
            risk_zone = "red_zone"
            recommended_action = "expedite supply and protect service level immediately"
        elif (
            forecast_share >= 0.18 or stockout_probability >= 0.28 or reorder_urgency_score >= 0.55
        ):
            risk_zone = "demand_spike"
            recommended_action = "pull forward replenishment and monitor daily"
        elif days_of_cover >= 120 and stockout_probability <= 0.2:
            risk_zone = "inventory_heavy"
            recommended_action = "slow buys and evaluate targeted markdowns"
        grouped_row = grouped[risk_zone]
        grouped_row["sku_count"] += 1
        grouped_row["forecast_share"] += forecast_share
        grouped_row["stockout_sum"] += stockout_probability
        grouped_row["urgency_sum"] += reorder_urgency_score
        focus_rows.append(
            {
                "sku": sku,
                "category": category,
                "supplier_name": supplier_name,
                "supplier_risk_band": supplier_risk_band,
                "seasonality_band": seasonality_band,
                "forecast_30d": forecast_30d,
                "days_of_cover": round(days_of_cover, 2),
                "stockout_probability": round(stockout_probability, 4),
                "reorder_urgency_score": round(reorder_urgency_score, 4),
                "risk_zone": risk_zone,
                "recommended_action": recommended_action,
            }
        )
    playbook = {
        "red_zone": "cross-functional shortage response with supplier escalation",
        "demand_spike": "tight replenishment cadence and promotional discipline",
        "inventory_heavy": "trim inbound inventory and clear excess stock",
        "balanced": "maintain standard operating rhythm",
    }
    for zone, values in grouped.items():
        risk_zone_rows.append(
            {
                "risk_zone": zone,
                "sku_count": int(values["sku_count"]),
                "forecast_share": round(float(values["forecast_share"]), 4),
                "average_stockout_probability": round(
                    float(values["stockout_sum"]) / float(values["sku_count"]), 4
                )
                if values["sku_count"]
                else 0.0,
                "average_reorder_urgency": round(
                    float(values["urgency_sum"]) / float(values["sku_count"]), 4
                )
                if values["sku_count"]
                else 0.0,
                "response_play": playbook[zone],
            }
        )
    risk_zone_rows.sort(
        key=lambda item: {
            "red_zone": 4,
            "demand_spike": 3,
            "inventory_heavy": 2,
            "balanced": 1,
        }.get(item["risk_zone"], 0),
        reverse=True,
    )
    focus_rows.sort(
        key=lambda item: (
            {"red_zone": 4, "demand_spike": 3, "inventory_heavy": 2, "balanced": 1}.get(
                item["risk_zone"], 0
            ),
            item["stockout_probability"],
            item["forecast_30d"],
        ),
        reverse=True,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": EXECUTIVE_SCORECARD_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "demand_supply_risk_matrix_report",
        "summary": {
            "sku_count": len(focus_rows),
            "risk_zone_count": len(risk_zone_rows),
            "red_zone_count": sum(1 for item in focus_rows if item["risk_zone"] == "red_zone"),
            "inventory_heavy_count": sum(
                1 for item in focus_rows if item["risk_zone"] == "inventory_heavy"
            ),
            "balanced_count": sum(1 for item in focus_rows if item["risk_zone"] == "balanced"),
            "top_risk_sku": focus_rows[0]["sku"] if focus_rows else "",
        },
        "risk_zones": risk_zone_rows,
        "focus_skus": focus_rows,
    }
    write_json(artifact_path, payload)
    payload["focus_skus"] = list(focus_rows)[:limit]
    return payload


def get_customer_journey_friction_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 15,
) -> dict[str, Any]:
    artifact_path = _cache_path(artifact_dir, upload_id, "customer_journey_friction")
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["customers"] = list(payload.get("customers", []))[:limit]
        return payload
    deps = _load_executive_scorecard_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    issue_rollup = _customer_issue_rollup(csv_path)
    customer_lookup = _customer_lookup(deps["customer"])
    churn_lookup = {
        to_text(item.get("customer_id")): item
        for item in deps["churn"].get("customers", [])
        if isinstance(item, dict) and to_text(item.get("customer_id"))
    }
    stages_rollup: dict[str, dict[str, float | set[str]]] = defaultdict(
        lambda: {
            "incident_count": 0.0,
            "customer_ids": set(),
            "revenue_at_risk": 0.0,
            "friction_score_sum": 0.0,
        }
    )
    customer_rows: list[dict[str, Any]] = []
    stage_playbook = {
        "payment": "fix authorization and settlement exceptions before escalation",
        "fulfillment": "stabilize ETA and carrier recovery workflow",
        "returns": "target return prevention and post-purchase coaching",
        "retention": "run save offers and service outreach for at-risk customers",
    }
    for customer_id, issues in issue_rollup.items():
        payment_issue_count = int(issues["payment_issue_count"])
        fulfillment_issue_count = int(issues["fulfillment_issue_count"])
        return_issue_count = int(issues["return_issue_count"])
        churn_item = churn_lookup.get(customer_id, {})
        customer_item = customer_lookup.get(customer_id, {})
        churn_band = to_text(churn_item.get("risk_band")) or "low"
        revenue = round(float(issues["revenue"]), 2)
        friction_score = round(
            (payment_issue_count * 1.4)
            + (fulfillment_issue_count * 1.3)
            + (return_issue_count * 1.1)
            + ({"high": 1.6, "lost": 2.2, "medium": 0.8}.get(churn_band, 0.2)),
            2,
        )
        stage_weights = {
            "payment": payment_issue_count,
            "fulfillment": fulfillment_issue_count,
            "returns": return_issue_count,
            "retention": 1 if churn_band in {"high", "lost"} else 0,
        }
        primary_stage = max(stage_weights, key=stage_weights.get)
        revenue_at_risk = round(revenue * min(0.9, 0.08 * friction_score), 2)
        stage_row = stages_rollup[primary_stage]
        stage_row["incident_count"] = float(stage_row["incident_count"]) + 1.0
        cast_customer_ids = stage_row["customer_ids"]
        assert isinstance(cast_customer_ids, set)
        cast_customer_ids.add(customer_id)
        stage_row["revenue_at_risk"] = float(stage_row["revenue_at_risk"]) + revenue_at_risk
        stage_row["friction_score_sum"] = float(stage_row["friction_score_sum"]) + friction_score
        customer_rows.append(
            {
                "customer_id": customer_id,
                "segment": to_text(customer_item.get("segment")) or "developing",
                "churn_risk_band": churn_band,
                "friction_score": friction_score,
                "payment_issue_count": payment_issue_count,
                "fulfillment_issue_count": fulfillment_issue_count,
                "return_issue_count": return_issue_count,
                "revenue_at_risk": revenue_at_risk,
                "primary_friction_stage": primary_stage,
                "recommended_action": stage_playbook[primary_stage],
            }
        )
    stage_rows = []
    for stage_name, values in stages_rollup.items():
        customer_ids = values["customer_ids"]
        assert isinstance(customer_ids, set)
        incident_count = int(values["incident_count"])
        stage_rows.append(
            {
                "stage_name": stage_name,
                "incident_count": incident_count,
                "customer_count": len(customer_ids),
                "revenue_at_risk": round(float(values["revenue_at_risk"]), 2),
                "average_friction_score": round(
                    float(values["friction_score_sum"]) / incident_count, 2
                )
                if incident_count
                else 0.0,
                "response_play": stage_playbook[stage_name],
            }
        )
    stage_rows.sort(key=lambda item: item["revenue_at_risk"], reverse=True)
    customer_rows.sort(
        key=lambda item: (item["friction_score"], item["revenue_at_risk"]), reverse=True
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": EXECUTIVE_SCORECARD_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "customer_journey_friction_report",
        "summary": {
            "customer_count": len(customer_rows),
            "friction_customer_count": sum(
                1 for item in customer_rows if item["friction_score"] >= 1.5
            ),
            "high_friction_customer_count": sum(
                1 for item in customer_rows if item["friction_score"] >= 3.0
            ),
            "revenue_at_risk": round(
                sum(float(item["revenue_at_risk"]) for item in customer_rows), 2
            ),
            "primary_friction_stage": stage_rows[0]["stage_name"] if stage_rows else "",
        },
        "stages": stage_rows,
        "customers": customer_rows,
    }
    write_json(artifact_path, payload)
    payload["customers"] = list(customer_rows)[:limit]
    return payload


def get_cash_conversion_risk_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    artifact_path = _cache_path(artifact_dir, upload_id, "cash_conversion_risk")
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["focus_entities"] = list(payload.get("focus_entities", []))[:limit]
        return payload
    deps = _load_executive_scorecard_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    inventory_lookup = _inventory_lookup(deps["inventory"])
    profitability_lookup = _profitability_lookup(deps["profitability"])
    returns_lookup = _returns_lookup(deps["returns"])
    payment_orders = [item for item in deps["payment"].get("orders", []) if isinstance(item, dict)]
    promotion_lookup = _promotion_lookup(deps["promotion"])
    inventory_cash_lock = 0.0
    focus_entities: list[dict[str, Any]] = []
    for sku, inventory_item in inventory_lookup.items():
        if to_text(inventory_item.get("aging_band")) not in {"critical", "stale"}:
            continue
        profitability_item = profitability_lookup.get(sku, {})
        quantity = max(to_float(profitability_item.get("quantity")), 1.0)
        unit_cost = to_float(profitability_item.get("cost")) / quantity if quantity else 0.0
        exposure = round(to_float(inventory_item.get("on_hand_units")) * unit_cost, 2)
        inventory_cash_lock += exposure
        focus_entities.append(
            {
                "entity_type": "sku",
                "entity_id": sku,
                "driver_name": "inventory_cash_lock",
                "exposure_amount": exposure,
                "severity": "high"
                if to_text(inventory_item.get("aging_band")) == "critical"
                else "medium",
                "recommended_action": "clear excess inventory and trim future buys",
            }
        )
    payment_variance_exposure = round(
        sum(
            abs(to_float(item.get("variance_amount")))
            for item in payment_orders
            if to_text(item.get("reconciliation_status")) != "matched"
        ),
        2,
    )
    for item in payment_orders:
        status = to_text(item.get("reconciliation_status"))
        if status == "matched":
            continue
        focus_entities.append(
            {
                "entity_type": "order",
                "entity_id": to_text(item.get("order_id")),
                "driver_name": "payment_variance_exposure",
                "exposure_amount": round(abs(to_float(item.get("variance_amount"))), 2),
                "severity": "high" if status in {"missing_payment", "underpaid"} else "medium",
                "recommended_action": "reconcile payment and close settlement variance",
            }
        )
    returns_exposure = round(
        sum(to_float(item.get("expected_return_cost")) for item in returns_lookup.values()), 2
    )
    for sku, item in returns_lookup.items():
        if to_float(item.get("expected_return_cost")) <= 0:
            continue
        focus_entities.append(
            {
                "entity_type": "sku",
                "entity_id": sku,
                "driver_name": "returns_exposure",
                "exposure_amount": round(to_float(item.get("expected_return_cost")), 2),
                "severity": "medium"
                if to_float(item.get("average_return_probability")) < 0.35
                else "high",
                "recommended_action": "reduce avoidable returns and improve post-purchase experience",
            }
        )
    discount_leakage = round(
        sum(
            to_float(item.get("discount_rate"))
            * to_float(profitability_lookup.get(sku, {}).get("revenue"))
            for sku, item in promotion_lookup.items()
        ),
        2,
    )
    total_cash_risk = round(
        inventory_cash_lock + payment_variance_exposure + returns_exposure + discount_leakage, 2
    )
    drivers = [
        {
            "driver_name": "inventory_cash_lock",
            "exposure_amount": round(inventory_cash_lock, 2),
            "severity": "high" if inventory_cash_lock >= total_cash_risk * 0.35 else "medium",
            "mitigation": "prioritize clearance and reset inbound inventory plans",
        },
        {
            "driver_name": "payment_variance_exposure",
            "exposure_amount": payment_variance_exposure,
            "severity": "high" if payment_variance_exposure >= total_cash_risk * 0.2 else "medium",
            "mitigation": "tighten reconciliation and provider exception handling",
        },
        {
            "driver_name": "returns_exposure",
            "exposure_amount": returns_exposure,
            "severity": "high" if returns_exposure >= total_cash_risk * 0.2 else "medium",
            "mitigation": "reduce return leakage on high-cost SKUs",
        },
        {
            "driver_name": "discount_leakage",
            "exposure_amount": discount_leakage,
            "severity": "high" if discount_leakage >= total_cash_risk * 0.2 else "medium",
            "mitigation": "enforce promotion guardrails and floor margins",
        },
    ]
    for item in drivers:
        item["exposure_share"] = round(
            _safe_rate(float(item["exposure_amount"]), total_cash_risk), 4
        )
    drivers.sort(key=lambda item: item["exposure_amount"], reverse=True)
    focus_entities.sort(key=lambda item: item["exposure_amount"], reverse=True)
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": EXECUTIVE_SCORECARD_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "cash_conversion_risk_report",
        "summary": {
            "total_cash_risk": total_cash_risk,
            "inventory_cash_lock": round(inventory_cash_lock, 2),
            "payment_variance_exposure": payment_variance_exposure,
            "returns_exposure": returns_exposure,
            "discount_leakage": discount_leakage,
            "top_driver": drivers[0]["driver_name"] if drivers else "",
        },
        "drivers": drivers,
        "focus_entities": focus_entities,
    }
    write_json(artifact_path, payload)
    payload["focus_entities"] = list(focus_entities)[:limit]
    return payload
