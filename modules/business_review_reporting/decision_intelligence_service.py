# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         decision_intelligence_service.py
# Path:         modules/business_review_reporting/decision_intelligence_service.py
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
#   - Main types: _BoardPackStyles
#   - Key APIs: build_scenario_simulation_report, build_alert_to_action_playbook_report, build_cross_module_decision_intelligence_report, build_portfolio_opportunity_matrix_report, build_board_style_pdf_pack, get_scenario_simulation_report, ...
#   - Dependencies: __future__, collections, pathlib, statistics, typing, pypdf, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
from modules.customer_cohort_intelligence.service import build_cohort_artifact
from modules.forecasting.service import get_or_create_batch_forecast_artifact
from modules.fulfillment_sla_intelligence.service import build_fulfillment_sla_artifact
from modules.inventory_aging_intelligence.service import build_inventory_aging_artifact
from modules.profitability_intelligence.service import build_profitability_artifact
from modules.promotion_pricing_intelligence.service import build_promotion_pricing_artifact
from modules.reorder_engine.service import get_or_create_reorder_artifact
from modules.returns_intelligence.service import get_or_create_returns_artifact
from modules.stockout_intelligence.service import get_or_create_stockout_artifact
from modules.supplier_procurement_intelligence.service import build_supplier_procurement_artifact

DECISION_INTELLIGENCE_REPORTING_VERSION = "decision-intelligence-reporting-v1"
DECISION_INTELLIGENCE_REPORT_INDEX = [
    {
        "report_name": "scenario_simulation_pack",
        "endpoint": "/api/v1/business-reports/scenario-simulation",
    },
    {
        "report_name": "board_style_pdf_pack",
        "endpoint": "/api/v1/business-reports/board-pack",
    },
    {
        "report_name": "alert_to_action_playbook",
        "endpoint": "/api/v1/business-reports/alert-to-action-playbook",
    },
    {
        "report_name": "cross_module_decision_intelligence_report",
        "endpoint": "/api/v1/business-reports/cross-module-decision-intelligence",
    },
    {
        "report_name": "portfolio_opportunity_matrix_report",
        "endpoint": "/api/v1/business-reports/portfolio-opportunity-matrix",
    },
]


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _decision_intelligence_dependency_dirs(artifact_dir: Path) -> dict[str, Path]:
    dependency_dir = artifact_dir / "dependencies"
    return {
        "forecast": dependency_dir / "forecasts",
        "stockout": dependency_dir / "stockout_risk",
        "reorder": dependency_dir / "reorder",
        "returns": dependency_dir / "returns_risk",
        "profitability": dependency_dir / "profitability",
        "inventory_aging": dependency_dir / "inventory_aging",
        "supplier": dependency_dir / "supplier_procurement",
        "fulfillment": dependency_dir / "fulfillment_sla",
        "promotion": dependency_dir / "promotion_pricing",
        "cohort": dependency_dir / "customer_cohorts",
    }


def _load_decision_intelligence_dependencies(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool,
) -> dict[str, Any]:
    dirs = _decision_intelligence_dependency_dirs(artifact_dir)
    return {
        "forecast": get_or_create_batch_forecast_artifact(
            upload_id=upload_id,
            uploads_dir=uploads_dir,
            artifact_dir=dirs["forecast"],
            refresh=refresh,
        ),
        "stockout": get_or_create_stockout_artifact(
            upload_id=upload_id,
            uploads_dir=uploads_dir,
            artifact_dir=dirs["stockout"],
            refresh=refresh,
        ),
        "reorder": get_or_create_reorder_artifact(
            upload_id=upload_id,
            uploads_dir=uploads_dir,
            forecast_artifact_dir=dirs["forecast"],
            stockout_artifact_dir=dirs["stockout"],
            artifact_dir=dirs["reorder"],
            refresh=refresh,
        ),
        "returns": get_or_create_returns_artifact(
            upload_id=upload_id,
            uploads_dir=uploads_dir,
            artifact_dir=dirs["returns"],
            refresh=refresh,
        ),
        "profitability": build_profitability_artifact(
            upload_id,
            uploads_dir,
            dirs["profitability"],
            refresh,
        ),
        "inventory_aging": build_inventory_aging_artifact(
            upload_id,
            uploads_dir,
            dirs["inventory_aging"],
            refresh,
        ),
        "supplier": build_supplier_procurement_artifact(
            upload_id,
            uploads_dir,
            dirs["supplier"],
            refresh,
        ),
        "fulfillment": build_fulfillment_sla_artifact(
            upload_id,
            uploads_dir,
            dirs["fulfillment"],
            refresh,
        ),
        "promotion": build_promotion_pricing_artifact(
            upload_id,
            uploads_dir,
            dirs["promotion"],
            refresh,
        ),
        "cohort": build_cohort_artifact(
            upload_id,
            uploads_dir,
            dirs["cohort"],
            refresh,
        ),
    }


