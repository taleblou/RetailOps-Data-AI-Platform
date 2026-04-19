# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         portfolio_reporting_service.py
# Path:         modules/business_review_reporting/portfolio_reporting_service.py
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
#   - Key APIs: get_profitability_margin_waterfall_report, get_abc_xyz_inventory_policy_report, get_basket_cross_sell_opportunity_report, get_customer_churn_recovery_report, get_payment_revenue_assurance_report, get_seasonality_calendar_readiness_report, ...
#   - Dependencies: __future__, collections, pathlib, statistics, typing, modules.abc_xyz_intelligence.service, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from modules.abc_xyz_intelligence.service import build_abc_xyz_artifact
from modules.assortment_intelligence.service import build_assortment_artifact
from modules.basket_affinity_intelligence.service import build_basket_affinity_artifact
from modules.common.upload_utils import (
    read_json_or_none,
    to_float,
    to_text,
    utc_now_iso,
    write_json,
)
from modules.customer_churn_intelligence.service import build_customer_churn_artifact
from modules.customer_intelligence.service import build_customer_intelligence_artifact
from modules.forecasting.service import get_or_create_batch_forecast_artifact
from modules.inventory_aging_intelligence.service import build_inventory_aging_artifact
from modules.payment_reconciliation.service import build_payment_reconciliation_artifact
from modules.profitability_intelligence.service import build_profitability_artifact
from modules.promotion_pricing_intelligence.service import build_promotion_pricing_artifact
from modules.reorder_engine.service import get_or_create_reorder_artifact
from modules.returns_intelligence.service import get_or_create_returns_artifact
from modules.seasonality_intelligence.service import build_seasonality_artifact
from modules.stockout_intelligence.service import get_or_create_stockout_artifact

PORTFOLIO_REPORTING_VERSION = "portfolio-reporting-v1"
PORTFOLIO_REPORT_INDEX = [
    {
        "report_name": "profitability_margin_waterfall_report",
        "endpoint": "/api/v1/business-reports/profitability-margin-waterfall",
    },
    {
        "report_name": "abc_xyz_inventory_policy_report",
        "endpoint": "/api/v1/business-reports/abc-xyz-inventory-policy",
    },
    {
        "report_name": "basket_cross_sell_opportunity_report",
        "endpoint": "/api/v1/business-reports/basket-cross-sell-opportunities",
    },
    {
        "report_name": "customer_churn_recovery_report",
        "endpoint": "/api/v1/business-reports/customer-churn-recovery",
    },
    {
        "report_name": "payment_revenue_assurance_report",
        "endpoint": "/api/v1/business-reports/payment-revenue-assurance",
    },
    {
        "report_name": "seasonality_calendar_readiness_report",
        "endpoint": "/api/v1/business-reports/seasonality-calendar-readiness",
    },
    {
        "report_name": "assortment_rationalization_report",
        "endpoint": "/api/v1/business-reports/assortment-rationalization",
    },
    {
        "report_name": "customer_value_segmentation_report",
        "endpoint": "/api/v1/business-reports/customer-value-segmentation",
    },
]


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _portfolio_dependency_dirs(artifact_dir: Path) -> dict[str, Path]:
    dependency_dir = artifact_dir / "dependencies"
    return {
        "abc_xyz": dependency_dir / "abc_xyz",
        "assortment": dependency_dir / "assortment",
        "basket": dependency_dir / "basket_affinity",
        "churn": dependency_dir / "customer_churn",
        "customer": dependency_dir / "customer_intelligence",
        "forecast": dependency_dir / "forecasts",
        "inventory": dependency_dir / "inventory_aging",
        "payment": dependency_dir / "payment_reconciliation",
        "profitability": dependency_dir / "profitability",
        "promotion": dependency_dir / "promotion_pricing",
        "reorder": dependency_dir / "reorder",
        "returns": dependency_dir / "returns_risk",
        "seasonality": dependency_dir / "seasonality",
        "stockout": dependency_dir / "stockout_risk",
    }


def _load_portfolio_dependencies(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool,
) -> dict[str, Any]:
    dirs = _portfolio_dependency_dirs(artifact_dir)
    forecast = get_or_create_batch_forecast_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["forecast"],
        refresh=refresh,
    )
    stockout = get_or_create_stockout_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["stockout"],
        refresh=refresh,
    )
    reorder = get_or_create_reorder_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=dirs["forecast"],
        stockout_artifact_dir=dirs["stockout"],
        artifact_dir=dirs["reorder"],
        refresh=refresh,
    )
    return {
        "abc_xyz": build_abc_xyz_artifact(upload_id, uploads_dir, dirs["abc_xyz"], refresh),
        "assortment": build_assortment_artifact(
            upload_id, uploads_dir, dirs["assortment"], refresh
        ),
        "basket": build_basket_affinity_artifact(upload_id, uploads_dir, dirs["basket"], refresh),
        "churn": build_customer_churn_artifact(upload_id, uploads_dir, dirs["churn"], refresh),
        "customer": build_customer_intelligence_artifact(
            upload_id, uploads_dir, dirs["customer"], refresh
        ),
        "forecast": forecast,
        "inventory": build_inventory_aging_artifact(
            upload_id, uploads_dir, dirs["inventory"], refresh
        ),
        "payment": build_payment_reconciliation_artifact(
            upload_id, uploads_dir, dirs["payment"], refresh
        ),
        "profitability": build_profitability_artifact(
            upload_id, uploads_dir, dirs["profitability"], refresh
        ),
        "promotion": build_promotion_pricing_artifact(
            upload_id, uploads_dir, dirs["promotion"], refresh
        ),
        "reorder": reorder,
        "returns": get_or_create_returns_artifact(
            upload_id=upload_id,
            uploads_dir=uploads_dir,
            artifact_dir=dirs["returns"],
            refresh=refresh,
        ),
        "seasonality": build_seasonality_artifact(
            upload_id, uploads_dir, dirs["seasonality"], refresh
        ),
        "stockout": stockout,
    }


