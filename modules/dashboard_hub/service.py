# Project:      RetailOps Data & AI Platform
# Module:       modules.dashboard_hub
# File:         service.py
# Path:         modules/dashboard_hub/service.py
#
# Summary:      Implements the dashboard hub service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for dashboard hub workflows.
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
#   - Key APIs: build_dashboard_workspace, render_dashboard_workspace_html, publish_dashboard_workspace, load_dashboard_workspace_artifact
#   - Dependencies: __future__, html, json, pathlib, typing, modules.analytics_kpi.service, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import html
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from modules.analytics_kpi.service import (
    build_inventory_health,
    build_overview,
    build_revenue_by_category,
    build_sales_daily,
    build_shipment_summary,
    load_transform_summary_from_upload,
)
from modules.business_review_reporting.executive_scorecard_service import (
    get_internal_benchmarking_report,
    get_operating_executive_scorecard,
)
from modules.business_review_reporting.service import (
    get_business_report_catalog,
    get_executive_business_review,
)
from modules.common.upload_utils import to_float, to_text, utc_now_iso, write_json
from modules.forecasting.service import get_or_create_batch_forecast_artifact
from modules.reorder_engine.service import get_or_create_reorder_artifact
from modules.returns_intelligence.service import get_or_create_returns_artifact
from modules.shipment_risk.service import get_open_order_predictions
from modules.stockout_intelligence.service import get_or_create_stockout_artifact

WORKSPACE_VERSION = "dashboard-hub-v1"
WORKSPACE_FILENAME_SUFFIX = "dashboard_workspace"


def _artifact_dirs(artifact_root: Path) -> dict[str, Path]:
    return {
        "workspace": artifact_root,
        "forecast": artifact_root / "forecasting",
        "stockout": artifact_root / "stockout_intelligence",
        "reorder": artifact_root / "reorder_engine",
        "returns": artifact_root / "returns_intelligence",
        "shipment": artifact_root / "shipment_risk",
        "business": artifact_root / "business_review_reporting",
    }


def _artifact_path(artifact_root: Path, upload_id: str) -> Path:
    return artifact_root / f"{upload_id}_{WORKSPACE_FILENAME_SUFFIX}.json"


def _html_artifact_path(artifact_root: Path, upload_id: str) -> Path:
    return artifact_root / f"{upload_id}_{WORKSPACE_FILENAME_SUFFIX}.html"


def _workspace_url(upload_id: str) -> str:
    return f"/dashboard/{upload_id}"


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _module_result(
    *,
    key: str,
    title: str,
    endpoint: str,
    payload: dict[str, Any] | None,
    error: str | None,
    summary: dict[str, Any],
    highlight_rows: list[dict[str, Any]],
    recommended_action: str,
) -> dict[str, Any]:
    status = "available" if error is None else "unavailable"
    artifact_path = ""
    if isinstance(payload, dict):
        artifact_path = to_text(payload.get("artifact_path"))
    return {
        "module_key": key,
        "title": title,
        "status": status,
        "endpoint": endpoint,
        "artifact_path": artifact_path,
        "summary": summary,
        "highlight_rows": highlight_rows,
        "recommended_action": recommended_action,
        "error": error or "",
    }


