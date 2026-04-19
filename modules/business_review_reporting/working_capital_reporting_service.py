# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         working_capital_reporting_service.py
# Path:         modules/business_review_reporting/working_capital_reporting_service.py
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
#   - Key APIs: get_inventory_investment_report, get_revenue_root_cause_report, get_forecast_quality_report, get_replenishment_decision_review
#   - Dependencies: __future__, collections, datetime, pathlib, typing, modules.common.upload_utils, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
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
from modules.forecasting.service import get_or_create_batch_forecast_artifact
from modules.inventory_aging_intelligence.service import build_inventory_aging_artifact
from modules.profitability_intelligence.service import build_profitability_artifact
from modules.reorder_engine.service import get_or_create_reorder_artifact
from modules.stockout_intelligence.service import get_or_create_stockout_artifact

WORKING_CAPITAL_REPORTING_VERSION = "working-capital-reporting-v1"
WORKING_CAPITAL_REPORT_INDEX = [
    {
        "report_name": "inventory_investment_and_working_capital_report",
        "endpoint": "/api/v1/business-reports/inventory-investment",
    },
    {
        "report_name": "revenue_root_cause_analysis_report",
        "endpoint": "/api/v1/business-reports/revenue-root-cause",
    },
    {
        "report_name": "forecast_quality_and_reliability_report",
        "endpoint": "/api/v1/business-reports/forecast-quality",
    },
    {
        "report_name": "replenishment_decision_review_pack",
        "endpoint": "/api/v1/business-reports/replenishment-review",
    },
]


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _pressure_band(ratio: float) -> str:
    if ratio >= 0.5:
        return "critical"
    if ratio >= 0.3:
        return "high"
    if ratio >= 0.15:
        return "watch"
    return "healthy"


def _quality_band(mape: float, bias: float) -> str:
    if mape <= 15.0 and abs(bias) <= 1.0:
        return "strong"
    if mape <= 30.0 and abs(bias) <= 2.5:
        return "usable"
    return "weak"


def _reliability_band(point_forecast: float, interval_width: float) -> str:
    if point_forecast <= 0 and interval_width <= 0:
        return "cold_start"
    if point_forecast <= 0:
        return "low_confidence"
    relative_width = interval_width / max(point_forecast, 1.0)
    if relative_width <= 0.6:
        return "stable"
    if relative_width <= 1.1:
        return "watch"
    return "low_confidence"


def _resolve_unit_costs(csv_path: Path) -> dict[str, float]:
    totals: dict[str, dict[str, float]] = defaultdict(lambda: {"cost": 0.0, "qty": 0.0})
    for row in iter_normalized_rows(csv_path):
        sku = canonical_value(row, "sku", "product_id", "product sku") or "unknown"
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=0.0), 0.0)
        unit_cost = max(
            to_float(canonical_value(row, "unit_cost", "cost", "cogs", "cost_of_goods")),
            0.0,
        )
        totals[sku]["cost"] += unit_cost * quantity
        totals[sku]["qty"] += quantity
    return {
        sku: round(item["cost"] / item["qty"], 4)
        for sku, item in totals.items()
        if item["qty"] > 0 and item["cost"] > 0
    }


def _artifact_meta(path: Path, upload_id: str, refresh: bool) -> dict[str, Any] | None:
    if refresh:
        return None
    cached = read_json_or_none(path)
    if cached is None:
        return None
    if cached.get("upload_id") != upload_id:
        return None
    return cached