def _abc_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in artifact.get("skus", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _profitability_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in artifact.get("skus", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _inventory_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in artifact.get("skus", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _stockout_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in artifact.get("skus", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _reorder_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in artifact.get("recommendations", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _forecast_lookup(artifact: dict[str, Any]) -> dict[str, float]:
    lookup: dict[str, float] = {}
    for item in artifact.get("products", []):
        if not isinstance(item, dict):
            continue
        sku = to_text(item.get("product_id"))
        if not sku:
            continue
        horizon_30 = 0.0
        for horizon in item.get("horizons", []):
            if not isinstance(horizon, dict):
                continue
            if int(to_float(horizon.get("horizon_days"), default=0.0)) == 30:
                horizon_30 = round(to_float(horizon.get("p50") or horizon.get("point_forecast")), 2)
                break
        lookup[sku] = horizon_30
    return lookup


def _returns_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "expected_return_cost": 0.0,
            "return_probability_sum": 0.0,
            "rows": 0.0,
        }
    )
    for item in artifact.get("scores", []):
        if not isinstance(item, dict):
            continue
        sku = to_text(item.get("sku"))
        if not sku:
            continue
        current = grouped[sku]
        current["expected_return_cost"] += to_float(item.get("expected_return_cost"))
        current["return_probability_sum"] += to_float(item.get("return_probability"))
        current["rows"] += 1.0
    return {
        sku: {
            "expected_return_cost": round(values["expected_return_cost"], 2),
            "average_return_probability": round(
                values["return_probability_sum"] / values["rows"], 4
            )
            if values["rows"]
            else 0.0,
        }
        for sku, values in grouped.items()
    }


def _customer_lookup(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("customer_id")): item
        for item in artifact.get("customers", [])
        if isinstance(item, dict) and to_text(item.get("customer_id"))
    }


def _cache_path(artifact_dir: Path, upload_id: str, report_slug: str) -> Path:
    return artifact_dir / f"{upload_id}_{report_slug}.json"


def _read_cached(artifact_path: Path, refresh: bool) -> dict[str, Any] | None:
    if refresh:
        return None
    return read_json_or_none(artifact_path)


def _policy_targets(combined_class: str) -> tuple[float, str, str, str]:
    abc_class = combined_class[:1]
    xyz_class = combined_class[1:2]
    service_level_target = 0.95
    review_cadence = "weekly"
    safety_stock_posture = "balanced"
    if abc_class == "A" and xyz_class == "X":
        return (
            0.99,
            "daily",
            "protect aggressively",
            "keep high service levels and priority replenishment",
        )
    if abc_class == "A":
        return (
            0.98,
            "twice weekly",
            "above target",
            "review supplier coverage and protect availability",
        )
    if xyz_class == "Z":
        return 0.92, "weekly", "light", "use tighter buys and escalate only on true demand spikes"
    if abc_class == "C":
        return (
            0.9,
            "monthly",
            "minimal",
            "use reorder thresholds conservatively and limit working capital",
        )
    return (
        service_level_target,
        review_cadence,
        safety_stock_posture,
        "maintain standard review rhythm",
    )


def _margin_action(leakage_value: float, margin_rate: float) -> str:
    if margin_rate < 0:
        return "stop discounting, review cost floor, and gate replenishment"
    if leakage_value >= 150:
        return "review price realization and return leakage before next replenishment"
    if margin_rate < 0.2:
        return "tighten markdown discipline and review vendor terms"
    return "maintain current pricing and monitor leakage"


def _assortment_action(
    movement_class: str, combined_class: str, margin_rate: float, days_of_cover: float
) -> str:
    if movement_class == "hero" and margin_rate >= 0.25:
        return "expand distribution and protect availability"
    if movement_class in {"slow_mover", "long_tail"} and days_of_cover >= 60:
        return "rationalize assortment and reduce buys"
    if combined_class.endswith("Z"):
        return "keep with cautious buys and shorter review cycles"
    return "retain in core range and monitor performance"


def get_profitability_margin_waterfall_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 12,
) -> dict[str, Any]:
    artifact_path = _cache_path(
        artifact_dir, upload_id, "portfolio_reporting_profitability_margin_waterfall"
    )
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["category_leakage"] = list(payload.get("category_leakage", []))[:limit]
        return payload

    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    profitability = dependencies["profitability"]
    promotion = dependencies["promotion"]
    returns_by_sku = _returns_lookup(dependencies["returns"])

    category_rollup: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "revenue": 0.0,
            "gross_profit": 0.0,
            "expected_return_cost": 0.0,
            "discount_value": 0.0,
            "gross_revenue": 0.0,
        }
    )
    for item in profitability.get("skus", []):
        if not isinstance(item, dict):
            continue
        sku = to_text(item.get("sku"))
        category = to_text(item.get("category")) or "uncategorized"
        current = category_rollup[category]
        current["revenue"] += to_float(item.get("revenue"))
        current["gross_profit"] += to_float(item.get("gross_profit"))
        current["expected_return_cost"] += returns_by_sku.get(sku, {}).get(
            "expected_return_cost", 0.0
        )

    for item in promotion.get("skus", []):
        if not isinstance(item, dict):
            continue
        category = to_text(item.get("category")) or "uncategorized"
        current = category_rollup[category]
        current["discount_value"] += to_float(item.get("discount_value"))
        current["gross_revenue"] += to_float(item.get("gross_revenue"))

    category_leakage = []
    total_leakage = 0.0
    for category, values in category_rollup.items():
        revenue = round(values["revenue"], 2)
        gross_profit = round(values["gross_profit"], 2)
        gross_margin_rate = _safe_rate(gross_profit, revenue)
        discount_rate = _safe_rate(values["discount_value"], values["gross_revenue"])
        leakage_value = round(
            values["expected_return_cost"] + values["discount_value"] + max(-gross_profit, 0.0), 2
        )
        total_leakage += leakage_value
        category_leakage.append(
            {
                "category": category,
                "revenue": revenue,
                "gross_margin_rate": gross_margin_rate,
                "expected_return_cost": round(values["expected_return_cost"], 2),
                "discount_rate": discount_rate,
                "leakage_value": leakage_value,
                "action_priority": _margin_action(leakage_value, gross_margin_rate),
            }
        )
    category_leakage.sort(key=lambda item: (item["leakage_value"], item["revenue"]), reverse=True)

    gross_revenue = to_float(promotion.get("summary", {}).get("gross_revenue"))
    net_revenue = to_float(profitability.get("summary", {}).get("revenue"))
    gross_profit = to_float(profitability.get("summary", {}).get("gross_profit"))
    discount_value = to_float(promotion.get("summary", {}).get("discount_value"))
    expected_return_cost = sum(item["expected_return_cost"] for item in returns_by_sku.values())
    adjusted_profit = round(gross_profit - expected_return_cost, 2)
    waterfall = [
        {
            "stage_name": "gross_list_revenue",
            "amount": round(gross_revenue, 2),
            "delta_to_net": round(gross_revenue - net_revenue, 2),
            "insight": "List value before discount and return leakage.",
        },
        {
            "stage_name": "realized_net_revenue",
            "amount": round(net_revenue, 2),
            "delta_to_net": 0.0,
            "insight": "Revenue realized after discounts and price realization.",
        },
        {
            "stage_name": "discount_leakage",
            "amount": round(discount_value, 2),
            "delta_to_net": round(-discount_value, 2),
            "insight": "Commercial leakage from promotions and markdowns.",
        },
        {
            "stage_name": "gross_profit",
            "amount": round(gross_profit, 2),
            "delta_to_net": round(gross_profit - net_revenue, 2),
            "insight": "Gross profit before return-risk adjustment.",
        },
        {
            "stage_name": "profit_after_expected_returns",
            "amount": adjusted_profit,
            "delta_to_net": round(adjusted_profit - net_revenue, 2),
            "insight": "Profit after expected return-cost drag.",
        },
    ]
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PORTFOLIO_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "profitability_margin_waterfall_report",
        "summary": {
            "sku_count": int(
                to_float(profitability.get("summary", {}).get("sku_count"), default=0.0)
            ),
            "revenue": round(net_revenue, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_margin_rate": _safe_rate(gross_profit, net_revenue),
            "margin_leakage_value": round(total_leakage, 2),
            "return_cost_ratio": _safe_rate(expected_return_cost, net_revenue),
            "loss_making_sku_count": int(
                to_float(profitability.get("summary", {}).get("loss_making_sku_count"), default=0.0)
            ),
        },
        "waterfall": waterfall,
        "category_leakage": category_leakage[:limit],
    }
    return write_json(artifact_path, payload)