def _forecast_30_lookup(forecast: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for item in forecast.get("products", []):
        if not isinstance(item, dict):
            continue
        product_id = to_text(item.get("product_id"))
        if not product_id:
            continue
        horizon_30 = 0.0
        for horizon in item.get("horizons", []):
            if not isinstance(horizon, dict):
                continue
            if int(to_float(horizon.get("horizon_days"), default=0.0)) == 30:
                horizon_30 = round(to_float(horizon.get("p50") or horizon.get("point_forecast")), 2)
                break
        lookup[product_id] = {
            "category": to_text(item.get("category")) or "uncategorized",
            "product_group": to_text(item.get("product_group")) or "unknown",
            "forecast_30d": horizon_30,
            "selected_model": to_text(item.get("selected_model")) or "baseline",
            "history_points": int(to_float(item.get("history_points"), default=0.0)),
        }
    return lookup


def _stockout_lookup(stockout: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in stockout.get("skus", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _reorder_lookup(reorder: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in reorder.get("recommendations", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _profitability_lookup(profitability: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in profitability.get("skus", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _inventory_lookup(inventory_aging: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        to_text(item.get("sku")): item
        for item in inventory_aging.get("skus", [])
        if isinstance(item, dict) and to_text(item.get("sku"))
    }


def _returns_lookup(returns_artifact: dict[str, Any]) -> dict[str, dict[str, float]]:
    accumulator: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "return_probability_sum": 0.0,
            "expected_return_cost": 0.0,
            "rows": 0.0,
        }
    )
    for item in returns_artifact.get("scores", []):
        if not isinstance(item, dict):
            continue
        sku = to_text(item.get("sku"))
        if not sku:
            continue
        current = accumulator[sku]
        current["return_probability_sum"] += to_float(item.get("return_probability"))
        current["expected_return_cost"] += to_float(item.get("expected_return_cost"))
        current["rows"] += 1.0
    return {
        sku: {
            "average_return_probability": round(
                values["return_probability_sum"] / values["rows"], 4
            )
            if values["rows"]
            else 0.0,
            "expected_return_cost": round(values["expected_return_cost"], 2),
        }
        for sku, values in accumulator.items()
    }


def _supplier_risk_lookup(
    upload_id: str, uploads_dir: Path, supplier: dict[str, Any]
) -> dict[str, str]:
    supplier_band_by_id = {
        to_text(item.get("supplier_id")): to_text(item.get("procurement_risk_band")) or "unknown"
        for item in supplier.get("suppliers", [])
        if isinstance(item, dict) and to_text(item.get("supplier_id"))
    }
    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    lookup: dict[str, str] = {}
    for row in iter_normalized_rows(csv_path):
        sku = canonical_value(row, "sku", "product_id")
        supplier_id = canonical_value(row, "supplier_id")
        if sku and supplier_id and sku not in lookup:
            lookup[sku] = supplier_band_by_id.get(supplier_id, "unknown")
    return lookup


def _inventory_value_lookup(
    profitability_by_sku: dict[str, dict[str, Any]],
    inventory_by_sku: dict[str, dict[str, Any]],
) -> dict[str, float]:
    values: dict[str, float] = {}
    for sku, inventory_item in inventory_by_sku.items():
        on_hand_units = to_float(inventory_item.get("on_hand_units"))
        profit_item = profitability_by_sku.get(sku, {})
        quantity = max(to_float(profit_item.get("quantity")), 0.0)
        cost = max(to_float(profit_item.get("cost")), 0.0)
        unit_cost = cost / quantity if quantity else 0.0
        values[sku] = round(on_hand_units * unit_cost, 2)
    return values


def _rank_label(score: float) -> str:
    if score >= 2.8:
        return "critical"
    if score >= 1.8:
        return "high"
    if score >= 0.9:
        return "watch"
    return "steady"


def _strategy_for_item(
    *,
    forecast_30d: float,
    margin_rate: float,
    stockout_probability: float,
    reorder_urgency: float,
    return_probability: float,
    days_of_cover: float,
    supplier_risk_band: str,
) -> tuple[str, str, str]:
    if (
        forecast_30d >= 100.0
        and margin_rate >= 0.16
        and stockout_probability <= 0.25
        and return_probability < 0.30
    ):
        return (
            "invest_to_grow",
            "high",
            "demand is sizeable enough to justify growth funding if service is protected",
        )
    if (
        stockout_probability >= 0.4
        or reorder_urgency >= 0.75
        or (supplier_risk_band in {"high", "critical"} and stockout_probability >= 0.25)
    ):
        return (
            "protect_service",
            "high",
            "service reliability is the binding constraint on current revenue",
        )
    if days_of_cover >= 120.0 and margin_rate >= 0.25 and return_probability < 0.45:
        return (
            "harvest_cash",
            "medium",
            "inventory is absorbing cash faster than the SKU is turning",
        )
    if margin_rate < 0.18 or return_probability >= 0.45:
        return (
            "fix_or_exit",
            "medium",
            "profit leakage is too high relative to the commercial opportunity",
        )
    return (
        "optimize_mix",
        "watch",
        "the SKU is viable but still needs tighter pricing, mix, or inventory tuning",
    )


def build_scenario_simulation_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = (
        artifact_dir / f"{upload_id}_decision_intelligence_scenario_simulation_report.json"
    )
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    dependencies = _load_decision_intelligence_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    forecast_lookup = _forecast_30_lookup(dependencies["forecast"])
    stockout_lookup = _stockout_lookup(dependencies["stockout"])
    reorder_lookup = _reorder_lookup(dependencies["reorder"])
    profitability_lookup = _profitability_lookup(dependencies["profitability"])
    inventory_lookup = _inventory_lookup(dependencies["inventory_aging"])
    inventory_values = _inventory_value_lookup(profitability_lookup, inventory_lookup)

    base_projected_revenue = round(
        sum(to_float(item.get("forecast_30d")) for item in forecast_lookup.values()),
        2,
    )
    base_gross_margin_rate = round(
        to_float(dependencies["profitability"].get("summary", {}).get("gross_margin_rate")),
        4,
    )
    base_stockout_probability = round(
        mean(
            [to_float(item.get("stockout_probability")) for item in stockout_lookup.values()]
            or [0.0]
        ),
        4,
    )
    base_on_time_rate = round(
        to_float(dependencies["fulfillment"].get("summary", {}).get("on_time_rate")),
        4,
    )
    base_reorder_quantity = round(
        sum(to_float(item.get("reorder_quantity")) for item in reorder_lookup.values()),
        2,
    )
    base_inventory_value = round(sum(inventory_values.values()), 2)

    scenario_specs = [
        {
            "scenario_name": "lead_time_shock_20pct",
            "assumption_summary": "lead time stretches by 20 percent and supplier responsiveness softens",
            "revenue_multiplier": 0.96,
            "margin_delta": -0.01,
            "stockout_multiplier": 1.22,
            "service_delta": -0.05,
            "reorder_multiplier": 1.18,
            "working_capital_multiplier": 0.11,
            "dominant_tradeoff": "less revenue and lower service with higher working-capital pressure",
        },
        {
            "scenario_name": "demand_spike_15pct",
            "assumption_summary": "commercial demand accelerates by 15 percent faster than the current plan",
            "revenue_multiplier": 1.08,
            "margin_delta": -0.005,
            "stockout_multiplier": 1.28,
            "service_delta": -0.03,
            "reorder_multiplier": 1.24,
            "working_capital_multiplier": 0.08,
            "dominant_tradeoff": "stronger revenue with tighter service and replenishment pressure",
        },
        {
            "scenario_name": "pricing_and_promo_reset",
            "assumption_summary": "price realization improves and weak promotions are reduced",
            "revenue_multiplier": 1.03,
            "margin_delta": 0.018,
            "stockout_multiplier": 0.98,
            "service_delta": 0.01,
            "reorder_multiplier": 1.02,
            "working_capital_multiplier": 0.02,
            "dominant_tradeoff": "moderate revenue lift with a stronger margin profile",
        },
        {
            "scenario_name": "safety_stock_uplift",
            "assumption_summary": "safety-stock targets rise to stabilize availability on growth SKUs",
            "revenue_multiplier": 1.02,
            "margin_delta": -0.004,
            "stockout_multiplier": 0.76,
            "service_delta": 0.04,
            "reorder_multiplier": 1.16,
            "working_capital_multiplier": 0.16,
            "dominant_tradeoff": "better service and lower stockout risk in exchange for more cash tied up",
        },
    ]

    scenarios: list[dict[str, Any]] = []
    best_scenario = ""
    worst_scenario = ""
    best_score = float("-inf")
    worst_score = float("inf")
    for spec in scenario_specs:
        projected_revenue = round(base_projected_revenue * spec["revenue_multiplier"], 2)
        revenue_delta = round(projected_revenue - base_projected_revenue, 2)
        projected_margin_rate = round(
            max(min(base_gross_margin_rate + spec["margin_delta"], 0.9), 0.0), 4
        )
        margin_rate_delta = round(projected_margin_rate - base_gross_margin_rate, 4)
        projected_stockout_probability = round(
            max(min(base_stockout_probability * spec["stockout_multiplier"], 0.99), 0.0),
            4,
        )
        stockout_probability_delta = round(
            projected_stockout_probability - base_stockout_probability,
            4,
        )
        projected_on_time_rate = round(
            max(min(base_on_time_rate + spec["service_delta"], 0.999), 0.0),
            4,
        )
        on_time_rate_delta = round(projected_on_time_rate - base_on_time_rate, 4)
        incremental_reorder_quantity = round(
            base_reorder_quantity * (spec["reorder_multiplier"] - 1.0),
            2,
        )
        working_capital_delta = round(
            base_inventory_value * spec["working_capital_multiplier"],
            2,
        )
        scenario_score = round(
            projected_revenue * projected_margin_rate
            - working_capital_delta * 0.18
            - projected_stockout_probability * 900.0
            + projected_on_time_rate * 400.0,
            2,
        )
        if scenario_score > best_score:
            best_score = scenario_score
            best_scenario = spec["scenario_name"]
        if scenario_score < worst_score:
            worst_score = scenario_score
            worst_scenario = spec["scenario_name"]
        if spec["scenario_name"] == "pricing_and_promo_reset":
            recommended_action = (
                "reallocate promotions toward strong offers and protect price realization"
            )
        elif spec["scenario_name"] == "safety_stock_uplift":
            recommended_action = (
                "apply only to high-value growth SKUs with repeated service failures"
            )
        elif spec["scenario_name"] == "demand_spike_15pct":
            recommended_action = (
                "pre-buy supply and pre-approve expedited replenishment for hot SKUs"
            )
        else:
            recommended_action = (
                "escalate suppliers early and tighten promise dates before demand is lost"
            )
        scenarios.append(
            {
                "scenario_name": spec["scenario_name"],
                "assumption_summary": spec["assumption_summary"],
                "projected_revenue": projected_revenue,
                "revenue_delta": revenue_delta,
                "projected_gross_margin_rate": projected_margin_rate,
                "margin_rate_delta": margin_rate_delta,
                "projected_stockout_probability": projected_stockout_probability,
                "stockout_probability_delta": stockout_probability_delta,
                "projected_on_time_rate": projected_on_time_rate,
                "on_time_rate_delta": on_time_rate_delta,
                "incremental_reorder_quantity": incremental_reorder_quantity,
                "working_capital_delta": working_capital_delta,
                "scenario_score": scenario_score,
                "dominant_tradeoff": spec["dominant_tradeoff"],
                "recommended_action": recommended_action,
            }
        )

    focus_candidates: list[tuple[float, dict[str, Any]]] = []
    for sku, forecast_item in forecast_lookup.items():
        stockout_item = stockout_lookup.get(sku, {})
        reorder_item = reorder_lookup.get(sku, {})
        impact_score = (
            to_float(forecast_item.get("forecast_30d")) * 0.002
            + to_float(stockout_item.get("stockout_probability")) * 2.0
            + to_float(reorder_item.get("reorder_urgency_score"))
        )
        focus_candidates.append(
            (
                impact_score,
                {
                    "sku": sku,
                    "category": to_text(forecast_item.get("category")) or "uncategorized",
                    "current_stockout_probability": round(
                        to_float(stockout_item.get("stockout_probability")),
                        4,
                    ),
                    "current_reorder_quantity": round(
                        to_float(reorder_item.get("reorder_quantity")),
                        2,
                    ),
                },
            )
        )
    focus_candidates.sort(key=lambda item: item[0], reverse=True)
    focus_skus = []
    recommended_spec = next(
        item for item in scenario_specs if item["scenario_name"] == best_scenario
    )
    for _, item in focus_candidates[:5]:
        projected_stockout_probability = round(
            min(
                item["current_stockout_probability"] * recommended_spec["stockout_multiplier"], 0.99
            ),
            4,
        )
        projected_reorder_quantity = round(
            item["current_reorder_quantity"] * recommended_spec["reorder_multiplier"],
            2,
        )
        focus_skus.append(
            {
                "scenario_name": best_scenario,
                "sku": item["sku"],
                "category": item["category"],
                "current_stockout_probability": item["current_stockout_probability"],
                "projected_stockout_probability": projected_stockout_probability,
                "current_reorder_quantity": item["current_reorder_quantity"],
                "projected_reorder_quantity": projected_reorder_quantity,
                "impact_reason": "high demand value and supply risk make this SKU the primary scenario lever",
            }
        )

    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": DECISION_INTELLIGENCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "scenario_simulation_pack",
        "summary": {
            "scenario_count": len(scenarios),
            "recommended_scenario": best_scenario,
            "worst_case_scenario": worst_scenario,
            "base_projected_revenue": base_projected_revenue,
            "base_gross_margin_rate": base_gross_margin_rate,
            "base_stockout_probability": base_stockout_probability,
            "base_on_time_rate": base_on_time_rate,
        },
        "scenarios": scenarios,
        "focus_skus": focus_skus,
    }
    return write_json(artifact_path, payload)


def build_alert_to_action_playbook_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    artifact_path = (
        artifact_dir / f"{upload_id}_decision_intelligence_alert_to_action_playbook_report.json"
    )
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    dependencies = _load_decision_intelligence_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    inventory_values = _inventory_value_lookup(
        _profitability_lookup(dependencies["profitability"]),
        _inventory_lookup(dependencies["inventory_aging"]),
    )
    actions: list[dict[str, Any]] = []

    for item in dependencies["reorder"].get("recommendations", []):
        if not isinstance(item, dict):
            continue
        urgency = to_text(item.get("urgency")) or "watch"
        if urgency not in {"urgent", "high"}:
            continue
        sku = to_text(item.get("sku"))
        actions.append(
            {
                "playbook_name": "inventory_recovery",
                "action_title": f"Approve reorder for {sku}",
                "owner": "inventory",
                "urgency": "critical" if urgency == "urgent" else "high",
                "entity_type": "sku",
                "entity_id": sku,
                "reason": to_text(item.get("rationale"))
                or "service risk is outpacing current inventory",
                "expected_value": round(
                    to_float(item.get("expected_lost_sales_estimate"))
                    + to_float(item.get("demand_forecast_14d")) * 0.15,
                    2,
                ),
                "deadline_days": 1,
                "recommended_action": to_text(item.get("recommended_action"))
                or "issue purchase order today",
            }
        )

    for item in dependencies["fulfillment"].get("orders", []):
        if not isinstance(item, dict):
            continue
        sla_band = to_text(item.get("sla_band"))
        if sla_band not in {"breach_risk", "delayed"}:
            continue
        order_id = to_text(item.get("order_id"))
        delay_days = to_float(item.get("delay_days"))
        actions.append(
            {
                "playbook_name": "fulfillment_recovery",
                "action_title": f"Escalate order {order_id}",
                "owner": "operations",
                "urgency": "critical" if sla_band == "breach_risk" else "high",
                "entity_type": "order",
                "entity_id": order_id,
                "reason": f"carrier {to_text(item.get('carrier')) or 'unknown'} is exposing the order to {sla_band}",
                "expected_value": round(max(delay_days, 1.0) * 35.0, 2),
                "deadline_days": 1,
                "recommended_action": to_text(item.get("recommended_action"))
                or "start manual recovery workflow",
            }
        )

    for item in dependencies["returns"].get("risky_products", []):
        if not isinstance(item, dict):
            continue
        if to_text(item.get("risk_band")) not in {"high", "critical"}:
            continue
        sku = to_text(item.get("sku"))
        actions.append(
            {
                "playbook_name": "margin_protection",
                "action_title": f"Investigate return leakage on {sku}",
                "owner": "merchandising",
                "urgency": "high",
                "entity_type": "sku",
                "entity_id": sku,
                "reason": "returns cost is concentrated enough to erode product economics",
                "expected_value": round(to_float(item.get("total_expected_return_cost")), 2),
                "deadline_days": 3,
                "recommended_action": "review sizing, quality signals, and post-purchase experience",
            }
        )

    for item in dependencies["inventory_aging"].get("skus", []):
        if not isinstance(item, dict):
            continue
        aging_band = to_text(item.get("aging_band"))
        if aging_band not in {"critical", "stale", "slow_mover"}:
            continue
        sku = to_text(item.get("sku"))
        actions.append(
            {
                "playbook_name": "cash_recovery",
                "action_title": f"Reduce slow stock on {sku}",
                "owner": "merchandising",
                "urgency": "high" if aging_band in {"critical", "stale"} else "watch",
                "entity_type": "sku",
                "entity_id": sku,
                "reason": f"inventory aging band is {aging_band} with weak sales velocity",
                "expected_value": round(inventory_values.get(sku, 0.0), 2),
                "deadline_days": 7,
                "recommended_action": "prepare markdown, bundle, or stop-buy plan",
            }
        )

    supplier_counter = Counter()
    for item in dependencies["supplier"].get("suppliers", []):
        if not isinstance(item, dict):
            continue
        band = to_text(item.get("procurement_risk_band"))
        if band not in {"high", "critical"}:
            continue
        supplier_name = to_text(item.get("supplier_name")) or to_text(item.get("supplier_id"))
        supplier_counter[supplier_name] += 1
        actions.append(
            {
                "playbook_name": "supplier_escalation",
                "action_title": f"Escalate supplier {supplier_name}",
                "owner": "procurement",
                "urgency": "critical" if band == "critical" else "high",
                "entity_type": "supplier",
                "entity_id": supplier_name,
                "reason": f"fill rate and lead-time variability place the supplier in {band} risk",
                "expected_value": round(to_float(item.get("total_ordered_qty")) * 12.0, 2),
                "deadline_days": 2,
                "recommended_action": to_text(item.get("recommended_action"))
                or "launch supplier recovery call and secure alternate capacity",
            }
        )

    urgency_rank = {"critical": 4, "high": 3, "watch": 2, "steady": 1}
    actions.sort(
        key=lambda item: (urgency_rank.get(item["urgency"], 0), item["expected_value"]),
        reverse=True,
    )
    actions = actions[:limit]

    lanes: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for action in actions:
        lanes[(action["playbook_name"], action["owner"])].append(action)

    playbook_lanes = []
    for (playbook_name, owner), lane_actions in sorted(
        lanes.items(),
        key=lambda item: sum(action["expected_value"] for action in item[1]),
        reverse=True,
    ):
        playbook_lanes.append(
            {
                "lane_name": playbook_name,
                "owner": owner,
                "action_count": len(lane_actions),
                "critical_action_count": sum(
                    1 for action in lane_actions if action["urgency"] == "critical"
                ),
                "total_expected_value": round(
                    sum(action["expected_value"] for action in lane_actions), 2
                ),
                "objective": {
                    "inventory_recovery": "recover service on hot SKUs before revenue slips",
                    "fulfillment_recovery": "prevent breached orders from compounding service damage",
                    "margin_protection": "reduce avoidable return and markdown leakage",
                    "cash_recovery": "free trapped capital from slow or stale inventory",
                    "supplier_escalation": "stabilize inbound flow on risky suppliers",
                }.get(playbook_name, "protect value at risk"),
            }
        )

    owner_counter = Counter(action["owner"] for action in actions)
    playbook_counter = Counter(action["playbook_name"] for action in actions)
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": DECISION_INTELLIGENCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "alert_to_action_playbook",
        "summary": {
            "total_actions": len(actions),
            "critical_action_count": sum(
                1 for action in actions if action["urgency"] == "critical"
            ),
            "high_action_count": sum(1 for action in actions if action["urgency"] == "high"),
            "action_backlog_value": round(sum(action["expected_value"] for action in actions), 2),
            "primary_owner": owner_counter.most_common(1)[0][0] if owner_counter else "inventory",
            "top_playbook": playbook_counter.most_common(1)[0][0]
            if playbook_counter
            else "inventory_recovery",
        },
        "playbook_lanes": playbook_lanes,
        "actions": actions,
    }
    return write_json(artifact_path, payload)


def build_cross_module_decision_intelligence_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 25,
) -> dict[str, Any]:
    artifact_path = (
        artifact_dir
        / f"{upload_id}_decision_intelligence_cross_module_decision_intelligence_report.json"
    )
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    dependencies = _load_decision_intelligence_dependencies(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    forecast_lookup = _forecast_30_lookup(dependencies["forecast"])
    stockout_lookup = _stockout_lookup(dependencies["stockout"])
    reorder_lookup = _reorder_lookup(dependencies["reorder"])
    profitability_lookup = _profitability_lookup(dependencies["profitability"])
    inventory_lookup = _inventory_lookup(dependencies["inventory_aging"])
    returns_lookup = _returns_lookup(dependencies["returns"])
    supplier_lookup = _supplier_risk_lookup(upload_id, uploads_dir, dependencies["supplier"])

    decisions: list[dict[str, Any]] = []
    total_revenue_reference = round(
        sum(to_float(item.get("forecast_30d")) for item in forecast_lookup.values()),
        2,
    )
    for sku, forecast_item in forecast_lookup.items():
        stockout_item = stockout_lookup.get(sku, {})
        reorder_item = reorder_lookup.get(sku, {})
        profit_item = profitability_lookup.get(sku, {})
        inventory_item = inventory_lookup.get(sku, {})
        return_item = returns_lookup.get(sku, {})
        forecast_30d = round(to_float(forecast_item.get("forecast_30d")), 2)
        margin_rate = round(to_float(profit_item.get("gross_margin_rate")), 4)
        stockout_probability = round(to_float(stockout_item.get("stockout_probability")), 4)
        reorder_urgency = round(to_float(reorder_item.get("reorder_urgency_score")), 4)
        return_probability = round(to_float(return_item.get("average_return_probability")), 4)
        days_of_cover = round(to_float(inventory_item.get("days_of_cover")), 2)
        supplier_risk_band = supplier_lookup.get(sku, "unknown")
        strategy, confidence_band, rationale = _strategy_for_item(
            forecast_30d=forecast_30d,
            margin_rate=margin_rate,
            stockout_probability=stockout_probability,
            reorder_urgency=reorder_urgency,
            return_probability=return_probability,
            days_of_cover=days_of_cover,
            supplier_risk_band=supplier_risk_band,
        )
        value_multiplier = {
            "invest_to_grow": 0.38,
            "protect_service": 0.32,
            "fix_or_exit": 0.22,
            "harvest_cash": 0.18,
            "optimize_mix": 0.16,
        }[strategy]
        estimated_value_at_stake = round(
            forecast_30d * value_multiplier
            + reorder_urgency * 40.0
            + max(stockout_probability - return_probability, 0.0) * 120.0,
            2,
        )
        recommended_action = {
            "invest_to_grow": "increase buy depth and protect service on this growth SKU",
            "protect_service": "stabilize supply and order promising before pushing more demand",
            "fix_or_exit": "repair economics or reduce exposure before more capital is committed",
            "harvest_cash": "take inventory out, keep cash discipline, and avoid incremental buys",
            "optimize_mix": "keep the SKU but tune price, promo, and replenishment rules",
        }[strategy]
        decisions.append(
            {
                "sku": sku,
                "category": to_text(forecast_item.get("category")) or "uncategorized",
                "strategy": strategy,
                "confidence_band": confidence_band,
                "revenue_reference": forecast_30d,
                "gross_margin_rate": margin_rate,
                "stockout_probability": stockout_probability,
                "reorder_urgency_score": reorder_urgency,
                "average_return_probability": return_probability,
                "days_of_cover": days_of_cover,
                "supplier_risk_band": supplier_risk_band,
                "estimated_value_at_stake": estimated_value_at_stake,
                "rationale": rationale,
                "recommended_action": recommended_action,
            }
        )

    decisions.sort(
        key=lambda item: (item["estimated_value_at_stake"], item["revenue_reference"]),
        reverse=True,
    )
    decisions = decisions[:limit]
    strategy_counter = Counter(item["strategy"] for item in decisions)
    strategy_mix = []
    for strategy, count in strategy_counter.most_common():
        strategy_value = round(
            sum(
                item["estimated_value_at_stake"]
                for item in decisions
                if item["strategy"] == strategy
            ),
            2,
        )
        strategy_revenue = round(
            sum(item["revenue_reference"] for item in decisions if item["strategy"] == strategy),
            2,
        )
        strategy_mix.append(
            {
                "strategy": strategy,
                "sku_count": count,
                "revenue_share": _safe_rate(strategy_revenue, total_revenue_reference),
                "estimated_value_at_stake": strategy_value,
                "strategy_goal": {
                    "invest_to_grow": "convert demand into incremental profitable growth",
                    "protect_service": "stop service failures from destroying demand",
                    "fix_or_exit": "repair bad unit economics or reduce exposure",
                    "harvest_cash": "release capital from slow-moving stock",
                    "optimize_mix": "fine-tune acceptable SKUs without large structural changes",
                }.get(strategy, "improve business control"),
            }
        )

    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": DECISION_INTELLIGENCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "cross_module_decision_intelligence_report",
        "summary": {
            "sku_count": len(decisions),
            "strategy_count": len(strategy_mix),
            "top_strategy": strategy_mix[0]["strategy"] if strategy_mix else "optimize_mix",
            "total_estimated_value_at_stake": round(
                sum(item["estimated_value_at_stake"] for item in decisions), 2
            ),
            "invest_count": strategy_counter.get("invest_to_grow", 0),
            "protect_count": strategy_counter.get("protect_service", 0),
            "fix_count": strategy_counter.get("fix_or_exit", 0),
            "harvest_count": strategy_counter.get("harvest_cash", 0),
        },
        "strategy_mix": strategy_mix,
        "decisions": decisions,
    }
    return write_json(artifact_path, payload)


def build_portfolio_opportunity_matrix_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 12,
) -> dict[str, Any]:
    artifact_path = (
        artifact_dir / f"{upload_id}_decision_intelligence_portfolio_opportunity_matrix_report.json"
    )
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    decision_report = build_cross_module_decision_intelligence_report(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        limit=200,
    )
    quadrant_map = {
        "invest_to_grow": ("accelerate_growth", "scale winning demand"),
        "protect_service": ("protect_revenue", "stabilize supply and service"),
        "fix_or_exit": ("repair_or_exit", "fix economics or shrink exposure"),
        "harvest_cash": ("release_cash", "reduce trapped working capital"),
        "optimize_mix": ("optimize_core", "fine-tune mix and pricing"),
    }
    total_revenue_reference = round(
        sum(
            to_float(item.get("revenue_reference")) for item in decision_report.get("decisions", [])
        ),
        2,
    )
    quadrants: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "sku_count": 0,
            "revenue_reference": 0.0,
            "margin_rates": [],
            "stockout_probabilities": [],
            "goal": "improve portfolio quality",
            "recommended_action": "review priority items",
        }
    )
    focus_items: list[dict[str, Any]] = []
    for item in decision_report.get("decisions", []):
        if not isinstance(item, dict):
            continue
        quadrant_name, goal = quadrant_map.get(
            to_text(item.get("strategy")),
            ("optimize_core", "fine-tune mix and pricing"),
        )
        quadrant = quadrants[quadrant_name]
        quadrant["sku_count"] += 1
        quadrant["revenue_reference"] += to_float(item.get("revenue_reference"))
        quadrant["margin_rates"].append(to_float(item.get("gross_margin_rate")))
        quadrant["stockout_probabilities"].append(to_float(item.get("stockout_probability")))
        quadrant["goal"] = goal
        quadrant["recommended_action"] = {
            "accelerate_growth": "fund growth but pair it with higher service protection",
            "protect_revenue": "lock in supply and carrier reliability before more promotion",
            "repair_or_exit": "repair margin or returns leakage quickly, otherwise pull back",
            "release_cash": "take inventory out and stop incremental buys until turn improves",
            "optimize_core": "keep optimizing without large structural changes",
        }.get(quadrant_name, "review priority items")
        focus_items.append(
            {
                "sku": to_text(item.get("sku")),
                "category": to_text(item.get("category")) or "uncategorized",
                "quadrant": quadrant_name,
                "revenue_reference": round(to_float(item.get("revenue_reference")), 2),
                "gross_margin_rate": round(to_float(item.get("gross_margin_rate")), 4),
                "stockout_probability": round(to_float(item.get("stockout_probability")), 4),
                "average_return_probability": round(
                    to_float(item.get("average_return_probability")), 4
                ),
                "days_of_cover": round(to_float(item.get("days_of_cover")), 2),
                "opportunity_note": to_text(item.get("rationale")) or "cross-module review signal",
            }
        )

    quadrant_rows = []
    for quadrant_name, quadrant in sorted(
        quadrants.items(),
        key=lambda item: item[1]["revenue_reference"],
        reverse=True,
    ):
        quadrant_rows.append(
            {
                "quadrant_name": quadrant_name,
                "sku_count": quadrant["sku_count"],
                "revenue_share": _safe_rate(quadrant["revenue_reference"], total_revenue_reference),
                "average_margin_rate": round(mean(quadrant["margin_rates"] or [0.0]), 4),
                "average_stockout_probability": round(
                    mean(quadrant["stockout_probabilities"] or [0.0]), 4
                ),
                "primary_goal": quadrant["goal"],
                "recommended_action": quadrant["recommended_action"],
            }
        )
    focus_items.sort(key=lambda item: item["revenue_reference"], reverse=True)
    dominant_quadrant = quadrant_rows[0]["quadrant_name"] if quadrant_rows else "optimize_core"
    growth_revenue_share = round(
        sum(
            item["revenue_share"]
            for item in quadrant_rows
            if item["quadrant_name"] in {"accelerate_growth", "protect_revenue"}
        ),
        4,
    )
    cash_recovery_share = round(
        sum(
            item["revenue_share"]
            for item in quadrant_rows
            if item["quadrant_name"] in {"repair_or_exit", "release_cash"}
        ),
        4,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": DECISION_INTELLIGENCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "portfolio_opportunity_matrix_report",
        "summary": {
            "quadrant_count": len(quadrant_rows),
            "dominant_quadrant": dominant_quadrant,
            "high_priority_sku_count": len(focus_items[:limit]),
            "growth_revenue_share": growth_revenue_share,
            "cash_recovery_revenue_share": cash_recovery_share,
        },
        "quadrants": quadrant_rows,
        "focus_items": focus_items[:limit],
    }
    return write_json(artifact_path, payload)