def get_inventory_investment_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_inventory_investment_report.json"
    cached = _artifact_meta(artifact_path, upload_id, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["rows"] = list(payload.get("rows", []))[:limit]
        return payload

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    unit_cost_by_sku = _resolve_unit_costs(csv_path)
    inventory = build_inventory_aging_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    profitability = build_profitability_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    profitability_by_sku = {
        to_text(item.get("sku")): item
        for item in profitability.get("skus", [])
        if isinstance(item, dict)
    }

    rows: list[dict[str, Any]] = []
    total_inventory_value = 0.0
    total_overstock_value = 0.0
    total_dead_stock_value = 0.0
    total_stale_stock_value = 0.0
    total_days_of_cover = 0.0
    covered_sku_count = 0
    liquidation_candidate_count = 0

    for item in inventory.get("skus", []):
        if not isinstance(item, dict):
            continue
        sku = to_text(item.get("sku"))
        profitability_item = profitability_by_sku.get(sku, {})
        on_hand_units = max(to_float(item.get("on_hand_units")), 0.0)
        days_since_last_sale = max(to_float(item.get("days_since_last_sale")), 0.0)
        days_of_cover = item.get("days_of_cover")
        cover_value = None
        if days_of_cover is not None:
            cover_value = max(to_float(days_of_cover), 0.0)
            total_days_of_cover += cover_value
            covered_sku_count += 1
        quantity_sold = max(to_float(profitability_item.get("quantity")), 0.0)
        unit_cost_estimate = max(
            _safe_rate(to_float(profitability_item.get("cost")), quantity_sold),
            unit_cost_by_sku.get(sku, 0.0),
        )
        inventory_value = round(on_hand_units * unit_cost_estimate, 2)
        total_inventory_value += inventory_value
        overstock_ratio = 0.0
        if cover_value is not None and cover_value > 45.0:
            overstock_ratio = min((cover_value - 45.0) / max(cover_value, 1.0), 1.0)
        overstock_value = round(inventory_value * overstock_ratio, 2)
        total_overstock_value += overstock_value
        aging_band = to_text(item.get("aging_band")) or "active"
        dead_stock_value = (
            inventory_value if aging_band == "critical" or days_since_last_sale >= 90.0 else 0.0
        )
        stale_stock_value = inventory_value if aging_band in {"stale", "critical"} else 0.0
        total_dead_stock_value += dead_stock_value
        total_stale_stock_value += stale_stock_value
        movement_class = to_text(item.get("movement_class") or "")
        margin_band = to_text(profitability_item.get("margin_band") or "")
        if dead_stock_value > 0 or (cover_value is not None and cover_value >= 75.0):
            recommended_action = "liquidate_or_markdown"
            liquidation_candidate_count += 1
        elif overstock_value > 0:
            recommended_action = "reduce_buying_and_rebalance"
        elif margin_band in {"loss_making", "thin"}:
            recommended_action = "review_price_and_assortment"
        else:
            recommended_action = "keep_active_with_monitoring"
        rows.append(
            {
                "sku": sku,
                "category": to_text(
                    item.get("category") or profitability_item.get("category") or "uncategorized"
                ),
                "on_hand_units": round(on_hand_units, 2),
                "unit_cost_estimate": round(unit_cost_estimate, 2),
                "inventory_value": inventory_value,
                "overstock_value": overstock_value,
                "dead_stock_value": round(dead_stock_value, 2),
                "days_since_last_sale": round(days_since_last_sale, 2),
                "days_of_cover": round(cover_value, 2) if cover_value is not None else None,
                "aging_band": aging_band,
                "movement_class": movement_class or None,
                "margin_band": margin_band or None,
                "recommended_action": recommended_action,
            }
        )

    rows.sort(
        key=lambda item: (
            item["dead_stock_value"],
            item["overstock_value"],
            item["inventory_value"],
        ),
        reverse=True,
    )
    trapped_working_capital = round(total_dead_stock_value + total_overstock_value, 2)
    average_days_of_cover = (
        round(total_days_of_cover / covered_sku_count, 2) if covered_sku_count else 0.0
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": WORKING_CAPITAL_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "inventory_investment_and_working_capital_report",
        "summary": {
            "sku_count": len(rows),
            "total_inventory_value": round(total_inventory_value, 2),
            "overstock_value": round(total_overstock_value, 2),
            "dead_stock_value": round(total_dead_stock_value, 2),
            "stale_stock_value": round(total_stale_stock_value, 2),
            "trapped_working_capital": trapped_working_capital,
            "liquidation_candidate_count": liquidation_candidate_count,
            "working_capital_pressure_band": _pressure_band(
                _safe_rate(trapped_working_capital, total_inventory_value)
            ),
            "average_days_of_cover": average_days_of_cover,
        },
        "rows": rows,
    }
    payload = write_json(artifact_path, payload)
    payload = dict(payload)
    payload["rows"] = list(payload.get("rows", []))[:limit]
    return payload


def _resolve_periods(
    csv_path: Path, window_days: int
) -> tuple[list[dict[str, str]], date, date, date, date]:
    rows = list(iter_normalized_rows(csv_path))
    dated_rows = [
        (row, parse_iso_date(canonical_value(row, "order_date", "created_at", "date")))
        for row in rows
    ]
    valid_dates = [item for _, item in dated_rows if item is not None]
    if not valid_dates:
        raise ValueError("The uploaded CSV does not contain usable order_date values.")
    current_end = max(valid_dates)
    current_start = current_end - timedelta(days=max(window_days - 1, 0))
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=max(window_days - 1, 0))
    return rows, previous_start, previous_end, current_start, current_end