def _call_module(
    factory: Callable[..., dict[str, Any]],
    **kwargs: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = factory(**kwargs)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        return None, str(exc)
    return payload, None


def _forecast_module(
    payload: dict[str, Any] | None,
    error: str | None,
    max_rows: int,
) -> dict[str, Any]:
    summary = dict(payload.get("summary", {})) if isinstance(payload, dict) else {}
    products = list(payload.get("products", [])) if isinstance(payload, dict) else []
    ranked: list[dict[str, Any]] = []
    for product in products:
        if not isinstance(product, dict):
            continue
        horizons = product.get("horizons") or []
        demand_30d = 0.0
        for item in horizons:
            if not isinstance(item, dict):
                continue
            if int(to_float(item.get("horizon_days"))) != 30:
                continue
            demand_30d = max(
                to_float(item.get("point_forecast")),
                to_float(item.get("p50")),
            )
            break
        ranked.append(
            {
                "product_id": to_text(product.get("product_id")),
                "category": to_text(product.get("category")),
                "selected_model": to_text(product.get("selected_model")),
                "demand_30d": round(demand_30d, 2),
                "latest_inventory_units": round(
                    to_float(product.get("latest_inventory_units")),
                    2,
                ),
            }
        )
    ranked.sort(key=lambda item: item["demand_30d"], reverse=True)
    action = "Review high-demand products that have low inventory cover."
    return _module_result(
        key="forecasting",
        title="Demand Forecasting",
        endpoint="/api/v1/forecasting/batch",
        payload=payload,
        error=error,
        summary=summary,
        highlight_rows=ranked[:max_rows],
        recommended_action=action,
    )


def _stockout_module(
    payload: dict[str, Any] | None,
    error: str | None,
    max_rows: int,
) -> dict[str, Any]:
    summary = dict(payload.get("summary", {})) if isinstance(payload, dict) else {}
    rows = list(payload.get("skus", [])) if isinstance(payload, dict) else []
    ranked = [item for item in rows if isinstance(item, dict)]
    ranked.sort(
        key=lambda item: (
            to_float(item.get("stockout_probability")),
            -to_float(item.get("days_to_stockout")),
        ),
        reverse=True,
    )
    action = "Escalate critical SKUs with high probability and short days to stockout."
    return _module_result(
        key="stockout_intelligence",
        title="Stockout Intelligence",
        endpoint="/api/v1/stockout/predictions",
        payload=payload,
        error=error,
        summary=summary,
        highlight_rows=ranked[:max_rows],
        recommended_action=action,
    )


def _reorder_module(
    payload: dict[str, Any] | None,
    error: str | None,
    max_rows: int,
) -> dict[str, Any]:
    summary = dict(payload.get("summary", {})) if isinstance(payload, dict) else {}
    rows = list(payload.get("recommendations", [])) if isinstance(payload, dict) else []
    ranked = [item for item in rows if isinstance(item, dict)]
    ranked.sort(
        key=lambda item: (
            to_float(item.get("urgency_score")),
            to_float(item.get("reorder_quantity")),
        ),
        reverse=True,
    )
    action = "Convert urgent recommendations into supplier or store transfer actions."
    return _module_result(
        key="reorder_engine",
        title="Reorder Engine",
        endpoint="/api/v1/reorder/recommendations",
        payload=payload,
        error=error,
        summary=summary,
        highlight_rows=ranked[:max_rows],
        recommended_action=action,
    )


def _returns_module(
    payload: dict[str, Any] | None,
    error: str | None,
    max_rows: int,
) -> dict[str, Any]:
    summary = dict(payload.get("summary", {})) if isinstance(payload, dict) else {}
    rows = list(payload.get("scores", [])) if isinstance(payload, dict) else []
    ranked = [item for item in rows if isinstance(item, dict)]
    ranked.sort(
        key=lambda item: (
            to_float(item.get("expected_return_cost")),
            to_float(item.get("return_probability")),
        ),
        reverse=True,
    )
    action = "Target the highest return-cost orders with recovery or fraud controls."
    return _module_result(
        key="returns_intelligence",
        title="Returns Intelligence",
        endpoint="/api/v1/returns/scores",
        payload=payload,
        error=error,
        summary=summary,
        highlight_rows=ranked[:max_rows],
        recommended_action=action,
    )


def _shipment_module(
    payload: dict[str, Any] | None,
    error: str | None,
    max_rows: int,
) -> dict[str, Any]:
    summary = dict(payload.get("summary", {})) if isinstance(payload, dict) else {}
    rows = list(payload.get("open_orders", [])) if isinstance(payload, dict) else []
    ranked = [item for item in rows if isinstance(item, dict)]
    ranked.sort(
        key=lambda item: (
            to_float(item.get("probability")),
            to_float(item.get("inventory_lag_days")),
        ),
        reverse=True,
    )
    action = "Review open shipments with the highest delay probability and lag days."
    return _module_result(
        key="shipment_risk",
        title="Shipment Risk",
        endpoint="/api/v1/shipment-risk/open-orders",
        payload=payload,
        error=error,
        summary=summary,
        highlight_rows=ranked[:max_rows],
        recommended_action=action,
    )


def _overview_cards(
    overview: dict[str, Any],
    report_count: int,
    available_modules: int,
) -> dict[str, Any]:
    total_orders = to_float(overview.get("total_orders"))
    total_revenue = to_float(overview.get("total_revenue"))
    delayed_shipments = to_float(overview.get("delayed_shipments"))
    return {
        "total_orders": int(total_orders),
        "total_revenue": round(total_revenue, 2),
        "avg_order_value": round(to_float(overview.get("avg_order_value")), 2),
        "sales_days": int(to_float(overview.get("sales_days"))),
        "delayed_shipments": int(delayed_shipments),
        "low_stock_items": int(to_float(overview.get("low_stock_items"))),
        "report_count": report_count,
        "available_module_count": available_modules,
        "delay_rate": round(
            _safe_rate(delayed_shipments, total_orders),
            4,
        ),
    }


def _take_metric_cards(metric_cards: list[dict[str, Any]], max_rows: int) -> list[dict[str, Any]]:
    rows = [item for item in metric_cards if isinstance(item, dict)]
    return rows[:max_rows]


def _scorecard_snapshot(payload: dict[str, Any] | None, max_rows: int) -> dict[str, Any]:
    safe_payload = payload or {}
    pillars = [item for item in safe_payload.get("pillars", []) if isinstance(item, dict)]
    pillars.sort(key=lambda item: to_float(item.get("score")), reverse=True)
    return {
        "summary": dict(safe_payload.get("summary", {})),
        "pillars": pillars[:max_rows],
    }


def _executive_snapshot(payload: dict[str, Any] | None, max_rows: int) -> dict[str, Any]:
    safe_payload = payload or {}
    return {
        "headline": to_text(safe_payload.get("headline")),
        "metric_cards": _take_metric_cards(list(safe_payload.get("metric_cards", [])), max_rows),
        "top_risks": [
            item for item in list(safe_payload.get("top_risks", [])) if isinstance(item, dict)
        ][:max_rows],
        "top_actions": [
            item for item in list(safe_payload.get("top_actions", [])) if isinstance(item, dict)
        ][:max_rows],
        "watchlist_skus": [
            item for item in list(safe_payload.get("watchlist_skus", [])) if isinstance(item, dict)
        ][:max_rows],
    }


def _benchmark_snapshot(payload: dict[str, Any] | None, max_rows: int) -> dict[str, Any]:
    safe_payload = payload or {}
    return {
        "summary": dict(safe_payload.get("summary", {})),
        "store_benchmarks": [
            item
            for item in list(safe_payload.get("store_benchmarks", []))
            if isinstance(item, dict)
        ][:max_rows],
        "category_benchmarks": [
            item
            for item in list(safe_payload.get("category_benchmarks", []))
            if isinstance(item, dict)
        ][:max_rows],
    }


def _report_catalog_snapshot(payload: dict[str, Any] | None) -> dict[str, Any]:
    safe_payload = payload or {}
    report_index = [item for item in safe_payload.get("report_index", []) if isinstance(item, dict)]
    return {
        "artifact_path": to_text(safe_payload.get("artifact_path")),
        "report_count": len(report_index),
        "reports": report_index,
    }


def _endpoint_catalog(
    *,
    upload_id: str,
    report_catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        {
            "category": "workspace",
            "label": "Unified workspace JSON",
            "endpoint": f"/api/v1/dashboard-hub/workspace?upload_id={upload_id}",
        },
        {
            "category": "workspace",
            "label": "Unified workspace HTML",
            "endpoint": _workspace_url(upload_id),
        },
        {
            "category": "workspace",
            "label": "Published workspace artifact",
            "endpoint": f"/api/v1/dashboard-hub/artifact/{upload_id}",
        },
        {
            "category": "analytics",
            "label": "KPI overview",
            "endpoint": f"/api/v1/kpis/overview?upload_id={upload_id}",
        },
        {
            "category": "analytics",
            "label": "Daily sales",
            "endpoint": f"/api/v1/kpis/sales-daily?upload_id={upload_id}",
        },
        {
            "category": "analytics",
            "label": "Revenue by category",
            "endpoint": f"/api/v1/kpis/revenue-by-category?upload_id={upload_id}",
        },
        {
            "category": "analytics",
            "label": "Inventory health",
            "endpoint": f"/api/v1/kpis/inventory-health?upload_id={upload_id}",
        },
        {
            "category": "analytics",
            "label": "Shipment summary",
            "endpoint": f"/api/v1/kpis/shipments?upload_id={upload_id}",
        },
        {
            "category": "reports",
            "label": "Business report catalog",
            "endpoint": f"/api/v1/business-reports/catalog?upload_id={upload_id}",
        },
        {
            "category": "reports",
            "label": "Executive review",
            "endpoint": f"/api/v1/business-reports/executive-review?upload_id={upload_id}",
        },
        {
            "category": "reports",
            "label": "Operating executive scorecard",
            "endpoint": (
                f"/api/v1/business-reports/operating-executive-scorecard?upload_id={upload_id}"
            ),
        },
    ]
    for item in report_catalog.get("reports", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "category": "reports",
                "label": to_text(item.get("report_name")),
                "endpoint": to_text(item.get("endpoint")),
            }
        )
    return rows