def get_abc_xyz_inventory_policy_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 12,
) -> dict[str, Any]:
    artifact_path = _cache_path(
        artifact_dir, upload_id, "portfolio_reporting_abc_xyz_inventory_policy"
    )
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["focus_skus"] = list(payload.get("focus_skus", []))[:limit]
        return payload

    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    abc = dependencies["abc_xyz"]
    abc_by_sku = _abc_lookup(abc)
    stockout_by_sku = _stockout_lookup(dependencies["stockout"])
    reorder_by_sku = _reorder_lookup(dependencies["reorder"])
    inventory_by_sku = _inventory_lookup(dependencies["inventory"])

    grouped: dict[str, dict[str, float]] = defaultdict(
        lambda: {"sku_count": 0.0, "revenue_share": 0.0}
    )
    focus_skus = []
    high_attention_sku_count = 0
    ax_revenue_share = 0.0
    cz_sku_count = 0
    for sku, item in abc_by_sku.items():
        combined_class = to_text(item.get("combined_class")) or "CZ"
        grouped_row = grouped[combined_class]
        grouped_row["sku_count"] += 1.0
        grouped_row["revenue_share"] += to_float(item.get("revenue_share"))
        if combined_class == "AX":
            ax_revenue_share += to_float(item.get("revenue_share"))
        if combined_class == "CZ":
            cz_sku_count += 1
        stockout_probability = to_float(stockout_by_sku.get(sku, {}).get("stockout_probability"))
        days_of_cover = to_float(inventory_by_sku.get(sku, {}).get("days_of_cover"))
        reorder_urgency_score = to_float(reorder_by_sku.get(sku, {}).get("urgency_score"))
        if (
            stockout_probability >= 0.35
            or reorder_urgency_score >= 2.0
            or combined_class in {"AZ", "BZ", "CZ"}
        ):
            if stockout_probability >= 0.35 or combined_class == "CZ":
                high_attention_sku_count += 1
            focus_skus.append(
                {
                    "sku": sku,
                    "category": to_text(item.get("category")) or "uncategorized",
                    "combined_class": combined_class,
                    "stockout_probability": round(stockout_probability, 4),
                    "days_of_cover": round(days_of_cover, 2),
                    "reorder_urgency_score": round(reorder_urgency_score, 2),
                    "policy_action": _policy_targets(combined_class)[3],
                }
            )

    policy_grid = []
    for combined_class, values in sorted(grouped.items()):
        service_level_target, review_cadence, safety_stock_posture, recommended_action = (
            _policy_targets(combined_class)
        )
        policy_grid.append(
            {
                "combined_class": combined_class,
                "sku_count": int(values["sku_count"]),
                "revenue_share": round(values["revenue_share"], 4),
                "service_level_target": service_level_target,
                "review_cadence": review_cadence,
                "safety_stock_posture": safety_stock_posture,
                "recommended_action": recommended_action,
            }
        )
    focus_skus.sort(
        key=lambda item: (
            item["stockout_probability"],
            item["reorder_urgency_score"],
            -item["days_of_cover"],
        ),
        reverse=True,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PORTFOLIO_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "abc_xyz_inventory_policy_report",
        "summary": {
            "sku_count": int(to_float(abc.get("summary", {}).get("sku_count"), default=0.0)),
            "class_count": len(policy_grid),
            "ax_revenue_share": round(ax_revenue_share, 4),
            "cz_sku_count": cz_sku_count,
            "high_attention_sku_count": len(focus_skus),
        },
        "policy_grid": policy_grid,
        "focus_skus": focus_skus[:limit],
    }
    return write_json(artifact_path, payload)