def _period_metrics(rows: list[dict[str, str]], start_date: date, end_date: date) -> dict[str, Any]:
    metrics = {
        "revenue": 0.0,
        "units": 0.0,
        "gross_revenue": 0.0,
        "discount_value": 0.0,
        "delayed_revenue": 0.0,
        "returned_revenue": 0.0,
        "orders": set(),
        "categories": defaultdict(float),
        "stores": defaultdict(float),
    }
    for row in rows:
        order_date = parse_iso_date(canonical_value(row, "order_date", "created_at", "date"))
        if order_date is None or order_date < start_date or order_date > end_date:
            continue
        quantity = max(to_float(canonical_value(row, "quantity", "qty"), default=0.0), 0.0)
        unit_price = max(to_float(canonical_value(row, "unit_price", "price", "price_each")), 0.0)
        list_price = max(
            to_float(canonical_value(row, "list_price", "msrp"), default=unit_price), unit_price
        )
        revenue = round(quantity * unit_price, 2)
        gross_revenue = round(quantity * list_price, 2)
        discount_value = round(max(gross_revenue - revenue, 0.0), 2)
        shipment_status = to_text(canonical_value(row, "shipment_status", "status")).lower()
        promised_date = parse_iso_date(canonical_value(row, "promised_date", "promise_date"))
        actual_delivery_date = parse_iso_date(
            canonical_value(row, "actual_delivery_date", "delivered_date", "delivery_date")
        )
        delayed = False
        if shipment_status in {"late", "delayed"}:
            delayed = True
        elif promised_date is not None:
            comparator = actual_delivery_date or end_date
            delayed = comparator > promised_date
        order_status = to_text(canonical_value(row, "order_status", "status")).lower()
        returned_flag = to_text(
            canonical_value(row, "returned", "return_flag", "is_returned")
        ).lower() in {"1", "true", "yes", "y", "returned"}
        returned = returned_flag or order_status in {"returned", "refund", "refunded", "exchange"}
        category = to_text(canonical_value(row, "category", "product_category") or "uncategorized")
        store_code = to_text(canonical_value(row, "store_code", "store", "store_id") or "unknown")
        order_id = to_text(canonical_value(row, "order_id") or f"synthetic-{category}-{store_code}")
        metrics["revenue"] += revenue
        metrics["units"] += quantity
        metrics["gross_revenue"] += gross_revenue
        metrics["discount_value"] += discount_value
        metrics["orders"].add(order_id)
        metrics["categories"][category] += revenue
        metrics["stores"][store_code] += revenue
        if delayed:
            metrics["delayed_revenue"] += revenue
        if returned:
            metrics["returned_revenue"] += revenue
    return metrics