def _action_center(
    *,
    executive_review: dict[str, Any],
    scorecard: dict[str, Any],
    module_status: list[dict[str, Any]],
    max_rows: int,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in executive_review.get("top_actions", []):
        if not isinstance(item, dict):
            continue
        actions.append(
            {
                "title": to_text(item.get("title")),
                "owner": to_text(item.get("owner")) or "operations",
                "source": "executive_review",
                "rationale": to_text(item.get("expected_outcome")),
            }
        )
    pillars = [item for item in scorecard.get("pillars", []) if isinstance(item, dict)]
    pillars.sort(key=lambda item: to_float(item.get("gap_to_target")), reverse=True)
    for item in pillars[:max_rows]:
        actions.append(
            {
                "title": f"Close gap for {to_text(item.get('pillar_name'))}",
                "owner": "executive-team",
                "source": "operating_scorecard",
                "rationale": to_text(item.get("recommended_action")),
            }
        )
    for module in module_status:
        if module.get("status") != "available":
            continue
        rows = [item for item in module.get("highlight_rows", []) if isinstance(item, dict)]
        if not rows:
            continue
        actions.append(
            {
                "title": f"Review {to_text(module.get('title'))}",
                "owner": "operations",
                "source": to_text(module.get("module_key")),
                "rationale": to_text(module.get("recommended_action")),
            }
        )
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in actions:
        key = item["title"].strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[: max_rows * 2]


def build_dashboard_workspace(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_root: Path,
    refresh: bool = False,
    max_rows: int = 8,
) -> dict[str, Any]:
    dirs = _artifact_dirs(artifact_root)
    transform_summary = load_transform_summary_from_upload(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
    )
    overview = build_overview(transform_summary)
    sales_daily = build_sales_daily(transform_summary)
    revenue_by_category = build_revenue_by_category(transform_summary)
    inventory_health = build_inventory_health(transform_summary)
    shipment_summary = build_shipment_summary(transform_summary)

    forecast_payload, forecast_error = _call_module(
        get_or_create_batch_forecast_artifact,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["forecast"],
        refresh=refresh,
    )
    stockout_payload, stockout_error = _call_module(
        get_or_create_stockout_artifact,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["stockout"],
        refresh=refresh,
    )
    reorder_payload, reorder_error = _call_module(
        get_or_create_reorder_artifact,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=dirs["forecast"],
        stockout_artifact_dir=dirs["stockout"],
        artifact_dir=dirs["reorder"],
        refresh=refresh,
    )
    returns_payload, returns_error = _call_module(
        get_or_create_returns_artifact,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["returns"],
        refresh=refresh,
    )
    shipment_payload, shipment_error = _call_module(
        get_open_order_predictions,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["shipment"],
        refresh=refresh,
        limit=max_rows,
    )
    report_catalog_payload, report_catalog_error = _call_module(
        get_business_report_catalog,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["business"],
        refresh=refresh,
    )
    executive_review_payload, executive_review_error = _call_module(
        get_executive_business_review,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["business"],
        refresh=refresh,
    )
    scorecard_payload, scorecard_error = _call_module(
        get_operating_executive_scorecard,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["business"],
        refresh=refresh,
    )
    benchmark_payload, benchmark_error = _call_module(
        get_internal_benchmarking_report,
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=dirs["business"],
        refresh=refresh,
        limit=max_rows,
    )

    module_status = [
        _forecast_module(forecast_payload, forecast_error, max_rows),
        _stockout_module(stockout_payload, stockout_error, max_rows),
        _reorder_module(reorder_payload, reorder_error, max_rows),
        _returns_module(returns_payload, returns_error, max_rows),
        _shipment_module(shipment_payload, shipment_error, max_rows),
    ]
    report_catalog = _report_catalog_snapshot(report_catalog_payload)
    executive_review = _executive_snapshot(executive_review_payload, max_rows)
    scorecard = _scorecard_snapshot(scorecard_payload, max_rows)
    benchmarking = _benchmark_snapshot(benchmark_payload, max_rows)

    available_count = sum(1 for item in module_status if item["status"] == "available")
    warnings = [
        f"{item['title']}: {item['error']}"
        for item in module_status
        if item["status"] != "available"
    ]
    extra_warnings = [
        ("Business report catalog", report_catalog_error),
        ("Executive review", executive_review_error),
        ("Operating executive scorecard", scorecard_error),
        ("Benchmarking", benchmark_error),
    ]
    warnings.extend(f"{label}: {message}" for label, message in extra_warnings if message)
    endpoint_catalog = _endpoint_catalog(
        upload_id=upload_id,
        report_catalog=report_catalog,
    )
    payload = {
        "upload_id": upload_id,
        "generated_at": utc_now_iso(),
        "refresh_used": refresh,
        "workspace_title": "RetailOps Professional Dashboard Workspace",
        "workspace_version": WORKSPACE_VERSION,
        "workspace_url": _workspace_url(upload_id),
        "artifact_root": str(artifact_root.resolve()),
        "report_count": int(report_catalog["report_count"]),
        "available_module_count": available_count,
        "unavailable_module_count": max(len(module_status) - available_count, 0),
        "overview": _overview_cards(
            overview,
            int(report_catalog["report_count"]),
            available_count,
        ),
        "charts": {
            "sales_daily": sales_daily,
            "revenue_by_category": revenue_by_category,
            "inventory_health": inventory_health[:max_rows],
            "shipment_summary": shipment_summary,
            "benchmarking": benchmarking,
        },
        "scorecard_summary": scorecard,
        "executive_review": executive_review,
        "module_status": module_status,
        "action_center": _action_center(
            executive_review=executive_review,
            scorecard=scorecard,
            module_status=module_status,
            max_rows=max_rows,
        ),
        "report_catalog": report_catalog,
        "endpoint_catalog": endpoint_catalog,
        "warnings": warnings,
    }
    return payload


def _render_bar_rows(
    *,
    rows: list[dict[str, Any]],
    label_key: str,
    value_key: str,
    title: str,
    max_rows: int,
) -> str:
    safe_rows = [item for item in rows if isinstance(item, dict)][:max_rows]
    if not safe_rows:
        return (
            "<section class='panel'><h2>"
            + html.escape(title)
            + "</h2><p>No data available.</p></section>"
        )
    max_value = max(to_float(item.get(value_key)) for item in safe_rows) or 1.0
    parts = [f"<section class='panel'><h2>{html.escape(title)}</h2>"]
    for item in safe_rows:
        label = html.escape(to_text(item.get(label_key)) or "unknown")
        value = round(to_float(item.get(value_key)), 2)
        width = max(4.0, (value / max_value) * 100.0)
        parts.append(
            "<div class='bar-row'>"
            f"<div class='bar-label'>{label}</div>"
            "<div class='bar-wrap'><div class='bar-fill' "
            f"style='width:{width:.1f}%'></div></div>"
            f"<div class='bar-value'>{html.escape(str(value))}</div>"
            "</div>"
        )
    parts.append("</section>")
    return "".join(parts)


def _render_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    empty_message: str,
    max_rows: int,
) -> str:
    safe_rows = [item for item in rows if isinstance(item, dict)][:max_rows]
    if not safe_rows:
        return (
            "<section class='panel'><h2>"
            + html.escape(title)
            + "</h2><p>"
            + html.escape(empty_message)
            + "</p></section>"
        )
    headers = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_rows: list[str] = []
    for row in safe_rows:
        cells = "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key, _ in columns)
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        f"<section class='panel'><h2>{html.escape(title)}</h2>"
        f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
        "</section>"
    )


