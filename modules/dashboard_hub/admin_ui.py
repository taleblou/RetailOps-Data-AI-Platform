# Project:      RetailOps Data & AI Platform
# Module:       modules.dashboard_hub
# File:         admin_ui.py
# Path:         modules/dashboard_hub/admin_ui.py
#
# Summary:      Renders the separated dashboard UI pages.
# Purpose:      Builds a chart-rich admin dashboard under /dashboard without
#               changing the existing API endpoints.
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

from __future__ import annotations

import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml
from fastapi.routing import APIRoute

from config.settings import get_settings
from core.api.error_logging import error_log_css, render_error_log_panel
from modules.common.upload_utils import to_float, to_text

PAGE_REGISTRY: list[tuple[str, str, str]] = [
    ("overview", "Overview", "Executive landing page for the full workspace."),
    (
        "ingestion",
        "Ingestion & Easy CSV",
        "Upload, mapping, validation, import, transform, and first dashboard flow.",
    ),
    (
        "executive",
        "Executive Command",
        "Leadership scorecards, risks, actions, and benchmark snapshots.",
    ),
    (
        "operations",
        "Operational Analytics",
        "Forecasting, stockout, reorder, returns, shipment, and inventory signals.",
    ),
    (
        "intelligence",
        "Intelligence Modules",
        "Merchandising, customer, profitability, anomaly, and supplier intelligence.",
    ),
    (
        "reports",
        "Report Directory",
        "All reporting families, report inventory, and quick launch links.",
    ),
    (
        "apis",
        "API Directory",
        "Full API surface grouped by router prefix and route methods.",
    ),
    (
        "capabilities",
        "Capability Map",
        "Everything the project ships, grouped by business capability.",
    ),
    (
        "platform",
        "Platform Control",
        "Connectors, optional extras, platform extensions, and readiness summaries.",
    ),
    (
        "runtime",
        "Runtime Without Services",
        "What is already available from files and generated artifacts only.",
    ),
    (
        "services",
        "Service Directory",
        "Configured local services, overlays, ports, and quick-open links.",
    ),
]
PAGE_KEYS = {item[0] for item in PAGE_REGISTRY}

GROUPED_CAPABILITIES: list[dict[str, Any]] = [
    {
        "group": "Ingestion & setup",
        "items": [
            ("Easy CSV wizard", "/easy-csv/wizard"),
            ("Source management", "/sources"),
            ("Platform setup", "/setup"),
        ],
    },
    {
        "group": "KPI analytics",
        "items": [
            ("KPI overview", "/api/v1/kpis/overview"),
            ("Daily sales", "/api/v1/kpis/sales-daily"),
            ("Revenue by category", "/api/v1/kpis/revenue-by-category"),
            ("Inventory health", "/api/v1/kpis/inventory-health"),
            ("Shipment summary", "/api/v1/kpis/shipments"),
        ],
    },
    {
        "group": "Operational decisions",
        "items": [
            ("Forecasting", "/api/v1/forecasting/batch"),
            ("Stockout intelligence", "/api/v1/stockout/predictions"),
            ("Reorder engine", "/api/v1/reorder/recommendations"),
            ("Returns intelligence", "/api/v1/returns/scores"),
            ("Shipment risk", "/api/v1/shipment-risk/open-orders"),
        ],
    },
    {
        "group": "Intelligence modules",
        "items": [
            ("ABC XYZ intelligence", "/api/v1/abc-xyz"),
            ("Assortment intelligence", "/api/v1/assortment"),
            ("Basket affinity intelligence", "/api/v1/basket-affinity"),
            ("Customer churn intelligence", "/api/v1/customer-churn"),
            ("Customer cohort intelligence", "/api/v1/customer-cohorts"),
            ("Customer intelligence", "/api/v1/customer-intelligence"),
            ("Fulfillment SLA intelligence", "/api/v1/fulfillment-sla"),
            ("Inventory aging intelligence", "/api/v1/inventory-aging"),
            ("Payment reconciliation", "/api/v1/payment-reconciliation"),
            ("Profitability intelligence", "/api/v1/profitability"),
            ("Promotion pricing intelligence", "/api/v1/promotion-pricing"),
            ("Sales anomaly intelligence", "/api/v1/sales-anomalies"),
            ("Seasonality intelligence", "/api/v1/seasonality"),
            ("Supplier procurement intelligence", "/api/v1/supplier-procurement"),
        ],
    },
    {
        "group": "Business reporting",
        "items": [
            ("Business report catalog", "/api/v1/business-reports/catalog"),
            ("Executive review", "/api/v1/business-reports/executive-review"),
            (
                "Operating executive scorecard",
                "/api/v1/business-reports/operating-executive-scorecard",
            ),
            ("Decision intelligence", "/api/v1/business-reports"),
        ],
    },
    {
        "group": "Platform extensions",
        "items": [
            ("ML registry", "/api/v1/ml-registry"),
            ("Serving", "/api/v1/serving"),
            ("Monitoring", "/api/v1/monitoring"),
            ("CDC", "/api/v1/cdc"),
            ("Streaming", "/api/v1/streaming"),
            ("Lakehouse", "/api/v1/lakehouse"),
            ("Query layer", "/api/v1/query-layer"),
            ("Metadata", "/api/v1/metadata"),
            ("Feature store", "/api/v1/feature-store"),
            ("Advanced serving", "/api/v1/advanced-serving"),
            ("Pro platform", "/api/v1/pro-platform"),
        ],
    },
]