class _BoardPackStyles:
    def __init__(self) -> None:
        base = getSampleStyleSheet()
        self.title = ParagraphStyle(
            "BoardPackTitle",
            parent=base["Title"],
            fontSize=24,
            leading=30,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=8,
        )
        self.subtitle = ParagraphStyle(
            "BoardPackSubtitle",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=10,
        )
        self.section = ParagraphStyle(
            "BoardPackSection",
            parent=base["Heading2"],
            fontSize=15,
            leading=20,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=8,
        )
        self.body = ParagraphStyle(
            "BoardPackBody",
            parent=base["BodyText"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#1F2937"),
        )
        self.caption = ParagraphStyle(
            "BoardPackCaption",
            parent=base["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748B"),
        )


def _board_pack_table(rows: list[list[str]], widths: list[float]) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    return table


def _render_board_pack_pdf(
    *,
    pdf_path: Path,
    upload_id: str,
    headline_metrics: list[dict[str, str]],
    board_calls: list[str],
    scenario_report: dict[str, Any],
    playbook_report: dict[str, Any],
    decision_report: dict[str, Any],
    portfolio_report: dict[str, Any],
) -> int:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    styles = _BoardPackStyles()
    story = []
    story.append(Paragraph("RetailOps Board Review Pack", styles.title))
    story.append(
        Paragraph(
            f"Upload: {upload_id} - decision-ready summary of scenario pressure, playbook actions, and portfolio choices.",
            styles.subtitle,
        )
    )

    metric_rows = [[item["label"], item["value"], item["context"]] for item in headline_metrics]
    story.append(
        _board_pack_table(
            [["Metric", "Value", "Context"], *metric_rows], [42 * mm, 28 * mm, 105 * mm]
        )
    )
    story.append(Spacer(1, 8))
    story.append(Paragraph("Board calls", styles.section))
    for call in board_calls:
        story.append(Paragraph(f"- {call}", styles.body))
    story.append(PageBreak())

    story.append(Paragraph("Scenario comparison", styles.section))
    scenario_rows = [
        [
            "Scenario",
            "Revenue delta",
            "Margin delta",
            "Stockout delta",
            "Working capital",
        ]
    ]
    for item in scenario_report.get("scenarios", []):
        if not isinstance(item, dict):
            continue
        scenario_rows.append(
            [
                to_text(item.get("scenario_name")),
                f"{to_float(item.get('revenue_delta')):,.0f}",
                f"{to_float(item.get('margin_rate_delta')):.1%}",
                f"{to_float(item.get('stockout_probability_delta')):.1%}",
                f"{to_float(item.get('working_capital_delta')):,.0f}",
            ]
        )
    story.append(_board_pack_table(scenario_rows, [52 * mm, 32 * mm, 28 * mm, 30 * mm, 34 * mm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Top scenario focus SKUs", styles.caption))
    story.append(
        _board_pack_table(
            [
                ["SKU", "Category", "Current risk", "Projected risk", "Projected reorder"],
                *[
                    [
                        to_text(item.get("sku")),
                        to_text(item.get("category")),
                        f"{to_float(item.get('current_stockout_probability')):.1%}",
                        f"{to_float(item.get('projected_stockout_probability')):.1%}",
                        f"{to_float(item.get('projected_reorder_quantity')):,.0f}",
                    ]
                    for item in scenario_report.get("focus_skus", [])
                    if isinstance(item, dict)
                ],
            ],
            [30 * mm, 40 * mm, 30 * mm, 34 * mm, 36 * mm],
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Alert-to-action playbook", styles.section))
    action_rows = [["Owner", "Action", "Urgency", "Entity", "Value"]]
    for item in playbook_report.get("actions", [])[:10]:
        if not isinstance(item, dict):
            continue
        action_rows.append(
            [
                to_text(item.get("owner")),
                to_text(item.get("action_title")),
                to_text(item.get("urgency")),
                to_text(item.get("entity_id")),
                f"{to_float(item.get('expected_value')):,.0f}",
            ]
        )
    story.append(_board_pack_table(action_rows, [25 * mm, 85 * mm, 22 * mm, 28 * mm, 25 * mm]))
    story.append(Spacer(1, 8))
    lane_rows = [["Lane", "Owner", "Actions", "Critical", "Value"]]
    for item in playbook_report.get("playbook_lanes", []):
        if not isinstance(item, dict):
            continue
        lane_rows.append(
            [
                to_text(item.get("lane_name")),
                to_text(item.get("owner")),
                str(int(to_float(item.get("action_count")))),
                str(int(to_float(item.get("critical_action_count")))),
                f"{to_float(item.get('total_expected_value')):,.0f}",
            ]
        )
    story.append(_board_pack_table(lane_rows, [45 * mm, 35 * mm, 24 * mm, 24 * mm, 32 * mm]))
    story.append(PageBreak())

    story.append(Paragraph("Cross-module decisions", styles.section))
    decision_rows = [["SKU", "Strategy", "Revenue", "Margin", "Risk", "Value"]]
    for item in decision_report.get("decisions", [])[:10]:
        if not isinstance(item, dict):
            continue
        decision_rows.append(
            [
                to_text(item.get("sku")),
                to_text(item.get("strategy")).replace("_", " "),
                f"{to_float(item.get('revenue_reference')):,.0f}",
                f"{to_float(item.get('gross_margin_rate')):.1%}",
                f"{to_float(item.get('stockout_probability')):.1%}",
                f"{to_float(item.get('estimated_value_at_stake')):,.0f}",
            ]
        )
    story.append(
        _board_pack_table(decision_rows, [28 * mm, 48 * mm, 28 * mm, 22 * mm, 22 * mm, 24 * mm])
    )
    story.append(Spacer(1, 8))
    story.append(Paragraph("Portfolio opportunity matrix", styles.section))
    quadrant_rows = [["Quadrant", "SKUs", "Share", "Margin", "Risk", "Action note"]]
    for item in portfolio_report.get("quadrants", []):
        if not isinstance(item, dict):
            continue
        action_note = to_text(item.get("recommended_action"))
        if len(action_note) > 42:
            action_note = action_note[:39].rstrip() + "..."
        quadrant_rows.append(
            [
                to_text(item.get("quadrant_name")).replace("_", " "),
                str(int(to_float(item.get("sku_count")))),
                f"{to_float(item.get('revenue_share')):.1%}",
                f"{to_float(item.get('average_margin_rate')):.1%}",
                f"{to_float(item.get('average_stockout_probability')):.1%}",
                action_note,
            ]
        )
    story.append(
        _board_pack_table(quadrant_rows, [28 * mm, 14 * mm, 18 * mm, 18 * mm, 18 * mm, 58 * mm])
    )

    def _draw_page(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(18 * mm, 10 * mm, "RetailOps Board Review Pack")
        canvas.drawRightString(192 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title="RetailOps Board Review Pack",
        author="OpenAI",
    )
    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    reader = PdfReader(str(pdf_path))
    return len(reader.pages)


def build_board_style_pdf_pack(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_decision_intelligence_board_style_pdf_pack.json"
    if not refresh:
        cached = read_json_or_none(artifact_path)
        if cached is not None:
            return cached

    scenario_report = build_scenario_simulation_report(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    playbook_report = build_alert_to_action_playbook_report(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        limit=15,
    )
    decision_report = build_cross_module_decision_intelligence_report(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        limit=15,
    )
    portfolio_report = build_portfolio_opportunity_matrix_report(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        limit=10,
    )

    pdf_path = artifact_dir / "pdfs" / f"{upload_id}_board_review_pack.pdf"
    headline_metrics = [
        {
            "label": "Projected 30d revenue",
            "value": f"{to_float(scenario_report.get('summary', {}).get('base_projected_revenue')):,.0f}",
            "context": "current base case from active SKU forecast",
        },
        {
            "label": "Base stockout risk",
            "value": f"{to_float(scenario_report.get('summary', {}).get('base_stockout_probability')):.1%}",
            "context": "average probability across scored SKUs",
        },
        {
            "label": "Open action backlog",
            "value": f"{int(to_float(playbook_report.get('summary', {}).get('total_actions')))}",
            "context": "board-visible actions across inventory, operations, procurement, and margin",
        },
        {
            "label": "Decision value at stake",
            "value": f"{to_float(decision_report.get('summary', {}).get('total_estimated_value_at_stake')):,.0f}",
            "context": "commercial value affected by the current decision mix",
        },
    ]
    recommended_scenario = to_text(
        scenario_report.get("summary", {}).get("recommended_scenario")
    ).replace("_", " ")
    top_strategy = to_text(decision_report.get("summary", {}).get("top_strategy")).replace("_", " ")
    primary_board_call = f"Prioritize {recommended_scenario} and focus on {top_strategy}."
    board_calls = [
        primary_board_call,
        "Approve same-day actions for critical replenishment and open order recovery.",
        "Protect margin by reducing leakage on return-heavy and promo-dilutive SKUs.",
        "Use the portfolio matrix to separate growth investment from cash-recovery items.",
    ]
    page_count = _render_board_pack_pdf(
        pdf_path=pdf_path,
        upload_id=upload_id,
        headline_metrics=headline_metrics,
        board_calls=board_calls,
        scenario_report=scenario_report,
        playbook_report=playbook_report,
        decision_report=decision_report,
        portfolio_report=portfolio_report,
    )
    sections = [
        {
            "section_name": "scenario_comparison",
            "headline": to_text(scenario_report.get("summary", {}).get("recommended_scenario")),
            "primary_message": "scenario pressure is quantified before more capital is committed",
        },
        {
            "section_name": "alert_to_action_playbook",
            "headline": to_text(playbook_report.get("summary", {}).get("top_playbook")),
            "primary_message": "critical operational actions are converted into owners and deadlines",
        },
        {
            "section_name": "cross_module_decisions",
            "headline": to_text(decision_report.get("summary", {}).get("top_strategy")),
            "primary_message": "SKU-level decisions align growth, service, returns, and cash",
        },
        {
            "section_name": "portfolio_opportunity_matrix",
            "headline": to_text(portfolio_report.get("summary", {}).get("dominant_quadrant")),
            "primary_message": "the portfolio is segmented into growth, protection, repair, and cash-release plays",
        },
    ]
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": DECISION_INTELLIGENCE_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "board_style_pdf_pack",
        "pdf_artifact_path": str(pdf_path.resolve()),
        "summary": {
            "pdf_generated": True,
            "pdf_page_count": page_count,
            "section_count": len(sections),
            "primary_board_call": primary_board_call,
            "board_readiness": "board_ready" if page_count >= 4 else "summary_ready",
        },
        "headline_metrics": headline_metrics,
        "sections": sections,
        "board_calls": board_calls,
    }
    return write_json(artifact_path, payload)


def get_scenario_simulation_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    return build_scenario_simulation_report(upload_id, uploads_dir, artifact_dir, refresh)


def get_alert_to_action_playbook_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    payload = build_alert_to_action_playbook_report(
        upload_id,
        uploads_dir,
        artifact_dir,
        refresh,
        limit,
    )
    response = dict(payload)
    response["actions"] = list(payload.get("actions", []))[:limit]
    return response


def get_cross_module_decision_intelligence_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 25,
) -> dict[str, Any]:
    payload = build_cross_module_decision_intelligence_report(
        upload_id,
        uploads_dir,
        artifact_dir,
        refresh,
        limit,
    )
    response = dict(payload)
    response["decisions"] = list(payload.get("decisions", []))[:limit]
    return response


def get_portfolio_opportunity_matrix_report(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 12,
) -> dict[str, Any]:
    payload = build_portfolio_opportunity_matrix_report(
        upload_id,
        uploads_dir,
        artifact_dir,
        refresh,
        limit,
    )
    response = dict(payload)
    response["focus_items"] = list(payload.get("focus_items", []))[:limit]
    return response


def get_board_style_pdf_pack(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    return build_board_style_pdf_pack(upload_id, uploads_dir, artifact_dir, refresh)