def get_basket_cross_sell_opportunity_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 12,
) -> dict[str, Any]:
    artifact_path = _cache_path(artifact_dir, upload_id, "portfolio_reporting_basket_cross_sell")
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["opportunities"] = list(payload.get("opportunities", []))[:limit]
        return payload

    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    basket = dependencies["basket"]
    profitability_by_sku = _profitability_lookup(dependencies["profitability"])
    opportunities = []
    lifts: list[float] = []
    total_incremental_revenue = 0.0
    for item in basket.get("pairs", []):
        if not isinstance(item, dict):
            continue
        left_sku = to_text(item.get("left_sku"))
        right_sku = to_text(item.get("right_sku"))
        if not left_sku or not right_sku:
            continue
        left_profit = profitability_by_sku.get(left_sku, {})
        right_profit = profitability_by_sku.get(right_sku, {})
        average_margin = mean(
            [
                to_float(left_profit.get("gross_margin_rate")),
                to_float(right_profit.get("gross_margin_rate")),
            ]
        )
        estimated_incremental_revenue = round(
            to_float(left_profit.get("revenue"))
            * to_float(item.get("confidence"))
            * max(to_float(item.get("lift")) - 1.0, 0.0),
            2,
        )
        total_incremental_revenue += estimated_incremental_revenue
        lift_value = round(to_float(item.get("lift")), 4)
        lifts.append(lift_value)
        campaign_type = "bundle_offer"
        if lift_value >= 2.0:
            campaign_type = "checkout_cross_sell"
        elif average_margin < 0.2:
            campaign_type = "cart_add_on"
        opportunities.append(
            {
                "left_sku": left_sku,
                "right_sku": right_sku,
                "support": round(to_float(item.get("support")), 4),
                "confidence": round(to_float(item.get("confidence")), 4),
                "lift": lift_value,
                "bundle_margin_rate": round(average_margin, 4),
                "estimated_incremental_revenue": estimated_incremental_revenue,
                "campaign_type": campaign_type,
                "recommended_action": f"Test {campaign_type.replace('_', ' ')} for {left_sku} and {right_sku}.",
            }
        )
    opportunities.sort(
        key=lambda item: (item["lift"], item["estimated_incremental_revenue"], item["confidence"]),
        reverse=True,
    )
    top_bundle = ""
    if opportunities:
        top_bundle = f"{opportunities[0]['left_sku']} + {opportunities[0]['right_sku']}"
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PORTFOLIO_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "basket_cross_sell_opportunity_report",
        "summary": {
            "pair_count": int(to_float(basket.get("summary", {}).get("pair_count"), default=0.0)),
            "high_confidence_pair_count": sum(
                1 for item in opportunities if item["confidence"] >= 0.5
            ),
            "average_lift": round(mean(lifts), 4) if lifts else 0.0,
            "estimated_incremental_monthly_revenue": round(total_incremental_revenue, 2),
            "top_bundle": top_bundle,
        },
        "opportunities": opportunities[:limit],
    }
    return write_json(artifact_path, payload)