SAMPLE_MODULE_PAYLOADS: dict[str, dict[str, Any]] = {
    "forecasting": {
        "summary": {
            "coverage_ratio": 0.94,
            "products_scored": 12,
            "selected_model_family": "ensemble_blend",
            "sample_mode": True,
        },
        "rows": [
            {
                "product_id": "SKU-001",
                "category": "electronics",
                "selected_model": "ensemble_blend",
                "demand_30d": 84.0,
                "latest_inventory_units": 18.0,
            },
            {
                "product_id": "SKU-004",
                "category": "beauty",
                "selected_model": "seasonal_xgb",
                "demand_30d": 62.0,
                "latest_inventory_units": 14.0,
            },
            {
                "product_id": "SKU-006",
                "category": "home",
                "selected_model": "baseline_plus",
                "demand_30d": 54.0,
                "latest_inventory_units": 36.0,
            },
        ],
    },
    "reorder_engine": {
        "summary": {
            "urgent_recommendations": 4,
            "reorder_value": 5840.0,
            "sample_mode": True,
        },
        "rows": [
            {"sku": "SKU-001", "urgency_score": 0.91, "reorder_quantity": 34.0},
            {"sku": "SKU-004", "urgency_score": 0.77, "reorder_quantity": 26.0},
            {"sku": "SKU-008", "urgency_score": 0.63, "reorder_quantity": 18.0},
        ],
    },
    "shipment_risk": {
        "summary": {
            "open_orders": 7,
            "orders_at_risk": 3,
            "sample_mode": True,
        },
        "rows": [
            {"order_id": "A-1001", "probability": 0.81, "inventory_lag_days": 5.0},
            {"order_id": "A-1007", "probability": 0.66, "inventory_lag_days": 3.0},
            {"order_id": "A-1014", "probability": 0.54, "inventory_lag_days": 2.0},
        ],
    },
    "stockout_intelligence": {
        "summary": {
            "critical_skus": 3,
            "portfolio_risk_value": 2100.0,
            "sample_mode": True,
        },
        "rows": [
            {"sku": "SKU-001", "stockout_probability": 0.88, "days_to_stockout": 3.0},
            {"sku": "SKU-005", "stockout_probability": 0.71, "days_to_stockout": 5.0},
            {"sku": "SKU-010", "stockout_probability": 0.48, "days_to_stockout": 8.0},
        ],
    },
    "returns_intelligence": {
        "summary": {
            "orders_scored": 16,
            "expected_return_cost": 920.0,
            "sample_mode": True,
        },
        "rows": [
            {"order_id": "R-1004", "return_probability": 0.62, "expected_return_cost": 210.0},
            {"order_id": "R-1011", "return_probability": 0.51, "expected_return_cost": 166.0},
            {"order_id": "R-1013", "return_probability": 0.42, "expected_return_cost": 132.0},
        ],
    },
}


def _escape(value: Any) -> str:
    return html.escape(to_text(value))


def _fmt_number(value: Any) -> str:
    number = to_float(value)
    if abs(number) >= 1000:
        return f"{number:,.0f}"
    if abs(number) >= 100:
        return f"{number:,.1f}"
    return f"{number:,.2f}".rstrip("0").rstrip(".")


def _fmt_percent(value: Any) -> str:
    number = to_float(value)
    if number <= 1.0:
        number *= 100.0
    return f"{number:.1f}%"


def _card(title: str, body: str, subtitle: str = "") -> str:
    subtitle_html = f"<p class='card-subtitle'>{_escape(subtitle)}</p>" if subtitle else ""
    return (
        "<section class='card panel-card'>"
        f"<div class='card-head'><h3>{_escape(title)}</h3>{subtitle_html}</div>"
        f"<div class='card-body'>{body}</div>"
        "</section>"
    )


def _kpi_cards(items: list[tuple[str, Any, str]]) -> str:
    cards = []
    for label, value, note in items:
        cards.append(
            "<div class='kpi-card'>"
            f"<span class='kpi-label'>{_escape(label)}</span>"
            f"<strong class='kpi-value'>{_escape(value)}</strong>"
            f"<span class='kpi-note'>{_escape(note)}</span>"
            "</div>"
        )
    return "<div class='kpi-grid'>" + "".join(cards) + "</div>"


def _progress_card(title: str, value: float, total: float, note: str) -> str:
    total = max(total, 1.0)
    ratio = min(max(value / total, 0.0), 1.0)
    circ = 2 * math.pi * 52
    offset = circ * (1.0 - ratio)
    body = (
        "<div class='ring-wrap'>"
        "<svg class='ring' viewBox='0 0 140 140'>"
        "<circle cx='70' cy='70' r='52' class='ring-track'></circle>"
        f"<circle cx='70' cy='70' r='52' class='ring-fill' style='stroke-dasharray:{circ:.2f};"
        f"stroke-dashoffset:{offset:.2f}'></circle>"
        f"<text x='70' y='68' text-anchor='middle' class='ring-value'>{_escape(_fmt_percent(ratio))}</text>"
        f"<text x='70' y='88' text-anchor='middle' class='ring-note'>{_escape(_fmt_number(value))}</text>"
        "</svg>"
        f"<p class='chart-caption'>{_escape(note)}</p>"
        "</div>"
    )
    return _card(title, body)


def _svg_bar_chart(
    title: str,
    rows: list[dict[str, Any]],
    label_key: str,
    value_key: str,
    color_class: str = "accent",
) -> str:
    clean = [item for item in rows if isinstance(item, dict)]
    if not clean:
        return _card(title, "<p>No data available.</p>")
    values = [max(to_float(item.get(value_key)), 0.0) for item in clean[:8]]
    labels = [to_text(item.get(label_key)) or "n/a" for item in clean[:8]]
    max_value = max(values) or 1.0
    bar_width = 50
    gap = 22
    base_y = 230
    height = 180
    parts = ["<svg class='chart-svg' viewBox='0 0 520 280'>"]
    parts.append("<line x1='24' y1='230' x2='500' y2='230' class='axis'></line>")
    for idx, value in enumerate(values):
        x = 36 + idx * (bar_width + gap)
        bar_height = (value / max_value) * height
        y = base_y - bar_height
        label = _escape(labels[idx][:12])
        parts.append(
            f"<rect x='{x}' y='{y:.2f}' width='{bar_width}' height='{bar_height:.2f}' "
            f"class='bar-{color_class}' rx='10'></rect>"
        )
        parts.append(
            f"<text x='{x + bar_width / 2:.1f}' y='250' text-anchor='middle' "
            f"class='axis-text'>{label}</text>"
        )
        parts.append(
            f"<text x='{x + bar_width / 2:.1f}' y='{max(y - 8, 14):.1f}' text-anchor='middle' "
            f"class='value-text'>{_escape(_fmt_number(value))}</text>"
        )
    parts.append("</svg>")
    return _card(title, "".join(parts))