def get_revenue_root_cause_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    window_days: int = 30,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_revenue_root_cause_report.json"
    cached = _artifact_meta(artifact_path, upload_id, refresh)
    if (
        cached is not None
        and int(to_float(cached.get("summary", {}).get("window_days"), default=window_days))
        == window_days
    ):
        return cached

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    rows, previous_start, previous_end, current_start, current_end = _resolve_periods(
        csv_path, window_days
    )
    previous = _period_metrics(rows, previous_start, previous_end)
    current = _period_metrics(rows, current_start, current_end)

    previous_revenue = round(previous["revenue"], 2)
    current_revenue = round(current["revenue"], 2)
    revenue_delta = round(current_revenue - previous_revenue, 2)
    previous_avg_price = _safe_rate(previous["revenue"], previous["units"])
    current_avg_price = _safe_rate(current["revenue"], current["units"])
    price_effect = round((current_avg_price - previous_avg_price) * current["units"], 2)
    volume_effect = round((current["units"] - previous["units"]) * previous_avg_price, 2)
    discount_effect = round(-(current["discount_value"] - previous["discount_value"]), 2)
    delay_rate_delta = _safe_rate(current["delayed_revenue"], current_revenue) - _safe_rate(
        previous["delayed_revenue"], previous_revenue
    )
    delay_effect = round(-delay_rate_delta * max(current_revenue, previous_revenue) * 0.35, 2)
    return_rate_delta = _safe_rate(current["returned_revenue"], current_revenue) - _safe_rate(
        previous["returned_revenue"], previous_revenue
    )
    returns_effect = round(-return_rate_delta * max(current_revenue, previous_revenue) * 0.4, 2)
    mix_effect = round(
        revenue_delta
        - price_effect
        - volume_effect
        - discount_effect
        - delay_effect
        - returns_effect,
        2,
    )
    contributions = [
        {
            "factor": "price_effect",
            "impact_value": price_effect,
            "direction": "positive" if price_effect >= 0 else "negative",
            "share_of_delta": _safe_rate(price_effect, revenue_delta) if revenue_delta else 0.0,
            "explanation": "Average selling price moved between the two windows.",
        },
        {
            "factor": "volume_effect",
            "impact_value": volume_effect,
            "direction": "positive" if volume_effect >= 0 else "negative",
            "share_of_delta": _safe_rate(volume_effect, revenue_delta) if revenue_delta else 0.0,
            "explanation": "Units sold changed relative to the previous comparison window.",
        },
        {
            "factor": "discount_effect",
            "impact_value": discount_effect,
            "direction": "positive" if discount_effect >= 0 else "negative",
            "share_of_delta": _safe_rate(discount_effect, revenue_delta) if revenue_delta else 0.0,
            "explanation": "Promotion depth and discount pressure changed between windows.",
        },
        {
            "factor": "fulfillment_pressure_effect",
            "impact_value": delay_effect,
            "direction": "positive" if delay_effect >= 0 else "negative",
            "share_of_delta": _safe_rate(delay_effect, revenue_delta) if revenue_delta else 0.0,
            "explanation": "A higher delayed-order share usually suppresses recognized commercial performance.",
        },
        {
            "factor": "returns_leakage_effect",
            "impact_value": returns_effect,
            "direction": "positive" if returns_effect >= 0 else "negative",
            "share_of_delta": _safe_rate(returns_effect, revenue_delta) if revenue_delta else 0.0,
            "explanation": "More returned revenue means more commercial leakage.",
        },
        {
            "factor": "mix_and_other_effect",
            "impact_value": mix_effect,
            "direction": "positive" if mix_effect >= 0 else "negative",
            "share_of_delta": _safe_rate(mix_effect, revenue_delta) if revenue_delta else 0.0,
            "explanation": "Residual change driven by category mix, store mix, and unmodelled structural shifts.",
        },
    ]
    contributions.sort(key=lambda item: abs(item["impact_value"]), reverse=True)

    segment_highlights: list[dict[str, Any]] = []
    for segment_type, current_map, previous_map in [
        ("category", current["categories"], previous["categories"]),
        ("store", current["stores"], previous["stores"]),
    ]:
        all_keys = set(current_map) | set(previous_map)
        segment_rows = []
        for key in all_keys:
            previous_segment_revenue = round(previous_map.get(key, 0.0), 2)
            current_segment_revenue = round(current_map.get(key, 0.0), 2)
            delta = round(current_segment_revenue - previous_segment_revenue, 2)
            segment_rows.append(
                {
                    "segment_type": segment_type,
                    "segment_name": key,
                    "previous_revenue": previous_segment_revenue,
                    "current_revenue": current_segment_revenue,
                    "delta_revenue": delta,
                    "explanation": (
                        f"{segment_type.capitalize()} contribution moved by {delta:.2f} between the two windows."
                    ),
                }
            )
        segment_rows.sort(key=lambda item: abs(item["delta_revenue"]), reverse=True)
        segment_highlights.extend(segment_rows[:3])

    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": WORKING_CAPITAL_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "revenue_root_cause_analysis_report",
        "summary": {
            "window_days": window_days,
            "previous_period_revenue": previous_revenue,
            "current_period_revenue": current_revenue,
            "revenue_delta": revenue_delta,
            "revenue_delta_rate": _safe_rate(revenue_delta, previous_revenue),
            "previous_period_start": previous_start.isoformat(),
            "previous_period_end": previous_end.isoformat(),
            "current_period_start": current_start.isoformat(),
            "current_period_end": current_end.isoformat(),
        },
        "methodology_note": (
            "This report uses a practical decomposition: price and volume are computed directly, "
            "discount, fulfillment, and returns are estimated from observed leakage deltas, and the "
            "remaining movement is grouped as mix and other structural change."
        ),
        "contributions": contributions,
        "segment_highlights": segment_highlights,
    }
    return write_json(artifact_path, payload)