def get_customer_churn_recovery_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 15,
) -> dict[str, Any]:
    artifact_path = _cache_path(
        artifact_dir, upload_id, "portfolio_reporting_customer_churn_recovery"
    )
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["customers"] = list(payload.get("customers", []))[:limit]
        return payload

    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    churn = dependencies["churn"]
    customer_by_id = _customer_lookup(dependencies["customer"])
    risk_band_rollup: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "customer_count": 0.0,
            "revenue_at_risk": 0.0,
            "churn_score_sum": 0.0,
        }
    )
    customers = []
    for item in churn.get("customers", []):
        if not isinstance(item, dict):
            continue
        customer_id = to_text(item.get("customer_id"))
        if not customer_id:
            continue
        customer_item = customer_by_id.get(customer_id, {})
        risk_band = to_text(item.get("churn_risk_band")) or "unknown"
        total_revenue = round(
            to_float(customer_item.get("total_revenue")) or to_float(item.get("total_revenue")), 2
        )
        expected_ltv = round(to_float(customer_item.get("expected_ltv")) or total_revenue * 1.3, 2)
        churn_score = round(to_float(item.get("churn_score")), 4)
        multiplier = (
            0.9
            if risk_band == "lost"
            else 0.6
            if risk_band == "high"
            else 0.35
            if risk_band == "medium"
            else 0.15
        )
        revenue_at_risk = round(expected_ltv * multiplier, 2)
        current = risk_band_rollup[risk_band]
        current["customer_count"] += 1.0
        current["revenue_at_risk"] += revenue_at_risk
        current["churn_score_sum"] += churn_score
        customers.append(
            {
                "customer_id": customer_id,
                "segment": to_text(customer_item.get("segment")) or "developing",
                "churn_risk_band": risk_band,
                "churn_score": churn_score,
                "total_revenue": total_revenue,
                "expected_ltv": expected_ltv,
                "recommended_action": to_text(item.get("recommended_action"))
                or "trigger retention journey",
                "revenue_at_risk": revenue_at_risk,
            }
        )
    customers.sort(
        key=lambda item: (item["revenue_at_risk"], item["churn_score"], item["expected_ltv"]),
        reverse=True,
    )
    risk_bands = []
    for risk_band, values in risk_band_rollup.items():
        primary_play = "maintain loyalty touchpoints"
        if risk_band == "lost":
            primary_play = "run win-back sequence with manual follow-up"
        elif risk_band == "high":
            primary_play = "launch save offer within 7 days"
        elif risk_band == "medium":
            primary_play = "send reminder and monitor repeat conversion"
        risk_bands.append(
            {
                "risk_band": risk_band,
                "customer_count": int(values["customer_count"]),
                "revenue_at_risk": round(values["revenue_at_risk"], 2),
                "average_churn_score": round(
                    values["churn_score_sum"] / values["customer_count"], 4
                )
                if values["customer_count"]
                else 0.0,
                "primary_play": primary_play,
            }
        )
    risk_bands.sort(key=lambda item: item["revenue_at_risk"], reverse=True)
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PORTFOLIO_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "customer_churn_recovery_report",
        "summary": {
            "customer_count": int(
                to_float(churn.get("summary", {}).get("customer_count"), default=0.0)
            ),
            "high_risk_customer_count": int(
                to_float(churn.get("summary", {}).get("high_risk_customer_count"), default=0.0)
            ),
            "lost_customer_count": int(
                to_float(churn.get("summary", {}).get("lost_customer_count"), default=0.0)
            ),
            "recovery_value_at_risk": round(sum(item["revenue_at_risk"] for item in customers), 2),
            "primary_recovery_segment": risk_bands[0]["risk_band"] if risk_bands else "low",
        },
        "risk_bands": risk_bands,
        "customers": customers[:limit],
    }
    return write_json(artifact_path, payload)