def render_dashboard_workspace_html(workspace: dict[str, Any]) -> str:
    overview = dict(workspace.get("overview", {}))
    executive_review = dict(workspace.get("executive_review", {}))
    scorecard = dict(workspace.get("scorecard_summary", {}))
    charts = dict(workspace.get("charts", {}))
    module_status = [item for item in workspace.get("module_status", []) if isinstance(item, dict)]
    warnings = [to_text(item) for item in workspace.get("warnings", []) if to_text(item)]
    action_center = [item for item in workspace.get("action_center", []) if isinstance(item, dict)]
    report_catalog = dict(workspace.get("report_catalog", {}))
    endpoint_catalog = [
        item for item in workspace.get("endpoint_catalog", []) if isinstance(item, dict)
    ]

    css = "\n".join(
        [
            "body { font-family: Arial, sans-serif; margin: 0; "
            "background: #f8fafc; color: #0f172a; }",
            ".shell { max-width: 1320px; margin: 0 auto; padding: 1.5rem; }",
            ".hero { background: linear-gradient(135deg, #0f172a, #1d4ed8); "
            "color: white; border-radius: 22px; padding: 1.5rem; "
            "margin-bottom: 1rem; }",
            ".hero p { color: #dbeafe; }",
            ".stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); "
            "gap: 0.9rem; margin-top: 1rem; }",
            ".card, .panel { background: white; border: 1px solid #dbe4ee; "
            "border-radius: 18px; padding: 1rem 1.1rem; box-shadow: 0 8px 30px "
            "rgba(15, 23, 42, 0.06); }",
            ".card strong { font-size: 1.5rem; display: block; margin-top: 0.25rem; }",
            ".grid-2 { display: grid; grid-template-columns: 1.4fr 1fr; gap: 1rem; "
            "margin-bottom: 1rem; }",
            ".grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); "
            "gap: 1rem; margin-bottom: 1rem; }",
            ".chips { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.75rem; }",
            ".chip { background: #eff6ff; color: #1d4ed8; border-radius: 999px; "
            "padding: 0.22rem 0.65rem; font-size: 0.86rem; }",
            ".warning { background: #fff7ed; color: #9a3412; border: 1px solid "
            "#fdba74; border-radius: 14px; padding: 0.75rem 0.9rem; "
            "margin-bottom: 0.75rem; }",
            ".section-title { margin: 1.2rem 0 0.6rem; }",
            ".bar-row { display: grid; grid-template-columns: 180px 1fr 90px; gap: "
            "0.75rem; align-items: center; margin-bottom: 0.55rem; }",
            ".bar-label, .bar-value { font-size: 0.92rem; }",
            ".bar-wrap { height: 12px; background: #e2e8f0; border-radius: 999px; "
            "overflow: hidden; }",
            ".bar-fill { height: 100%; background: #2563eb; border-radius: 999px; }",
            "table { width: 100%; border-collapse: collapse; margin-top: 0.75rem; }",
            "th, td { border: 1px solid #e2e8f0; padding: 0.55rem; text-align: "
            "left; vertical-align: top; font-size: 0.92rem; }",
            "th { background: #f8fafc; }",
            ".module-ok { color: #166534; }",
            ".module-missing { color: #991b1b; }",
            "ul.clean { margin: 0.4rem 0 0; padding-left: 1.1rem; }",
            "a { color: #1d4ed8; text-decoration: none; }",
            "@media (max-width: 1100px) { .stats, .grid-2, .grid-3 { "
            "grid-template-columns: 1fr; } .bar-row { grid-template-columns: "
            "1fr; } }",
        ]
    )

    stat_cards = [
        ("Total orders", overview.get("total_orders", 0)),
        ("Total revenue", overview.get("total_revenue", 0)),
        ("Available modules", overview.get("available_module_count", 0)),
        ("Report count", overview.get("report_count", 0)),
    ]
    stat_html = "".join(
        (
            "<div class='card'><span>"
            + html.escape(label)
            + "</span><strong>"
            + html.escape(str(value))
            + "</strong></div>"
        )
        for label, value in stat_cards
    )

    warning_html = "".join(f"<div class='warning'>{html.escape(item)}</div>" for item in warnings)
    risk_items = "".join(
        "<li><strong>"
        + html.escape(to_text(item.get("title")))
        + "</strong> — "
        + html.escape(to_text(item.get("recommended_action") or item.get("rationale")))
        + "</li>"
        for item in executive_review.get("top_risks", [])
        if isinstance(item, dict)
    )
    action_items = "".join(
        "<li><strong>"
        + html.escape(to_text(item.get("title")))
        + "</strong> — "
        + html.escape(to_text(item.get("owner")))
        + ": "
        + html.escape(to_text(item.get("rationale") or item.get("expected_outcome")))
        + "</li>"
        for item in action_center
    )
    module_rows = []
    for item in module_status:
        status = to_text(item.get("status"))
        status_class = "module-ok" if status == "available" else "module-missing"
        summary = dict(item.get("summary", {}))
        summary_text = ", ".join(f"{key}: {summary[key]}" for key in list(summary)[:4])
        module_rows.append(
            "<tr>"
            f"<td>{html.escape(to_text(item.get('title')))}</td>"
            f"<td class='{status_class}'>{html.escape(status)}</td>"
            f"<td>{html.escape(summary_text)}</td>"
            f"<td>{html.escape(to_text(item.get('recommended_action')))}</td>"
            "</tr>"
        )

    html_page = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{html.escape(to_text(workspace.get('workspace_title')))}</title>"
        f"<style>{css}</style></head><body><div class='shell'>"
        "<section class='hero'>"
        f"<h1>{html.escape(to_text(workspace.get('workspace_title')))}</h1>"
        f"<p>Upload ID: <strong>{html.escape(to_text(workspace.get('upload_id')))}</strong></p>"
        f"<p>{html.escape(to_text(executive_review.get('headline')))}</p>"
        f"<div class='stats'>{stat_html}</div>"
        "</section>"
        f"{warning_html}"
        "<div class='grid-2'>"
        "<section class='panel'>"
        "<h2>Operating scorecard</h2>"
        + _render_table(
            title="Scorecard pillars",
            rows=list(scorecard.get("pillars", [])),
            columns=[
                ("pillar_name", "Pillar"),
                ("score", "Score"),
                ("target_score", "Target"),
                ("gap_to_target", "Gap"),
                ("recommended_action", "Recommended action"),
            ],
            empty_message="No scorecard data is available.",
            max_rows=8,
        )
        + "</section>"
        "<section class='panel'>"
        "<h2>Leadership actions</h2>"
        f"<ul class='clean'>{action_items or '<li>No action items were generated.</li>'}</ul>"
        "<h2 class='section-title'>Top risks</h2>"
        f"<ul class='clean'>{risk_items or '<li>No risks were generated.</li>'}</ul>"
        "</section>"
        "</div>"
        "<div class='grid-3'>"
        + _render_bar_rows(
            rows=list(charts.get("sales_daily", [])),
            label_key="sales_date",
            value_key="revenue",
            title="Daily revenue trend",
            max_rows=10,
        )
        + _render_bar_rows(
            rows=list(charts.get("revenue_by_category", [])),
            label_key="category",
            value_key="revenue",
            title="Revenue by category",
            max_rows=8,
        )
        + _render_table(
            title="Inventory health",
            rows=list(charts.get("inventory_health", [])),
            columns=[
                ("sku", "SKU"),
                ("on_hand", "On hand"),
                ("days_of_cover", "Days of cover"),
                ("low_stock", "Low stock"),
            ],
            empty_message="No inventory health rows are available.",
            max_rows=8,
        )
        + "</div>"
        + _render_table(
            title="Operational module status",
            rows=module_status,
            columns=[
                ("title", "Module"),
                ("status", "Status"),
                ("recommended_action", "Recommended action"),
                ("error", "Error"),
            ],
            empty_message="No module status rows are available.",
            max_rows=10,
        )
        + _render_table(
            title="Operational module highlights",
            rows=[
                {
                    "module": to_text(module.get("title")),
                    "highlights": json.dumps(
                        module.get("highlight_rows", []),
                        ensure_ascii=False,
                    )[:350],
                }
                for module in module_status
            ],
            columns=[("module", "Module"), ("highlights", "Highlights")],
            empty_message="No highlight rows are available.",
            max_rows=10,
        )
        + _render_table(
            title="Business report catalog",
            rows=list(report_catalog.get("reports", [])),
            columns=[("report_name", "Report"), ("endpoint", "Endpoint")],
            empty_message="No reports were found.",
            max_rows=50,
        )
        + _render_table(
            title="Endpoint catalog",
            rows=endpoint_catalog,
            columns=[("category", "Category"), ("label", "Label"), ("endpoint", "Endpoint")],
            empty_message="No endpoints were found.",
            max_rows=80,
        )
        + "</div></body></html>"
    )
    return html_page