def _horizon_lookup(product: dict[str, Any], horizon_days: int) -> dict[str, Any]:
    for item in product.get("horizons", []):
        if not isinstance(item, dict):
            continue
        if int(to_float(item.get("horizon_days"))) == horizon_days:
            return item
    return {}


def _convert_group_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
        converted.append(
            {
                "group_name": to_text(item.get("group_name") or "unknown"),
                "product_count": int(to_float(item.get("product_count"), default=0)),
                "mae": round(to_float(metrics.get("mae")), 4),
                "rmse": round(to_float(metrics.get("rmse")), 4),
                "mape": round(to_float(metrics.get("mape")), 4),
                "bias": round(to_float(metrics.get("bias")), 4),
            }
        )
    converted.sort(key=lambda item: item["mape"], reverse=True)
    return converted


def get_forecast_quality_report(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_forecast_quality_report.json"
    cached = _artifact_meta(artifact_path, upload_id, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["products"] = list(payload.get("products", []))[:limit]
        return payload

    forecast = get_or_create_batch_forecast_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    products: list[dict[str, Any]] = []
    model_counter: Counter[str] = Counter()
    reliable_count = 0
    unstable_count = 0
    biased_count = 0
    low_confidence_count = 0
    total_interval_width = 0.0

    for item in forecast.get("products", []):
        if not isinstance(item, dict):
            continue
        backtest = (
            item.get("backtest_metrics") if isinstance(item.get("backtest_metrics"), dict) else {}
        )
        horizon_14d = _horizon_lookup(item, 14)
        p10 = to_float(horizon_14d.get("p10"))
        p50 = to_float(horizon_14d.get("p50") or horizon_14d.get("point_forecast"))
        p90 = to_float(horizon_14d.get("p90"))
        interval_width = round(max(p90 - p10, 0.0), 2)
        mape = round(to_float(backtest.get("mape")), 4)
        bias = round(to_float(backtest.get("bias")), 4)
        quality_band = _quality_band(mape, bias)
        reliability_band = _reliability_band(p50, interval_width)
        if quality_band == "strong":
            reliable_count += 1
        if quality_band == "weak":
            unstable_count += 1
        if abs(bias) > 2.5:
            biased_count += 1
        if reliability_band == "low_confidence":
            low_confidence_count += 1
        if quality_band == "weak":
            recommended_action = "retrain_and_review_features"
        elif reliability_band == "low_confidence":
            recommended_action = "increase_safety_stock_and_monitor"
        else:
            recommended_action = "keep_in_nightly_batch"
        selected_model = to_text(item.get("selected_model") or "unknown")
        model_counter[selected_model] += 1
        total_interval_width += interval_width
        products.append(
            {
                "product_id": to_text(item.get("product_id") or "unknown"),
                "category": to_text(item.get("category") or "uncategorized"),
                "product_group": to_text(item.get("product_group") or "uncategorized"),
                "selected_model": selected_model,
                "mae": round(to_float(backtest.get("mae")), 4),
                "rmse": round(to_float(backtest.get("rmse")), 4),
                "mape": mape,
                "bias": bias,
                "point_forecast_14d": round(p50, 2),
                "interval_width_14d": interval_width,
                "stockout_probability_14d": round(
                    to_float(horizon_14d.get("stockout_probability")), 4
                ),
                "quality_band": quality_band,
                "reliability_band": reliability_band,
                "recommended_action": recommended_action,
            }
        )

    products.sort(key=lambda item: (item["mape"], item["interval_width_14d"]), reverse=True)
    summary = forecast.get("summary") if isinstance(forecast.get("summary"), dict) else {}
    average_metrics = (
        summary.get("average_metrics") if isinstance(summary.get("average_metrics"), dict) else {}
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": WORKING_CAPITAL_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "forecast_quality_and_reliability_report",
        "summary": {
            "product_count": len(products),
            "reliable_product_count": reliable_count,
            "unstable_product_count": unstable_count,
            "biased_product_count": biased_count,
            "low_confidence_product_count": low_confidence_count,
            "dominant_model": model_counter.most_common(1)[0][0] if model_counter else "unknown",
            "average_mae": round(to_float(average_metrics.get("mae")), 4),
            "average_rmse": round(to_float(average_metrics.get("rmse")), 4),
            "average_mape": round(to_float(average_metrics.get("mape")), 4),
            "average_bias": round(to_float(average_metrics.get("bias")), 4),
            "average_interval_width_14d": round(total_interval_width / len(products), 2)
            if products
            else 0.0,
        },
        "category_metrics": _convert_group_metrics(
            [item for item in forecast.get("category_metrics", []) if isinstance(item, dict)]
        ),
        "product_group_metrics": _convert_group_metrics(
            [item for item in forecast.get("product_group_metrics", []) if isinstance(item, dict)]
        ),
        "products": products,
    }
    payload = write_json(artifact_path, payload)
    payload = dict(payload)
    payload["products"] = list(payload.get("products", []))[:limit]
    return payload


def get_replenishment_decision_review(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_replenishment_review_report.json"
    cached = _artifact_meta(artifact_path, upload_id, refresh)
    if cached is not None:
        payload = dict(cached)
        payload["rows"] = list(payload.get("rows", []))[:limit]
        return payload

    csv_path = resolve_uploaded_csv_path(upload_id, uploads_dir)
    unit_cost_by_sku = _resolve_unit_costs(csv_path)
    profitability = build_profitability_artifact(upload_id, uploads_dir, artifact_dir, refresh)
    profitability_by_sku = {
        to_text(item.get("sku")): item
        for item in profitability.get("skus", [])
        if isinstance(item, dict)
    }
    reorder = get_or_create_reorder_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=artifact_dir,
        stockout_artifact_dir=artifact_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    stockout = get_or_create_stockout_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    stockout_by_sku = {
        to_text(item.get("sku")): item
        for item in stockout.get("skus", [])
        if isinstance(item, dict)
    }

    rows: list[dict[str, Any]] = []
    critical_action_count = 0
    recommended_today_count = 0
    moq_conflict_count = 0
    lead_time_pressure_count = 0
    excess_cover_risk_count = 0
    total_reorder_value = 0.0
    total_lost_sales_exposure = 0.0

    for item in reorder.get("recommendations", []):
        if not isinstance(item, dict):
            continue
        sku = to_text(item.get("sku") or "unknown")
        urgency = to_text(item.get("urgency") or "low")
        reorder_quantity = round(to_float(item.get("reorder_quantity")), 2)
        current_inventory = round(to_float(item.get("current_inventory")), 2)
        supplier_moq = round(max(to_float(item.get("supplier_moq")), 0.0), 2)
        demand_forecast_14d = round(to_float(item.get("demand_forecast_14d")), 2)
        demand_forecast_30d = round(to_float(item.get("demand_forecast_30d")), 2)
        days_to_stockout = round(to_float(item.get("days_to_stockout")), 2)
        lead_time_days = round(to_float(item.get("lead_time_days")), 2)
        service_level_target = round(to_float(item.get("service_level_target")), 3)
        expected_lost_sales_estimate = round(to_float(item.get("expected_lost_sales_estimate")), 2)
        unit_cost = unit_cost_by_sku.get(sku, 0.0)
        estimated_reorder_value = round(reorder_quantity * unit_cost, 2)
        total_reorder_value += estimated_reorder_value
        total_lost_sales_exposure += expected_lost_sales_estimate
        if urgency in {"critical", "high"}:
            critical_action_count += 1
        if (
            to_text(item.get("reorder_date")) == to_text(item.get("as_of_date"))
            and reorder_quantity > 0
        ):
            recommended_today_count += 1
        flags: list[str] = []
        if reorder_quantity > 0 and supplier_moq > 0 and reorder_quantity <= supplier_moq:
            flags.append("moq_conflict")
            moq_conflict_count += 1
        if days_to_stockout <= lead_time_days:
            flags.append("lead_time_pressure")
            lead_time_pressure_count += 1
        if current_inventory >= max(demand_forecast_30d, 1.0) and reorder_quantity > 0:
            flags.append("excess_cover_risk")
            excess_cover_risk_count += 1
        if expected_lost_sales_estimate >= 250.0:
            flags.append("high_lost_sales_exposure")
        stockout_row = stockout_by_sku.get(sku, {})
        if to_text(stockout_row.get("risk_band")) in {"high", "critical"}:
            flags.append("stockout_hotspot")
        if service_level_target >= 0.97:
            flags.append("service_level_stretch")
        profitability_item = profitability_by_sku.get(sku, {})
        rows.append(
            {
                "sku": sku,
                "store_code": to_text(item.get("store_code") or "unknown"),
                "urgency": urgency,
                "reorder_date": to_text(item.get("reorder_date")),
                "reorder_quantity": reorder_quantity,
                "current_inventory": current_inventory,
                "demand_forecast_14d": demand_forecast_14d,
                "demand_forecast_30d": demand_forecast_30d,
                "stockout_probability": round(to_float(item.get("stockout_probability")), 4),
                "days_to_stockout": days_to_stockout,
                "supplier_moq": supplier_moq,
                "service_level_target": service_level_target,
                "expected_lost_sales_estimate": expected_lost_sales_estimate,
                "estimated_reorder_value": estimated_reorder_value,
                "margin_band": to_text(profitability_item.get("margin_band")) or None,
                "flags": flags,
                "rationale": to_text(item.get("rationale")),
                "recommended_action": to_text(item.get("recommended_action")),
            }
        )

    rows.sort(
        key=lambda item: (
            len(item["flags"]),
            item["stockout_probability"],
            item["estimated_reorder_value"],
        ),
        reverse=True,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "model_version": WORKING_CAPITAL_REPORTING_VERSION,
        "artifact_path": str(artifact_path.resolve()),
        "report_name": "replenishment_decision_review_pack",
        "summary": {
            "total_recommendations": len(rows),
            "critical_action_count": critical_action_count,
            "recommended_today_count": recommended_today_count,
            "moq_conflict_count": moq_conflict_count,
            "lead_time_pressure_count": lead_time_pressure_count,
            "excess_cover_risk_count": excess_cover_risk_count,
            "estimated_reorder_value": round(total_reorder_value, 2),
            "estimated_lost_sales_exposure": round(total_lost_sales_exposure, 2),
        },
        "rows": rows,
    }
    payload = write_json(artifact_path, payload)
    payload = dict(payload)
    payload["rows"] = list(payload.get("rows", []))[:limit]
    return payload