def get_payment_revenue_assurance_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 15,
) -> dict[str, Any]:
    artifact_path = _cache_path(
        artifact_dir, upload_id, "portfolio_reporting_payment_revenue_assurance"
    )
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["exceptions"] = list(payload.get("exceptions", []))[:limit]
        return payload

    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    payment = dependencies["payment"]
    provider_rollup: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "order_count": 0.0,
            "mismatch_count": 0.0,
            "variance_amount": 0.0,
            "refund_amount": 0.0,
        }
    )
    exceptions = []
    for item in payment.get("orders", []):
        if not isinstance(item, dict):
            continue
        provider = to_text(item.get("payment_provider")) or "unknown"
        variance_amount = round(to_float(item.get("variance_amount")), 2)
        refund_amount = round(to_float(item.get("refund_amount")), 2)
        status = to_text(item.get("reconciliation_status")) or "unknown"
        current = provider_rollup[provider]
        current["order_count"] += 1.0
        current["variance_amount"] += abs(variance_amount)
        current["refund_amount"] += refund_amount
        if status != "matched":
            current["mismatch_count"] += 1.0
            recommended_action = "investigate payment event and refund ledger"
            if status == "missing_payment":
                recommended_action = "check gateway capture and mark order for finance hold"
            elif status == "underpaid":
                recommended_action = "reconcile settlement shortfall and customer charge"
            elif status == "overpaid":
                recommended_action = "validate duplicate capture and refund if required"
            exceptions.append(
                {
                    "order_id": to_text(item.get("order_id")),
                    "payment_provider": provider,
                    "reconciliation_status": status,
                    "order_amount": round(to_float(item.get("order_amount")), 2),
                    "paid_amount": round(to_float(item.get("paid_amount")), 2),
                    "refund_amount": refund_amount,
                    "variance_amount": variance_amount,
                    "recommended_action": recommended_action,
                }
            )
    provider_scorecards = []
    for provider, values in provider_rollup.items():
        assurance_priority = "monitor"
        if values["mismatch_count"] >= 2 or values["variance_amount"] >= 100:
            assurance_priority = "high"
        if values["mismatch_count"] >= max(1.0, values["order_count"] * 0.5):
            assurance_priority = "critical"
        provider_scorecards.append(
            {
                "payment_provider": provider,
                "order_count": int(values["order_count"]),
                "mismatch_count": int(values["mismatch_count"]),
                "variance_amount": round(values["variance_amount"], 2),
                "refund_amount": round(values["refund_amount"], 2),
                "assurance_priority": assurance_priority,
            }
        )
    provider_scorecards.sort(
        key=lambda item: (item["mismatch_count"], item["variance_amount"]), reverse=True
    )
    exceptions.sort(key=lambda item: abs(item["variance_amount"]), reverse=True)
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PORTFOLIO_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "payment_revenue_assurance_report",
        "summary": {
            "order_count": int(
                to_float(payment.get("summary", {}).get("order_count"), default=0.0)
            ),
            "mismatch_order_count": len(exceptions),
            "missing_payment_orders": int(
                to_float(payment.get("summary", {}).get("missing_payment_orders"), default=0.0)
            ),
            "refunded_orders": int(
                to_float(payment.get("summary", {}).get("refunded_orders"), default=0.0)
            ),
            "gross_cash_exposure": round(
                sum(abs(item["variance_amount"]) for item in exceptions), 2
            ),
        },
        "provider_scorecards": provider_scorecards,
        "exceptions": exceptions[:limit],
    }
    return write_json(artifact_path, payload)


def get_seasonality_calendar_readiness_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 12,
) -> dict[str, Any]:
    artifact_path = _cache_path(
        artifact_dir, upload_id, "portfolio_reporting_seasonality_calendar_readiness"
    )
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["focus_skus"] = list(payload.get("focus_skus", []))[:limit]
        return payload

    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    seasonality = dependencies["seasonality"]
    forecast_by_sku = _forecast_lookup(dependencies["forecast"])
    peak_rollup: dict[str, dict[str, float]] = defaultdict(
        lambda: {"sku_count": 0.0, "revenue": 0.0}
    )
    focus_skus = []
    total_revenue = 0.0
    for item in seasonality.get("skus", []):
        if not isinstance(item, dict):
            continue
        peak_month = to_text(item.get("peak_month"))
        revenue = round(to_float(item.get("total_revenue")), 2)
        total_revenue += revenue
        peak_rollup[peak_month]["sku_count"] += 1.0
        peak_rollup[peak_month]["revenue"] += revenue
        seasonality_band = to_text(item.get("seasonality_band")) or "steady"
        if seasonality_band in {"strong_seasonal", "moderate_seasonal"}:
            readiness_action = "build buy plan 6-8 weeks before peak"
            if seasonality_band == "moderate_seasonal":
                readiness_action = "review calendar demand and align promo pacing"
            focus_skus.append(
                {
                    "sku": to_text(item.get("sku")),
                    "category": to_text(item.get("category")) or "uncategorized",
                    "seasonality_band": seasonality_band,
                    "peak_month": peak_month,
                    "peak_month_revenue_share": round(
                        to_float(item.get("peak_month_revenue_share")), 4
                    ),
                    "forecast_30d": forecast_by_sku.get(to_text(item.get("sku")), 0.0),
                    "readiness_action": readiness_action,
                }
            )
    peak_months = []
    for peak_month, values in peak_rollup.items():
        planning_message = "keep normal cadence"
        if values["sku_count"] >= 2:
            planning_message = "prepare inventory and marketing calendar before this peak"
        peak_months.append(
            {
                "peak_month": peak_month,
                "sku_count": int(values["sku_count"]),
                "revenue_share": _safe_rate(values["revenue"], total_revenue),
                "planning_message": planning_message,
            }
        )
    peak_months.sort(key=lambda item: item["revenue_share"], reverse=True)
    focus_skus.sort(
        key=lambda item: (item["peak_month_revenue_share"], item["forecast_30d"]), reverse=True
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PORTFOLIO_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "seasonality_calendar_readiness_report",
        "summary": {
            "sku_count": int(
                to_float(seasonality.get("summary", {}).get("sku_count"), default=0.0)
            ),
            "strong_seasonal_sku_count": int(
                to_float(
                    seasonality.get("summary", {}).get("strong_seasonal_sku_count"), default=0.0
                )
            ),
            "moderate_seasonal_sku_count": int(
                to_float(
                    seasonality.get("summary", {}).get("moderate_seasonal_sku_count"), default=0.0
                )
            ),
            "most_common_peak_month": to_text(
                seasonality.get("summary", {}).get("most_common_peak_month")
            ),
            "readiness_action_count": len(focus_skus),
        },
        "peak_months": peak_months,
        "focus_skus": focus_skus[:limit],
    }
    return write_json(artifact_path, payload)