def publish_dashboard_workspace(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_root: Path,
    refresh: bool = False,
    max_rows: int = 8,
) -> dict[str, Any]:
    workspace = build_dashboard_workspace(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_root=artifact_root,
        refresh=refresh,
        max_rows=max_rows,
    )
    artifact_path = _artifact_path(artifact_root, upload_id)
    html_artifact_path = _html_artifact_path(artifact_root, upload_id)
    write_json(artifact_path, workspace)
    html_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    html_artifact_path.write_text(
        render_dashboard_workspace_html(workspace),
        encoding="utf-8",
    )
    return {
        "upload_id": upload_id,
        "artifact_path": str(artifact_path.resolve()),
        "html_artifact_path": str(html_artifact_path.resolve()),
        "workspace_url": _workspace_url(upload_id),
        "workspace": workspace,
    }


def load_dashboard_workspace_artifact(*, upload_id: str, artifact_root: Path) -> dict[str, Any]:
    artifact_path = _artifact_path(artifact_root, upload_id)
    if not artifact_path.exists():
        raise FileNotFoundError("Dashboard workspace artifact was not found. Publish it first.")
    workspace = json.loads(artifact_path.read_text(encoding="utf-8"))
    return {
        "upload_id": upload_id,
        "artifact_path": str(artifact_path.resolve()),
        "html_artifact_path": str(_html_artifact_path(artifact_root, upload_id).resolve()),
        "workspace_url": _workspace_url(upload_id),
        "workspace": workspace,
    }