def _svg_line_chart(title: str, rows: list[dict[str, Any]], label_key: str, value_key: str) -> str:
    clean = [item for item in rows if isinstance(item, dict)]
    if not clean:
        return _card(title, "<p>No data available.</p>")
    values = [max(to_float(item.get(value_key)), 0.0) for item in clean[:10]]
    labels = [to_text(item.get(label_key)) or "n/a" for item in clean[:10]]
    max_value = max(values) or 1.0
    min_value = min(values) if values else 0.0
    span = max(max_value - min_value, 1.0)
    points: list[str] = []
    dots: list[str] = []
    for idx, value in enumerate(values):
        x = 50 + idx * 45
        y = 220 - ((value - min_value) / span) * 150
        points.append(f"{x:.1f},{y:.1f}")
        dots.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4.5' class='line-dot'></circle>"
            f"<text x='{x:.1f}' y='{max(y - 10, 16):.1f}' text-anchor='middle' class='value-text'>"
            f"{_escape(_fmt_number(value))}</text>"
            f"<text x='{x:.1f}' y='250' text-anchor='middle' class='axis-text'>{_escape(labels[idx][:10])}</text>"
        )
    path = " ".join(points)
    body = (
        "<svg class='chart-svg' viewBox='0 0 520 280'>"
        "<line x1='36' y1='220' x2='500' y2='220' class='axis'></line>"
        f"<polyline points='{path}' class='line-path'></polyline>" + "".join(dots) + "</svg>"
    )
    return _card(title, body)


def _mini_table(
    title: str,
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    table_id: str,
    filterable: bool = False,
    empty_message: str = "No rows available.",
) -> str:
    clean = [item for item in rows if isinstance(item, dict)]
    search = ""
    if filterable:
        search = (
            "<div class='table-tools'>"
            f"<input type='search' placeholder='Filter rows' oninput=\"filterTable('{table_id}', this.value)\">"
            "</div>"
        )
    if not clean:
        return _card(title, search + f"<p>{_escape(empty_message)}</p>")
    head = "".join(f"<th>{_escape(label)}</th>" for _, label in columns)
    body_rows: list[str] = []
    for row in clean:
        tds = []
        for key, _label in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                rendered = _fmt_number(value)
            else:
                rendered = to_text(value)
            tds.append(f"<td>{_escape(rendered)}</td>")
        body_rows.append("<tr>" + "".join(tds) + "</tr>")
    table = (
        f"<table id='{table_id}' class='data-table'><thead><tr>{head}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table>"
    )
    return _card(title, search + table)


def _status_pill(label: str, status: str) -> str:
    css = "pill-ok" if status in {"available", "ready", "present"} else "pill-warn"
    return f"<span class='pill {css}'>{_escape(label)}: {_escape(status)}</span>"


def _module_payload(module: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    key = to_text(module.get("module_key"))
    rows = [item for item in module.get("highlight_rows", []) if isinstance(item, dict)]
    summary = dict(module.get("summary", {}))
    if rows:
        return summary, rows, False
    sample = SAMPLE_MODULE_PAYLOADS.get(key)
    if sample is not None:
        return dict(sample.get("summary", {})), list(sample.get("rows", [])), True
    return summary, rows, False


def _module_metric_keys(module_key: str) -> tuple[str, str]:
    mapping = {
        "forecasting": ("product_id", "demand_30d"),
        "stockout_intelligence": ("sku", "stockout_probability"),
        "reorder_engine": ("sku", "reorder_quantity"),
        "returns_intelligence": ("order_id", "expected_return_cost"),
        "shipment_risk": ("order_id", "probability"),
    }
    return mapping.get(module_key, ("label", "value"))


def _module_panel(module: dict[str, Any], index: int) -> str:
    summary, rows, sample_used = _module_payload(module)
    key = to_text(module.get("module_key"))
    label_key, value_key = _module_metric_keys(key)
    status = to_text(module.get("status"))
    if sample_used:
        status = "sample"
    pills = [
        _status_pill("Mode", status),
        _status_pill("Rows", str(len(rows)) or "0"),
    ]
    for item_key in list(summary)[:3]:
        pills.append(
            f"<span class='pill pill-neutral'>{_escape(item_key)}: {_escape(summary[item_key])}</span>"
        )
    chart = _svg_bar_chart(module.get("title") or key, rows, label_key, value_key, "accent")
    summary_html = (
        "<div class='pill-row'>" + "".join(pills) + "</div>"
        f"<p class='chart-caption'>{_escape(module.get('recommended_action'))}</p>"
    )
    table = _mini_table(
        "Detail rows",
        rows,
        [
            (label_key, label_key.replace("_", " ").title()),
            (value_key, value_key.replace("_", " ").title()),
        ],
        table_id=f"module-table-{index}",
    )
    return (
        "<section class='module-stack'>"
        f"<div class='module-summary'>{summary_html}</div>{chart}{table}</section>"
    )


def _report_family(report_name: str) -> str:
    value = report_name.lower()
    rules = [
        ("executive", ["executive", "clearance", "demand_supply", "cash_conversion"]),
        ("commercial", ["promotion", "supplier", "cohort", "returns_profit"]),
        (
            "portfolio",
            ["portfolio", "assortment", "payment", "basket", "churn", "seasonality", "value"],
        ),
        (
            "working_capital",
            ["inventory_investment", "forecast_quality", "replenishment", "revenue_root"],
        ),
        ("governance", ["anomaly", "control_tower", "governance", "pipeline"]),
        ("decision", ["scenario", "playbook", "cross_module", "board_style"]),
    ]
    for label, parts in rules:
        if any(part in value for part in parts):
            return label
    return "core"


def _report_family_rows(report_catalog: dict[str, Any]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for item in report_catalog.get("reports", []):
        if not isinstance(item, dict):
            continue
        counter[_report_family(to_text(item.get("report_name")))] += 1
    return [
        {"family": family.replace("_", " ").title(), "count": count}
        for family, count in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))
    ]