def get_assortment_rationalization_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 15,
) -> dict[str, Any]:
    artifact_path = _cache_path(
        artifact_dir, upload_id, "portfolio_reporting_assortment_rationalization"
    )
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["sku_actions"] = list(payload.get("sku_actions", []))[:limit]
        return payload

    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    assortment = dependencies["assortment"]
    profitability_by_sku = _profitability_lookup(dependencies["profitability"])
    inventory_by_sku = _inventory_lookup(dependencies["inventory"])
    abc_by_sku = _abc_lookup(dependencies["abc_xyz"])
    category_rollup: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "sku_count": 0.0,
            "hero_revenue_share": 0.0,
            "long_tail_revenue_share": 0.0,
            "exit_candidate_count": 0.0,
            "expand_candidate_count": 0.0,
        }
    )
    sku_actions = []
    for item in assortment.get("skus", []):
        if not isinstance(item, dict):
            continue
        sku = to_text(item.get("sku"))
        category = to_text(item.get("category")) or "uncategorized"
        movement_class = to_text(item.get("movement_class")) or "long_tail"
        combined_class = to_text(abc_by_sku.get(sku, {}).get("combined_class")) or "CZ"
        margin_rate = round(to_float(profitability_by_sku.get(sku, {}).get("gross_margin_rate")), 4)
        days_of_cover = round(to_float(inventory_by_sku.get(sku, {}).get("days_of_cover")), 2)
        action = _assortment_action(movement_class, combined_class, margin_rate, days_of_cover)
        category_item = category_rollup[category]
        category_item["sku_count"] += 1.0
        if movement_class == "hero":
            category_item["hero_revenue_share"] += to_float(item.get("revenue_share"))
        if movement_class in {"slow_mover", "long_tail"}:
            category_item["long_tail_revenue_share"] += to_float(item.get("revenue_share"))
        if action == "rationalize assortment and reduce buys":
            category_item["exit_candidate_count"] += 1.0
        if action == "expand distribution and protect availability":
            category_item["expand_candidate_count"] += 1.0
        if movement_class in {"slow_mover", "long_tail", "hero"}:
            sku_actions.append(
                {
                    "sku": sku,
                    "category": category,
                    "movement_class": movement_class,
                    "combined_class": combined_class,
                    "gross_margin_rate": margin_rate,
                    "days_of_cover": days_of_cover,
                    "action": action,
                }
            )
    category_actions = []
    for category, values in category_rollup.items():
        recommendation = "keep balanced review cadence"
        if (
            values["exit_candidate_count"] >= values["expand_candidate_count"]
            and values["exit_candidate_count"] >= 1
        ):
            recommendation = "remove low-performing tail and simplify range"
        elif values["expand_candidate_count"] >= 1:
            recommendation = "add space to hero SKUs and protect service"
        category_actions.append(
            {
                "category": category,
                "sku_count": int(values["sku_count"]),
                "hero_revenue_share": round(values["hero_revenue_share"], 4),
                "long_tail_revenue_share": round(values["long_tail_revenue_share"], 4),
                "exit_candidate_count": int(values["exit_candidate_count"]),
                "expand_candidate_count": int(values["expand_candidate_count"]),
                "recommendation": recommendation,
            }
        )
    category_actions.sort(
        key=lambda item: (item["exit_candidate_count"], item["long_tail_revenue_share"]),
        reverse=True,
    )
    sku_actions.sort(
        key=lambda item: (
            item["action"] != "rationalize assortment and reduce buys",
            -item["days_of_cover"],
            item["gross_margin_rate"],
        )
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PORTFOLIO_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "assortment_rationalization_report",
        "summary": {
            "sku_count": int(to_float(assortment.get("summary", {}).get("sku_count"), default=0.0)),
            "category_count": int(
                to_float(assortment.get("summary", {}).get("category_count"), default=0.0)
            ),
            "hero_sku_share": round(
                to_float(assortment.get("summary", {}).get("hero_sku_share")), 4
            ),
            "long_tail_revenue_share": round(
                to_float(assortment.get("summary", {}).get("long_tail_revenue_share")), 4
            ),
            "exit_candidate_count": sum(item["exit_candidate_count"] for item in category_actions),
            "expand_candidate_count": sum(
                item["expand_candidate_count"] for item in category_actions
            ),
        },
        "category_actions": category_actions,
        "sku_actions": sku_actions[:limit],
    }
    return write_json(artifact_path, payload)