def _router_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from core.api.main import ROUTER_PATHS, _load_router

    routers: list[dict[str, Any]] = []
    endpoints: list[dict[str, Any]] = []
    for path in ROUTER_PATHS:
        router = _load_router(path)
        if router is None:
            continue
        prefix = to_text(getattr(router, "prefix", "")) or "/"
        tag = to_text((getattr(router, "tags", []) or [path])[0])
        route_count = 0
        for route in getattr(router, "routes", []):
            if not isinstance(route, APIRoute):
                continue
            methods = ", ".join(sorted(m for m in route.methods if m not in {"HEAD", "OPTIONS"}))
            endpoints.append(
                {
                    "tag": tag,
                    "prefix": prefix,
                    "methods": methods,
                    "path": route.path,
                    "name": route.name,
                }
            )
            route_count += 1
        routers.append(
            {
                "tag": tag,
                "prefix": prefix,
                "route_count": route_count,
                "module_path": path.split(":", 1)[0],
            }
        )
    routers.sort(key=lambda item: item["prefix"])
    endpoints.sort(key=lambda item: (item["prefix"], item["path"], item["methods"]))
    return routers, endpoints


def _compose_service_rows(project_root: Path) -> list[dict[str, Any]]:
    compose_dir = project_root / "compose"
    rows: list[dict[str, Any]] = []
    if not compose_dir.exists():
        return rows
    for path in sorted(compose_dir.glob("compose*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        services = data.get("services", {}) or {}
        for name, payload in services.items():
            ports = payload.get("ports", []) or []
            links: list[str] = []
            primary_port = ""
            for item in ports:
                text = to_text(item)
                host_port = text.split(":", 1)[0] if ":" in text else text
                if host_port.isdigit():
                    primary_port = primary_port or host_port
                    links.append(f"http://127.0.0.1:{host_port}")
            rows.append(
                {
                    "compose_file": path.name,
                    "service": name,
                    "image": to_text(payload.get("image") or payload.get("build") or ""),
                    "ports": ", ".join(to_text(item) for item in ports) or "-",
                    "primary_port": primary_port or "-",
                    "links": links,
                }
            )
    return rows


def _runtime_rows(
    project_root: Path,
    upload_id: str,
    workspace: dict[str, Any],
) -> list[dict[str, Any]]:
    files = [
        ("Upload metadata", project_root / "data" / "uploads" / f"{upload_id}.json"),
        (
            "Source CSV",
            project_root / "data" / "uploads" / f"{upload_id}_sample_orders_easy_csv_150.csv",
        ),
        (
            "Dashboard workspace JSON",
            project_root
            / "data"
            / "artifacts"
            / "dashboard_hub"
            / f"{upload_id}_dashboard_workspace.json",
        ),
        (
            "Dashboard workspace HTML",
            project_root
            / "data"
            / "artifacts"
            / "dashboard_hub"
            / f"{upload_id}_dashboard_workspace.html",
        ),
    ]
    metadata_path = project_root / "data" / "uploads" / f"{upload_id}.json"
    transform_path = forecast_path = starter_dashboard_path = ""
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        transform_path = to_text((metadata.get("transform_summary") or {}).get("artifact_path"))
        forecast_path = to_text((metadata.get("forecast_summary") or {}).get("artifact_path"))
        starter_dashboard_path = to_text(
            (metadata.get("dashboard_summary") or {}).get("artifact_path")
        )
    for label, raw_path in [
        ("Transform summary", Path(transform_path) if transform_path else None),
        ("Forecast summary", Path(forecast_path) if forecast_path else None),
        ("Starter dashboard", Path(starter_dashboard_path) if starter_dashboard_path else None),
    ]:
        if raw_path is not None:
            files.append((label, raw_path))
    rows = []
    for label, path in files:
        status = "present" if path.exists() else "missing"
        rows.append({"item": label, "status": status, "path": str(path)})
    rows.append(
        {
            "item": "Workspace URL",
            "status": "ready",
            "path": to_text(workspace.get("workspace_url")),
        }
    )
    return rows


def _metadata_summary(project_root: Path, upload_id: str) -> dict[str, Any]:
    metadata_path = project_root / "data" / "uploads" / f"{upload_id}.json"
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _sidebar(upload_id: str, page: str) -> str:
    links: list[str] = []
    for key, label, _desc in PAGE_REGISTRY:
        active = "nav-active" if key == page else ""
        href = f"/dashboard/{upload_id}" if key == "overview" else f"/dashboard/{upload_id}/{key}"
        links.append(f"<a class='nav-item {active}' href='{href}'>{_escape(label)}</a>")
    return (
        "<aside class='sidebar'><div class='brand'>RetailOps Admin</div>"
        + "".join(links)
        + "</aside>"
    )


def _topbar(title: str, description: str, upload_id: str) -> str:
    return (
        "<header class='topbar'>"
        "<div>"
        f"<h1>{_escape(title)}</h1>"
        f"<p>{_escape(description)} · Upload ID: <strong>{_escape(upload_id)}</strong></p>"
        "</div>"
        "<div class='topbar-actions'>"
        "<a class='btn-link' href='/docs'>API docs</a>"
        "<a class='btn-link' href='/openapi.json'>OpenAPI</a>"
        "<button id='theme-toggle' type='button'>Dark / Light</button>"
        "</div></header>"
    )


def _overview_page(workspace: dict[str, Any]) -> str:
    overview = dict(workspace.get("overview", {}))
    report_catalog = dict(workspace.get("report_catalog", {}))
    module_status = [item for item in workspace.get("module_status", []) if isinstance(item, dict)]
    action_center = [item for item in workspace.get("action_center", []) if isinstance(item, dict)]
    warnings = [to_text(item) for item in workspace.get("warnings", [])]
    available = sum(1 for item in module_status if to_text(item.get("status")) == "available")
    total_modules = max(len(module_status), 1)
    kpis = _kpi_cards(
        [
            ("Total orders", overview.get("total_orders", 0), "Loaded retail orders"),
            (
                "Total revenue",
                _fmt_number(overview.get("total_revenue", 0.0)),
                "Across transformed sales",
            ),
            ("Available modules", available, "Modules with live outputs"),
            ("Reports", overview.get("report_count", 0), "Business report inventory"),
            ("Delay rate", _fmt_percent(overview.get("delay_rate", 0.0)), "Shipment delay ratio"),
            ("Low stock items", overview.get("low_stock_items", 0), "Inventory exposure"),
        ]
    )
    warn_html = "".join(f"<div class='warning'>{_escape(item)}</div>" for item in warnings)
    rows = _report_family_rows(report_catalog)
    action_rows = [
        {
            "title": to_text(item.get("title")),
            "owner": to_text(item.get("owner")),
            "source": to_text(item.get("source")),
            "rationale": to_text(item.get("rationale")),
        }
        for item in action_center
    ]
    return (
        kpis
        + warn_html
        + "<div class='grid-2'>"
        + _svg_line_chart(
            "Daily revenue trend",
            list(workspace.get("charts", {}).get("sales_daily", [])),
            "sales_date",
            "revenue",
        )
        + _progress_card(
            "Module availability",
            available,
            total_modules,
            "Live modules replace sample outputs automatically when artifacts exist.",
        )
        + "</div><div class='grid-2'>"
        + _svg_bar_chart(
            "Revenue by category",
            list(workspace.get("charts", {}).get("revenue_by_category", [])),
            "category",
            "revenue",
        )
        + _svg_bar_chart("Report families", rows, "family", "count", "secondary")
        + "</div>"
        + _mini_table(
            "Leadership action center",
            action_rows,
            [("title", "Title"), ("owner", "Owner"), ("rationale", "Rationale")],
            table_id="action-center",
            filterable=True,
        )
    )


def _ingestion_page(workspace: dict[str, Any], project_root: Path) -> str:
    upload_id = to_text(workspace.get("upload_id"))
    metadata = _metadata_summary(project_root, upload_id)
    mapping = dict(metadata.get("mapping", {}))
    mapping_rows = [
        {"canonical_field": key, "source_column": value} for key, value in mapping.items()
    ]
    status_rows = [
        {"step": "Upload", "link": f"/easy-csv/{upload_id}/wizard", "status": "ready"},
        {"step": "Validation", "link": f"/easy-csv/{upload_id}/validate", "status": "ready"},
        {"step": "Import", "link": f"/easy-csv/{upload_id}/import", "status": "ready"},
        {"step": "Transform", "link": f"/easy-csv/{upload_id}/transform", "status": "ready"},
        {
            "step": "First dashboard",
            "link": f"/easy-csv/{upload_id}/dashboard/view",
            "status": "ready",
        },
        {
            "step": "First forecast",
            "link": f"/easy-csv/{upload_id}/forecast/view",
            "status": "ready",
        },
    ]
    workflow = "".join(
        (
            "<a class='workflow-link' href='" + _escape(item["link"]) + "'>"
            f"<strong>{_escape(item['step'])}</strong><span>{_escape(item['link'])}</span></a>"
        )
        for item in status_rows
    )
    return (
        _kpi_cards(
            [
                ("Upload file", to_text(metadata.get("filename") or "-"), "Current CSV source"),
                ("Mapped fields", len(mapping_rows), "Canonical coverage"),
                ("Delimiter", to_text(metadata.get("delimiter") or ","), "Detected separator"),
                ("Encoding", to_text(metadata.get("encoding") or "utf-8"), "Stored encoding"),
            ]
        )
        + "<div class='grid-2'>"
        + _progress_card(
            "Mapping coverage",
            len(mapping_rows),
            7,
            "Required first-pass fields are order_id, order_date, customer_id, sku, quantity, unit_price, store_code.",
        )
        + _card(
            "Workflow shortcuts",
            "<div class='workflow-grid'>"
            f"<a class='workflow-link' href='/easy-csv/wizard'><strong>Start wizard</strong><span>/easy-csv/wizard</span></a>"
            f"{workflow}</div>",
        )
        + "</div>"
        + _mini_table(
            "Field mapping",
            mapping_rows,
            [("canonical_field", "Canonical field"), ("source_column", "Source column")],
            table_id="mapping-table",
        )
    )


def _executive_page(workspace: dict[str, Any]) -> str:
    executive = dict(workspace.get("executive_review", {}))
    scorecard = dict(workspace.get("scorecard_summary", {}))
    benchmarking = dict(workspace.get("charts", {}).get("benchmarking", {}))
    metric_cards = [
        (
            to_text(item.get("label") or item.get("metric_name")),
            item.get("value"),
            to_text(item.get("commentary") or ""),
        )
        for item in executive.get("metric_cards", [])
        if isinstance(item, dict)
    ]
    kpis = _kpi_cards(metric_cards[:6]) if metric_cards else ""
    risk_rows = [item for item in executive.get("top_risks", []) if isinstance(item, dict)]
    action_rows = [item for item in executive.get("top_actions", []) if isinstance(item, dict)]
    watch_rows = [item for item in executive.get("watchlist_skus", []) if isinstance(item, dict)]
    pillar_rows = [item for item in scorecard.get("pillars", []) if isinstance(item, dict)]
    store_rows = [
        item for item in benchmarking.get("store_benchmarks", []) if isinstance(item, dict)
    ]
    category_rows = [
        item for item in benchmarking.get("category_benchmarks", []) if isinstance(item, dict)
    ]
    return (
        f"<div class='hero-note'>{_escape(executive.get('headline') or 'Executive narrative available.')}</div>"
        + kpis
        + "<div class='grid-2'>"
        + _svg_bar_chart("Scorecard pillars", pillar_rows, "pillar_name", "score")
        + _svg_bar_chart(
            "Store benchmarks", store_rows, "store_code", "benchmark_score", "secondary"
        )
        + "</div><div class='grid-2'>"
        + _mini_table(
            "Top risks",
            risk_rows,
            [("title", "Risk"), ("severity", "Severity"), ("recommended_action", "Action")],
            table_id="top-risks",
        )
        + _mini_table(
            "Top actions",
            action_rows,
            [("title", "Action"), ("owner", "Owner"), ("expected_outcome", "Outcome")],
            table_id="top-actions",
        )
        + "</div>"
        + _mini_table(
            "Watchlist SKUs",
            watch_rows or category_rows,
            [("sku", "SKU"), ("category", "Category"), ("risk_flag", "Risk")],
            table_id="watchlist-skus",
            empty_message="No executive watchlist rows were generated.",
        )
    )


def _operations_page(workspace: dict[str, Any]) -> str:
    module_status = [item for item in workspace.get("module_status", []) if isinstance(item, dict)]
    inventory_health = list(workspace.get("charts", {}).get("inventory_health", []))
    sections = [_module_panel(module, index) for index, module in enumerate(module_status)]
    inventory_chart = _svg_bar_chart(
        "Inventory days of cover",
        inventory_health,
        "sku",
        "days_of_cover",
        "secondary",
    )
    inventory_table = _mini_table(
        "Inventory health detail",
        inventory_health,
        [
            ("sku", "SKU"),
            ("on_hand", "On hand"),
            ("days_of_cover", "Days of cover"),
            ("low_stock", "Low stock"),
        ],
        table_id="inventory-health",
        filterable=True,
    )
    return "<div class='grid-2'>" + inventory_chart + inventory_table + "</div>" + "".join(sections)


def _intelligence_page(router_rows: list[dict[str, Any]]) -> str:
    wanted = {
        "abc_xyz_intelligence",
        "assortment_intelligence",
        "basket_affinity_intelligence",
        "customer_churn_intelligence",
        "customer_cohort_intelligence",
        "customer_intelligence",
        "fulfillment_sla_intelligence",
        "inventory_aging_intelligence",
        "payment_reconciliation",
        "profitability_intelligence",
        "promotion_pricing_intelligence",
        "sales_anomaly_intelligence",
        "seasonality_intelligence",
        "supplier_procurement_intelligence",
    }
    filtered = [row for row in router_rows if row["module_path"].split(".")[-2] in wanted]
    category_rows = []
    for row in filtered:
        category_rows.append(
            {
                "module": row["tag"],
                "prefix": row["prefix"],
                "routes": row["route_count"],
            }
        )
    return _svg_bar_chart(
        "Intelligence route density", category_rows, "module", "routes"
    ) + _mini_table(
        "Intelligence capabilities",
        category_rows,
        [("module", "Module"), ("prefix", "Prefix"), ("routes", "Routes")],
        table_id="intelligence-capabilities",
        filterable=True,
    )


def _reports_page(workspace: dict[str, Any]) -> str:
    report_catalog = dict(workspace.get("report_catalog", {}))
    report_rows = [item for item in report_catalog.get("reports", []) if isinstance(item, dict)]
    family_rows = _report_family_rows(report_catalog)
    enriched = []
    for item in report_rows:
        report_name = to_text(item.get("report_name"))
        enriched.append(
            {
                "family": _report_family(report_name).replace("_", " ").title(),
                "report_name": report_name,
                "endpoint": to_text(item.get("endpoint")),
            }
        )
    return (
        "<div class='grid-2'>"
        + _svg_bar_chart("Reports by family", family_rows, "family", "count")
        + _progress_card(
            "Report coverage",
            len(report_rows),
            max(len(report_rows), 1),
            "Every report from the catalog is listed below with its endpoint.",
        )
        + "</div>"
        + _mini_table(
            "Full report directory",
            enriched,
            [("family", "Family"), ("report_name", "Report"), ("endpoint", "Endpoint")],
            table_id="report-directory",
            filterable=True,
        )
    )


def _apis_page(router_rows: list[dict[str, Any]], endpoint_rows: list[dict[str, Any]]) -> str:
    category_rows: dict[str, int] = defaultdict(int)
    for item in router_rows:
        category_rows[item["tag"]] += int(item["route_count"])
    chart_rows = [{"tag": key, "route_count": value} for key, value in category_rows.items()]
    chart_rows.sort(key=lambda item: (-item["route_count"], item["tag"]))
    return (
        _kpi_cards(
            [
                ("Router groups", len(router_rows), "Registered router prefixes"),
                ("API routes", len(endpoint_rows), "Detected FastAPI routes"),
                ("Docs", "/docs", "Interactive API documentation"),
                ("OpenAPI", "/openapi.json", "Machine-readable schema"),
            ]
        )
        + "<div class='grid-2'>"
        + _svg_bar_chart("Route volume by group", chart_rows, "tag", "route_count")
        + _mini_table(
            "Router inventory",
            router_rows,
            [("tag", "Tag"), ("prefix", "Prefix"), ("route_count", "Routes")],
            table_id="router-inventory",
            filterable=True,
        )
        + "</div>"
        + _mini_table(
            "Full API directory",
            endpoint_rows,
            [("methods", "Methods"), ("path", "Path"), ("tag", "Tag")],
            table_id="api-directory",
            filterable=True,
        )
    )


def _capabilities_page(router_rows: list[dict[str, Any]]) -> str:
    prefixes = {item["prefix"] for item in router_rows}
    groups: list[str] = []
    for group in GROUPED_CAPABILITIES:
        rows = []
        for label, endpoint in group["items"]:
            matched = any(endpoint.startswith(prefix) for prefix in prefixes if prefix not in {"/"})
            rows.append(
                {
                    "capability": label,
                    "endpoint": endpoint,
                    "coverage": "api_present" if matched else "linked_reference",
                }
            )
        groups.append(
            _mini_table(
                group["group"],
                rows,
                [("capability", "Capability"), ("endpoint", "Endpoint"), ("coverage", "Coverage")],
                table_id=f"cap-{group['group'].lower().replace(' ', '-')}",
            )
        )
    return "".join(groups)


def _platform_page(service_rows: list[dict[str, Any]], runtime_rows: list[dict[str, Any]]) -> str:
    settings = get_settings()
    cards = _kpi_cards(
        [
            ("Profile", settings.app_profile, "Resolved runtime profile"),
            ("Connectors", ", ".join(settings.enabled_connector_values), "Enabled connectors"),
            (
                "Optional extras",
                ", ".join(settings.enabled_optional_extra_values) or "none",
                "Enabled optional modules",
            ),
            ("Service definitions", len(service_rows), "Services found in compose overlays"),
        ]
    )
    ready_count = sum(1 for row in runtime_rows if row["status"] in {"present", "ready"})
    file_counts: dict[str, int] = Counter(row["compose_file"] for row in service_rows)
    file_rows = [
        {"compose_file": key, "service_count": value} for key, value in file_counts.items()
    ]
    return (
        cards
        + "<div class='grid-2'>"
        + _progress_card(
            "Offline runtime readiness",
            ready_count,
            max(len(runtime_rows), 1),
            "Files and artifacts that already exist without live services.",
        )
        + _svg_bar_chart(
            "Compose service files",
            file_rows,
            "compose_file",
            "service_count",
            "secondary",
        )
        + "</div>"
        + _mini_table(
            "Runtime artifact inventory",
            runtime_rows,
            [("item", "Item"), ("status", "Status"), ("path", "Path")],
            table_id="runtime-artifacts",
        )
    )


def _runtime_page(runtime_rows: list[dict[str, Any]]) -> str:
    present = sum(1 for row in runtime_rows if row["status"] in {"present", "ready"})
    return _kpi_cards(
        [
            ("Ready artifacts", present, "Available without live services"),
            ("Tracked items", len(runtime_rows), "Files and generated outputs"),
            ("Sample fallback", "enabled", "Missing outputs still render visually"),
        ]
    ) + _mini_table(
        "Runtime without services",
        runtime_rows,
        [("item", "Item"), ("status", "Status"), ("path", "Location")],
        table_id="runtime-table",
        filterable=True,
    )


def _services_page(service_rows: list[dict[str, Any]]) -> str:
    display_rows = []
    for row in service_rows:
        links = " ".join(f"<a href='{_escape(item)}'>{_escape(item)}</a>" for item in row["links"])
        display_rows.append(
            {
                "compose_file": row["compose_file"],
                "service": row["service"],
                "ports": row["ports"],
                "links": links or "-",
            }
        )
    return _kpi_cards(
        [
            ("Configured services", len(service_rows), "Parsed from compose overlays"),
            ("Dashboard", "/dashboard/...", "Separated UI layer"),
        ]
    ) + _mini_table(
        "Configured service links",
        display_rows,
        [
            ("compose_file", "Compose file"),
            ("service", "Service"),
            ("ports", "Ports"),
            ("links", "Links"),
        ],
        table_id="service-directory",
        filterable=True,
    )


def _layout_css() -> str:
    return """
:root {
  --bg: #f3f5f9;
  --panel: #ffffff;
  --panel-2: #f8fafc;
  --text: #102038;
  --muted: #607089;
  --border: #d8e0ee;
  --accent: #2a3f54;
  --accent-2: #1abb9c;
  --warning: #f97316;
  --shadow: 0 18px 40px rgba(16, 32, 56, 0.08);
}
body.theme-dark {
  --bg: #111827;
  --panel: #172132;
  --panel-2: #1d2a3f;
  --text: #e5eef8;
  --muted: #9db0c5;
  --border: #283449;
  --accent: #2f4050;
  --accent-2: #1abb9c;
  --warning: #fb923c;
  --shadow: 0 18px 42px rgba(0, 0, 0, 0.30);
}
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, Arial, sans-serif; background: var(--bg); color: var(--text); }
a { color: #3b82f6; text-decoration: none; }
.shell { display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }
.sidebar { background: linear-gradient(180deg, #2a3f54 0%, #1f2c3a 100%); padding: 1.5rem 1rem; }
.brand { color: #fff; font-size: 1.35rem; font-weight: 800; margin-bottom: 1rem; }
.nav-item { display: block; padding: 0.72rem 0.95rem; border-radius: 12px; color: #dbe7f3; margin-bottom: 0.35rem; }
.nav-item:hover, .nav-active { background: rgba(255,255,255,0.12); color: #fff; }
.main { padding: 1.4rem; }
.topbar { display: flex; justify-content: space-between; gap: 1rem; align-items: start; margin-bottom: 1rem; }
.topbar h1 { margin: 0; font-size: 1.8rem; }
.topbar p { margin: 0.35rem 0 0; color: var(--muted); }
.topbar-actions { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; }
.btn-link, #theme-toggle { border: 1px solid var(--border); background: var(--panel); color: var(--text); border-radius: 10px; padding: 0.55rem 0.85rem; box-shadow: var(--shadow); cursor: pointer; }
.kpi-grid, .grid-2 { display: grid; gap: 1rem; margin-bottom: 1rem; }
.kpi-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.kpi-card, .card { background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 1rem 1.05rem; box-shadow: var(--shadow); }
.kpi-label, .card-subtitle, .chart-caption, .kpi-note { display: block; color: var(--muted); font-size: 0.9rem; }
.kpi-value { display: block; font-size: 1.6rem; margin: 0.3rem 0 0.2rem; }
.panel-card h3 { margin: 0 0 0.35rem; font-size: 1.06rem; }
.hero-note, .warning { background: var(--panel); border: 1px solid var(--border); border-left: 6px solid var(--warning); border-radius: 16px; padding: 0.95rem 1rem; margin-bottom: 1rem; box-shadow: var(--shadow); }
.chart-svg { width: 100%; height: auto; }
.axis { stroke: var(--border); stroke-width: 2; }
.axis-text, .value-text, .ring-note, .ring-value { fill: var(--muted); font-size: 12px; }
.line-path { fill: none; stroke: var(--accent-2); stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
.line-dot { fill: var(--accent-2); }
.bar-accent { fill: #2a3f54; }
.bar-secondary { fill: #1abb9c; }
.ring { width: 100%; max-width: 240px; display: block; margin: 0 auto; }
.ring-track { fill: none; stroke: rgba(96,112,137,0.16); stroke-width: 14; }
.ring-fill { fill: none; stroke: var(--accent-2); stroke-width: 14; transform: rotate(-90deg); transform-origin: 70px 70px; }
.pill-row { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 0.8rem; }
.pill { border-radius: 999px; padding: 0.24rem 0.6rem; font-size: 0.82rem; border: 1px solid var(--border); background: var(--panel-2); }
.pill-ok { color: #0f766e; }
.pill-warn { color: #c2410c; }
.pill-neutral { color: var(--muted); }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.data-table th, .data-table td { border-bottom: 1px solid var(--border); padding: 0.6rem; text-align: left; vertical-align: top; }
.data-table th { color: var(--muted); font-weight: 600; background: var(--panel-2); }
.table-tools { margin-bottom: 0.6rem; }
.table-tools input { width: 100%; padding: 0.65rem 0.75rem; border: 1px solid var(--border); border-radius: 10px; background: var(--panel-2); color: var(--text); }
.workflow-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 0.75rem; }
.workflow-link { display: block; border: 1px solid var(--border); border-radius: 14px; padding: 0.85rem; background: var(--panel-2); }
.workflow-link strong, .workflow-link span { display: block; }
.workflow-link span { margin-top: 0.35rem; color: var(--muted); font-size: 0.88rem; word-break: break-all; }
.module-stack { display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
.module-summary { background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 1rem; box-shadow: var(--shadow); }
@media (max-width: 1300px) { .kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } .module-stack { grid-template-columns: 1fr; } }
@media (max-width: 980px) { .shell { grid-template-columns: 1fr; } .sidebar { position: static; } .grid-2, .workflow-grid, .kpi-grid { grid-template-columns: 1fr; } }
"""


def _layout_script() -> str:
    return """
<script>
(function () {
  const saved = localStorage.getItem('retailops-dashboard-theme');
  if (saved === 'dark') { document.body.classList.add('theme-dark'); }
  window.toggleDashboardTheme = function () {
    document.body.classList.toggle('theme-dark');
    const value = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
    localStorage.setItem('retailops-dashboard-theme', value);
  };
  window.filterTable = function (tableId, query) {
    const table = document.getElementById(tableId);
    if (!table) { return; }
    const search = String(query || '').toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(function (row) {
      const text = row.textContent.toLowerCase();
      row.style.display = text.indexOf(search) >= 0 ? '' : 'none';
    });
  };
  window.addEventListener('DOMContentLoaded', function () {
    const button = document.getElementById('theme-toggle');
    if (button) { button.addEventListener('click', window.toggleDashboardTheme); }
  });
})();
</script>
"""


def render_dashboard_html(
    *,
    workspace: dict[str, Any],
    page: str,
    project_root: Path,
) -> str:
    active_page = page if page in PAGE_KEYS else "overview"
    page_title = next(label for key, label, _ in PAGE_REGISTRY if key == active_page)
    page_desc = next(desc for key, _label, desc in PAGE_REGISTRY if key == active_page)
    upload_id = to_text(workspace.get("upload_id"))
    router_rows, endpoint_rows = _router_inventory()
    runtime_rows = _runtime_rows(project_root, upload_id, workspace)
    service_rows = _compose_service_rows(project_root)
    renderers = {
        "overview": lambda: _overview_page(workspace),
        "ingestion": lambda: _ingestion_page(workspace, project_root),
        "executive": lambda: _executive_page(workspace),
        "operations": lambda: _operations_page(workspace),
        "intelligence": lambda: _intelligence_page(router_rows),
        "reports": lambda: _reports_page(workspace),
        "apis": lambda: _apis_page(router_rows, endpoint_rows),
        "capabilities": lambda: _capabilities_page(router_rows),
        "platform": lambda: _platform_page(service_rows, runtime_rows),
        "runtime": lambda: _runtime_page(runtime_rows),
        "services": lambda: _services_page(service_rows),
    }
    content = renderers[active_page]()
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{_escape(page_title)} · RetailOps Dashboard</title>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<style>{_layout_css()}\n{error_log_css()}</style></head><body>"
        f"<div class='shell'>{_sidebar(upload_id, active_page)}<main class='main'>"
        f"{_topbar(page_title, page_desc, upload_id)}{content}{render_error_log_panel(title='Recent page and API errors')}</main></div>"
        f"{_layout_script()}</body></html>"
    )