def get_customer_value_segmentation_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 15,
) -> dict[str, Any]:
    artifact_path = _cache_path(
        artifact_dir, upload_id, "portfolio_reporting_customer_value_segmentation"
    )
    cached = _read_cached(artifact_path, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["prioritized_customers"] = list(payload.get("prioritized_customers", []))[:limit]
        return payload

    dependencies = _load_portfolio_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    customer = dependencies["customer"]
    churn_by_customer = _customer_lookup(dependencies["churn"])
    total_revenue = sum(
        to_float(item.get("total_revenue"))
        for item in customer.get("customers", [])
        if isinstance(item, dict)
    )
    total_ltv = sum(
        to_float(item.get("expected_ltv"))
        for item in customer.get("customers", [])
        if isinstance(item, dict)
    )
    segment_rollup: dict[str, dict[str, float]] = defaultdict(
        lambda: {"customer_count": 0.0, "revenue": 0.0, "expected_ltv": 0.0}
    )
    prioritized_customers = []
    champion_customer_count = 0
    at_risk_value = 0.0
    for item in customer.get("customers", []):
        if not isinstance(item, dict):
            continue
        customer_id = to_text(item.get("customer_id"))
        segment = to_text(item.get("segment")) or "developing"
        if segment == "champion":
            champion_customer_count += 1
        revenue = round(to_float(item.get("total_revenue")), 2)
        expected_ltv = round(to_float(item.get("expected_ltv")), 2)
        recency_days = int(to_float(item.get("recency_days"), default=0.0))
        churn_band = to_text(churn_by_customer.get(customer_id, {}).get("churn_risk_band")) or "low"
        next_best_action = "maintain loyalty touchpoints"
        if segment == "champion":
            next_best_action = "protect service and attach premium bundles"
        elif churn_band in {"high", "lost"}:
            next_best_action = "trigger retention outreach with recovery offer"
        elif segment == "new":
            next_best_action = "drive second purchase within 30 days"
        if churn_band in {"high", "lost", "at_risk"}:
            at_risk_value += expected_ltv
        rollup = segment_rollup[segment]
        rollup["customer_count"] += 1.0
        rollup["revenue"] += revenue
        rollup["expected_ltv"] += expected_ltv
        prioritized_customers.append(
            {
                "customer_id": customer_id,
                "segment": segment,
                "churn_risk_band": churn_band,
                "total_revenue": revenue,
                "expected_ltv": expected_ltv,
                "recency_days": recency_days,
                "next_best_action": next_best_action,
            }
        )
    segment_mix = []
    for segment, values in segment_rollup.items():
        primary_action = "grow frequency"
        if segment == "champion":
            primary_action = "protect value and upsell premium range"
        elif segment == "at_risk":
            primary_action = "save customer before lapse"
        elif segment == "new":
            primary_action = "accelerate second-order conversion"
        segment_mix.append(
            {
                "segment": segment,
                "customer_count": int(values["customer_count"]),
                "revenue_share": _safe_rate(values["revenue"], total_revenue),
                "expected_ltv_share": _safe_rate(values["expected_ltv"], total_ltv),
                "primary_action": primary_action,
            }
        )
    segment_mix.sort(key=lambda item: item["expected_ltv_share"], reverse=True)
    prioritized_customers.sort(
        key=lambda item: (
            item["expected_ltv"],
            item["churn_risk_band"] in {"high", "lost"},
            -item["recency_days"],
        ),
        reverse=True,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": PORTFOLIO_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "customer_value_segmentation_report",
        "summary": {
            "customer_count": int(
                to_float(customer.get("summary", {}).get("customer_count"), default=0.0)
            ),
            "repeat_customer_rate": round(
                to_float(customer.get("summary", {}).get("repeat_customer_rate")), 4
            ),
            "champion_customer_count": champion_customer_count,
            "at_risk_value": round(at_risk_value, 2),
            "priority_segment": segment_mix[0]["segment"] if segment_mix else "developing",
        },
        "segment_mix": segment_mix,
        "prioritized_customers": prioritized_customers[:limit],
    }
    return write_json(artifact_path, payload)


def get_portfolio_report_index() -> list[dict[str, str]]:
    return list(PORTFOLIO_REPORT_INDEX)
