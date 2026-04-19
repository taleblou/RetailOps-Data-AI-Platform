# Project:      RetailOps Data & AI Platform
# Module:       modules.dashboard_hub
# File:         admin_theme.py
# Path:         modules/dashboard_hub/admin_theme.py
#
# Summary:      Renders the dashboard hub as a multi-page admin workspace.
# Purpose:      Separates API endpoints from dashboard views and provides a
#               professional admin-style interface for analytics, reports,
#               runtime status, and service links.
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
#   - Key APIs: render_admin_dashboard_html
#   - Dependencies: __future__, html, json, typing
#   - Constraints: HTML output is self-contained so it can be rendered without
#     external CSS or JavaScript services.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import html
import json
from typing import Any


def _escape(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _slug_title(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _nav_html(workspace: dict[str, Any], current_page: str) -> str:
    pages = [item for item in workspace.get("pages", []) if isinstance(item, dict)]
    parts = [
        "<aside class='sidebar'>",
        "<div class='brand'>",
        "<div class='brand-mark'>RO</div>",
        "<div><strong>RetailOps Admin</strong><div class='muted'>Dashboard Workspace</div></div>",
        "</div>",
        "<div class='sidebar-section-label'>Navigation</div>",
        "<nav class='nav-list'>",
    ]
    for page in pages:
        key = str(page.get("key", "overview"))
        title = _escape(page.get("title", key))
        href = _escape(page.get("path", f"/dashboard/{workspace.get('upload_id', '')}/{key}"))
        active = " active" if key == current_page else ""
        parts.append(
            "<a class='nav-item"
            + active
            + "' href='"
            + href
            + "'><span class='nav-bullet'></span>"
            + title
            + "</a>"
        )
    parts.extend(
        [
            "</nav>",
            "<div class='sidebar-section-label'>Direct links</div>",
            "<div class='sidebar-links'>",
            "<a href='/docs'>OpenAPI Docs</a>",
            "<a href='/health'>API Health</a>",
            "<a href='" + _escape(workspace.get("api_workspace_url", "")) + "'>Workspace JSON</a>",
            "<a href='"
            + _escape(workspace.get("artifact_api_url", ""))
            + "'>Published Artifact</a>",
            "</div>",
            "<div class='theme-note'>",
            "Admin information architecture is adapted for this project from the Gentelella-style left-nav admin pattern.",
            "</div>",
            "</aside>",
        ]
    )
    return "".join(parts)


def _metric_cards(overview: dict[str, Any]) -> str:
    cards = [
        (
            "Orders",
            overview.get("total_orders", 0),
            "Uploaded order rows in the current workspace.",
        ),
        (
            "Revenue",
            overview.get("total_revenue", 0),
            "Revenue aggregated from the transform artifact.",
        ),
        (
            "Modules",
            overview.get("available_module_count", 0),
            "Operational analytics modules that returned data.",
        ),
        (
            "Reports",
            overview.get("report_count", 0),
            "Business review reports available in the catalog.",
        ),
        (
            "Avg order",
            overview.get("avg_order_value", 0),
            "Average order value from transformed orders.",
        ),
        ("Delay rate", overview.get("delay_rate", 0), "Delayed shipments divided by total orders."),
    ]
    return "".join(
        "<div class='metric-card'><div class='metric-label'>"
        + _escape(label)
        + "</div><div class='metric-value'>"
        + _escape(value)
        + "</div><div class='metric-help'>"
        + _escape(help_text)
        + "</div></div>"
        for label, value, help_text in cards
    )


def _warning_banners(workspace: dict[str, Any]) -> str:
    warnings = [item for item in workspace.get("warnings", []) if item]
    if not warnings:
        return "<div class='callout ok'>No dashboard warnings were detected for this upload.</div>"
    return "".join(
        "<div class='callout warn'><strong>Attention:</strong> " + _escape(item) + "</div>"
        for item in warnings
    )


def _summary_list(items: list[dict[str, Any]], title_key: str, detail_key: str) -> str:
    safe_items = [item for item in items if isinstance(item, dict)]
    if not safe_items:
        return "<div class='empty-state'>No rows are available.</div>"
    parts = ["<ul class='summary-list'>"]
    for item in safe_items:
        parts.append(
            "<li><strong>"
            + _escape(item.get(title_key, ""))
            + "</strong><span>"
            + _escape(item.get(detail_key, ""))
            + "</span></li>"
        )
    parts.append("</ul>")
    return "".join(parts)


def _simple_bars(
    rows: list[dict[str, Any]], label_key: str, value_key: str, max_rows: int = 8
) -> str:
    safe_rows = [item for item in rows if isinstance(item, dict)][:max_rows]
    if not safe_rows:
        return "<div class='empty-state'>No chart rows are available.</div>"
    max_value = max(float(item.get(value_key) or 0) for item in safe_rows) or 1.0
    parts = ["<div class='bars'>"]
    for row in safe_rows:
        value = round(float(row.get(value_key) or 0), 2)
        width = max(4.0, (value / max_value) * 100.0)
        parts.append(
            "<div class='bar-row'><div class='bar-label'>"
            + _escape(row.get(label_key, "unknown"))
            + "</div><div class='bar-track'><div class='bar-fill' style='width:"
            + f"{width:.1f}%"
            + "'></div></div><div class='bar-value'>"
            + _escape(value)
            + "</div></div>"
        )
    parts.append("</div>")
    return "".join(parts)


def _table_card(
    title: str,
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    empty_message: str,
) -> str:
    safe_rows = [item for item in rows if isinstance(item, dict)]
    parts = [
        "<section class='panel'>",
        "<div class='panel-head'><h3>",
        _escape(title),
        "</h3></div>",
    ]
    if not safe_rows:
        parts.extend(["<div class='empty-state'>", _escape(empty_message), "</div></section>"])
        return "".join(parts)
    parts.append("<div class='table-wrap'><table><thead><tr>")
    for _, label in columns:
        parts.extend(["<th>", _escape(label), "</th>"])
    parts.append("</tr></thead><tbody>")
    for row in safe_rows:
        parts.append("<tr>")
        for key, _ in columns:
            cell = row.get(key, "")
            if isinstance(cell, (dict, list)):
                cell_text = json.dumps(cell, ensure_ascii=False)
            else:
                cell_text = str(cell)
            parts.extend(["<td>", _escape(cell_text), "</td>"])
        parts.append("</tr>")
    parts.append("</tbody></table></div></section>")
    return "".join(parts)


def _module_cards(workspace: dict[str, Any]) -> str:
    module_status = [item for item in workspace.get("module_status", []) if isinstance(item, dict)]
    if not module_status:
        return "<div class='empty-state'>No module status rows are available.</div>"
    parts = ["<div class='card-grid'>"]
    for item in module_status:
        status = str(item.get("status", "unknown"))
        tone = "good" if status == "available" else "bad"
        summary = item.get("summary") or {}
        summary_text = ", ".join(f"{key}: {value}" for key, value in list(summary.items())[:4])
        parts.extend(
            [
                "<section class='mini-card ",
                tone,
                "'><div class='mini-head'><h4>",
                _escape(item.get("title", "Module")),
                "</h4><span class='pill ",
                tone,
                "'>",
                _escape(status),
                "</span></div><div class='mini-text'>",
                _escape(summary_text or item.get("error", "No summary available.")),
                "</div><div class='mini-link'><a href='",
                _escape(item.get("endpoint", "#")),
                "'>Open API</a></div></section>",
            ]
        )
    parts.append("</div>")
    return "".join(parts)


def _report_group_sections(workspace: dict[str, Any]) -> str:
    groups = [item for item in workspace.get("report_groups", []) if isinstance(item, dict)]
    if not groups:
        return "<div class='empty-state'>No report groups are available.</div>"
    parts = []
    for group in groups:
        reports = [item for item in group.get("reports", []) if isinstance(item, dict)]
        rows = [
            {
                "report_name": item.get("report_name", ""),
                "endpoint": item.get("endpoint", ""),
                "family": group.get("title", ""),
            }
            for item in reports
        ]
        parts.append(
            _table_card(
                str(group.get("title", "Report Group")),
                rows,
                [
                    ("report_name", "Report"),
                    ("endpoint", "API endpoint"),
                    ("family", "Family"),
                ],
                "No reports were found in this family.",
            )
        )
    return "".join(parts)


def _capability_sections(workspace: dict[str, Any]) -> str:
    groups = [item for item in workspace.get("capability_groups", []) if isinstance(item, dict)]
    if not groups:
        return "<div class='empty-state'>No capability groups are available.</div>"
    parts = []
    for group in groups:
        items = [item for item in group.get("items", []) if isinstance(item, dict)]
        rows = []
        for item in items:
            rows.append(
                {
                    "capability": item.get("title", ""),
                    "path": item.get("endpoint", ""),
                    "notes": item.get("notes", ""),
                }
            )
        parts.append(
            _table_card(
                str(group.get("title", "Capability Group")),
                rows,
                [("capability", "Capability"), ("path", "Primary path"), ("notes", "Notes")],
                "No capabilities were listed for this group.",
            )
        )
    return "".join(parts)


def _runtime_section(workspace: dict[str, Any]) -> str:
    rows = [item for item in workspace.get("runtime_status", []) if isinstance(item, dict)]
    return _table_card(
        "Offline runtime and artifact readiness",
        rows,
        [
            ("title", "Item"),
            ("status", "Status"),
            ("detail", "Detail"),
            ("path", "Path"),
            ("notes", "Offline usage"),
        ],
        "No runtime status rows are available.",
    )


def _service_section(workspace: dict[str, Any]) -> str:
    rows = [item for item in workspace.get("service_directory", []) if isinstance(item, dict)]
    if not rows:
        return "<div class='empty-state'>No services were discovered from compose files.</div>"
    parts = [
        "<section class='panel'><div class='panel-head'><h3>Configured services and local links</h3></div>",
        "<div class='table-wrap'><table><thead><tr><th>Service</th><th>Compose file</th><th>Port</th><th>Type</th><th>Local access</th><th>Notes</th></tr></thead><tbody>",
    ]
    for row in rows:
        local_url = str(row.get("local_url", ""))
        if local_url:
            access_html = "<a href='" + _escape(local_url) + "'>" + _escape(local_url) + "</a>"
        else:
            access_html = _escape(row.get("access_hint", "internal"))
        parts.extend(
            [
                "<tr><td>",
                _escape(row.get("service", "")),
                "</td><td>",
                _escape(row.get("compose_file", "")),
                "</td><td>",
                _escape(row.get("port_mapping", "")),
                "</td><td>",
                _escape(row.get("kind", "")),
                "</td><td>",
                access_html,
                "</td><td>",
                _escape(row.get("notes", "")),
                "</td></tr>",
            ]
        )
    parts.append("</tbody></table></div></section>")
    return "".join(parts)


def _api_section(workspace: dict[str, Any]) -> str:
    rows = [item for item in workspace.get("endpoint_catalog", []) if isinstance(item, dict)]
    return _table_card(
        "API directory",
        rows,
        [("category", "Category"), ("label", "Label"), ("endpoint", "Endpoint")],
        "No API endpoints were catalogued.",
    )


def _overview_page(workspace: dict[str, Any]) -> str:
    charts = dict(workspace.get("charts", {}))
    executive = dict(workspace.get("executive_review", {}))
    scorecard = dict(workspace.get("scorecard_summary", {}))
    return "".join(
        [
            "<div class='page-grid two'>",
            "<section class='panel hero-panel'>",
            "<div class='eyebrow'>Unified enterprise dashboard</div>",
            "<h2>",
            _escape(workspace.get("workspace_title", "RetailOps Dashboard")),
            "</h2>",
            "<p class='hero-copy'>",
            _escape(
                executive.get(
                    "headline",
                    "Analytics, reports, runtime state, and service links are consolidated here.",
                )
            ),
            "</p>",
            "<div class='metric-grid'>",
            _metric_cards(dict(workspace.get("overview", {}))),
            "</div></section>",
            "<section class='panel'>",
            "<div class='panel-head'><h3>Leadership action queue</h3></div>",
            _summary_list(
                [item for item in workspace.get("action_center", []) if isinstance(item, dict)],
                "title",
                "rationale",
            ),
            "</section></div>",
            _warning_banners(workspace),
            "<div class='page-grid three'>",
            "<section class='panel'><div class='panel-head'><h3>Daily revenue</h3></div>",
            _simple_bars(list(charts.get("sales_daily", [])), "sales_date", "revenue", 10),
            "</section>",
            "<section class='panel'><div class='panel-head'><h3>Revenue by category</h3></div>",
            _simple_bars(list(charts.get("revenue_by_category", [])), "category", "revenue", 8),
            "</section>",
            _table_card(
                "Inventory health",
                list(charts.get("inventory_health", [])),
                [
                    ("sku", "SKU"),
                    ("on_hand", "On hand"),
                    ("days_of_cover", "Days of cover"),
                    ("low_stock", "Low stock"),
                ],
                "No inventory health rows are available.",
            ),
            "</div>",
            _table_card(
                "Operating scorecard pillars",
                list(scorecard.get("pillars", [])),
                [
                    ("pillar_name", "Pillar"),
                    ("score", "Score"),
                    ("target_score", "Target"),
                    ("gap_to_target", "Gap"),
                    ("recommended_action", "Recommended action"),
                ],
                "No scorecard data is available.",
            ),
        ]
    )


def _executive_page(workspace: dict[str, Any]) -> str:
    executive = dict(workspace.get("executive_review", {}))
    charts = dict(workspace.get("charts", {}))
    benchmarking = dict(charts.get("benchmarking", {}))
    return "".join(
        [
            "<section class='panel'><div class='panel-head'><h3>Executive review headline</h3></div>",
            "<p class='hero-copy'>",
            _escape(executive.get("headline", "No executive headline is available.")),
            "</p></section>",
            "<div class='page-grid two'>",
            _table_card(
                "Top risks",
                list(executive.get("top_risks", [])),
                [("title", "Risk"), ("severity", "Severity"), ("recommended_action", "Action")],
                "No top risks were generated.",
            ),
            _table_card(
                "Top actions",
                list(executive.get("top_actions", [])),
                [("title", "Action"), ("owner", "Owner"), ("expected_outcome", "Expected outcome")],
                "No top actions were generated.",
            ),
            "</div>",
            _table_card(
                "Watchlist SKUs",
                list(executive.get("watchlist_skus", [])),
                [("sku", "SKU"), ("reason", "Reason"), ("recommended_action", "Action")],
                "No watchlist rows were generated.",
            ),
            "<div class='page-grid two'>",
            _table_card(
                "Store benchmarks",
                list(benchmarking.get("store_benchmarks", [])),
                [("store_code", "Store"), ("score", "Score"), ("benchmark_status", "Status")],
                "No store benchmarks are available.",
            ),
            _table_card(
                "Category benchmarks",
                list(benchmarking.get("category_benchmarks", [])),
                [("category", "Category"), ("score", "Score"), ("benchmark_status", "Status")],
                "No category benchmarks are available.",
            ),
            "</div>",
        ]
    )


def _operations_page(workspace: dict[str, Any]) -> str:
    module_status = [item for item in workspace.get("module_status", []) if isinstance(item, dict)]
    highlight_rows = []
    for module in module_status:
        highlight_rows.append(
            {
                "module": module.get("title", ""),
                "endpoint": module.get("endpoint", ""),
                "recommended_action": module.get("recommended_action", ""),
                "highlights": json.dumps(module.get("highlight_rows", []), ensure_ascii=False)[
                    :350
                ],
            }
        )
    return "".join(
        [
            _module_cards(workspace),
            _table_card(
                "Operational module matrix",
                module_status,
                [
                    ("title", "Module"),
                    ("status", "Status"),
                    ("endpoint", "API endpoint"),
                    ("recommended_action", "Recommended action"),
                    ("error", "Error"),
                ],
                "No module status rows are available.",
            ),
            _table_card(
                "Operational highlights",
                highlight_rows,
                [
                    ("module", "Module"),
                    ("endpoint", "Endpoint"),
                    ("recommended_action", "Action"),
                    ("highlights", "Highlights"),
                ],
                "No module highlights are available.",
            ),
        ]
    )


def _reports_page(workspace: dict[str, Any]) -> str:
    header = (
        "<section class='panel'><div class='panel-head'><h3>Report directory</h3></div>"
        "<p class='hero-copy'>All report APIs stay under their current /api paths. This page gives grouped navigation only.</p></section>"
    )
    return header + _report_group_sections(workspace)


def _apis_page(workspace: dict[str, Any]) -> str:
    header = (
        "<section class='panel'><div class='panel-head'><h3>API directory</h3></div>"
        "<p class='hero-copy'>The dashboard lives under /dashboard while APIs stay under their original /api paths.</p></section>"
    )
    return header + _api_section(workspace)


def _capabilities_page(workspace: dict[str, Any]) -> str:
    return (
        "<section class='panel'><div class='panel-head'><h3>Platform capabilities</h3></div>"
        "<p class='hero-copy'>This section includes capabilities beyond the report catalog, including ingestion, intelligence modules, MLOps, and platform extensions.</p></section>"
        + _capability_sections(workspace)
    )


def _runtime_page(workspace: dict[str, Any]) -> str:
    return (
        "<section class='panel'><div class='panel-head'><h3>Runtime without services</h3></div>"
        "<p class='hero-copy'>These checks do not depend on external services. They show whether the current upload already has the files and artifacts needed for an offline dashboard view.</p></section>"
        + _runtime_section(workspace)
    )


def _services_page(workspace: dict[str, Any]) -> str:
    return (
        "<section class='panel'><div class='panel-head'><h3>Service directory</h3></div>"
        "<p class='hero-copy'>Links below come from compose configuration. If a service is not running, the link still appears as the configured local access point.</p></section>"
        + _service_section(workspace)
    )


def _render_page_body(workspace: dict[str, Any], current_page: str) -> str:
    page_map = {
        "overview": _overview_page,
        "executive": _executive_page,
        "operations": _operations_page,
        "reports": _reports_page,
        "apis": _apis_page,
        "capabilities": _capabilities_page,
        "runtime": _runtime_page,
        "services": _services_page,
    }
    renderer = page_map.get(current_page, _overview_page)
    return renderer(workspace)


def render_admin_dashboard_html(workspace: dict[str, Any], current_page: str = "overview") -> str:
    upload_id = str(workspace.get("upload_id", ""))
    page_title = _slug_title(current_page)
    css = """
:root {
  --sidebar-bg: #1f2a36;
  --sidebar-edge: #32475b;
  --accent: #1abb9c;
  --accent-soft: #e8fbf7;
  --bg: #f5f7fa;
  --panel: #ffffff;
  --text: #2a3f54;
  --muted: #73879c;
  --line: #e6ecf2;
  --danger: #c0392b;
  --success: #1e8449;
  --shadow: 0 10px 28px rgba(20, 37, 63, 0.08);
}
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, Segoe UI, Arial, sans-serif; background: var(--bg); color: var(--text); }
a { color: #2f7bd9; text-decoration: none; }
a:hover { text-decoration: underline; }
.app-shell { display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }
.sidebar { background: linear-gradient(180deg, var(--sidebar-bg), #16202a); color: #d9e2ec; padding: 20px 18px; border-right: 1px solid rgba(255,255,255,0.06); }
.brand { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
.brand-mark { width: 42px; height: 42px; border-radius: 12px; background: var(--accent); color: #fff; display: grid; place-items: center; font-weight: 700; }
.sidebar .muted { color: #9fb3c8; font-size: 12px; margin-top: 3px; }
.sidebar-section-label { font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: #8aa1b6; margin: 18px 0 8px; }
.nav-list { display: flex; flex-direction: column; gap: 6px; }
.nav-item { color: #dfe7ef; padding: 11px 12px; border-radius: 10px; display: flex; align-items: center; gap: 10px; }
.nav-item:hover, .nav-item.active { background: rgba(255,255,255,0.08); text-decoration: none; }
.nav-bullet { width: 8px; height: 8px; border-radius: 999px; background: var(--accent); flex: none; }
.sidebar-links { display: grid; gap: 8px; }
.sidebar-links a { color: #d7e5f2; }
.theme-note { margin-top: 22px; padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.07); color: #b9cada; font-size: 12px; line-height: 1.5; }
.main-shell { display: flex; flex-direction: column; min-width: 0; }
.topbar { display: flex; justify-content: space-between; align-items: center; gap: 20px; background: #fff; padding: 18px 28px; border-bottom: 1px solid var(--line); }
.top-title h1 { margin: 0; font-size: 24px; }
.top-title p { margin: 6px 0 0; color: var(--muted); }
.top-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.top-actions a { padding: 10px 14px; border-radius: 10px; border: 1px solid var(--line); background: #fff; }
.top-actions a.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.content { padding: 24px 28px 34px; }
.page-grid { display: grid; gap: 18px; margin-bottom: 18px; }
.page-grid.two { grid-template-columns: 1.35fr 1fr; }
.page-grid.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 18px; box-shadow: var(--shadow); padding: 18px 18px 16px; }
.hero-panel { background: linear-gradient(135deg, #fff, #fbfffe); }
.panel-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; }
.panel-head h3 { margin: 0; font-size: 18px; }
.eyebrow { font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); margin-bottom: 10px; }
.hero-copy { color: var(--muted); line-height: 1.65; }
.metric-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }
.metric-card { border: 1px solid var(--line); border-radius: 14px; padding: 14px; background: #fff; }
.metric-label { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.metric-value { font-size: 26px; font-weight: 700; margin: 8px 0; }
.metric-help { color: var(--muted); font-size: 13px; line-height: 1.5; }
.callout { margin-bottom: 12px; padding: 13px 14px; border-radius: 12px; border: 1px solid var(--line); background: #fff; }
.callout.warn { background: #fff8f6; border-color: #f4c7c3; color: #8b2c22; }
.callout.ok { background: var(--accent-soft); border-color: #b8efe1; color: #186d5c; }
.summary-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
.summary-list li { border: 1px solid var(--line); border-radius: 12px; padding: 12px 13px; display: grid; gap: 4px; }
.summary-list li span { color: var(--muted); }
.bars { display: grid; gap: 12px; }
.bar-row { display: grid; grid-template-columns: 140px 1fr 90px; gap: 10px; align-items: center; }
.bar-label, .bar-value { font-size: 13px; }
.bar-track { height: 12px; border-radius: 999px; background: #edf2f7; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), #41c5af); }
.table-wrap { overflow: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; font-size: 13px; }
th { color: var(--muted); text-transform: uppercase; font-size: 11px; letter-spacing: .08em; background: #fafcff; position: sticky; top: 0; }
.card-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-bottom: 18px; }
.mini-card { border: 1px solid var(--line); border-radius: 16px; padding: 16px; background: #fff; box-shadow: var(--shadow); }
.mini-card.good { border-left: 4px solid var(--success); }
.mini-card.bad { border-left: 4px solid var(--danger); }
.mini-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 12px; }
.mini-head h4 { margin: 0; font-size: 16px; }
.mini-text { color: var(--muted); min-height: 42px; line-height: 1.55; }
.mini-link { margin-top: 12px; }
.pill { display: inline-flex; align-items: center; border-radius: 999px; padding: 5px 10px; font-size: 12px; font-weight: 700; }
.pill.good { background: #e9f8f0; color: var(--success); }
.pill.bad { background: #fff0ef; color: var(--danger); }
.empty-state { padding: 16px; border: 1px dashed #cfd9e3; border-radius: 12px; color: var(--muted); }
.footer-note { color: var(--muted); font-size: 12px; margin-top: 24px; }
@media (max-width: 1200px) {
  .page-grid.two, .page-grid.three, .metric-grid, .card-grid { grid-template-columns: 1fr; }
}
@media (max-width: 940px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { display: none; }
  .content, .topbar { padding-left: 18px; padding-right: 18px; }
  .bar-row { grid-template-columns: 1fr; }
}
"""
    page_body = _render_page_body(workspace, current_page)
    nav_html = _nav_html(workspace, current_page)
    return "".join(
        [
            "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            "<title>",
            _escape(workspace.get("workspace_title", "RetailOps Dashboard")),
            " — ",
            _escape(page_title),
            "</title><style>",
            css,
            "</style></head><body>",
            "<div class='app-shell'>",
            nav_html,
            "<main class='main-shell'><header class='topbar'><div class='top-title'><h1>",
            _escape(page_title),
            "</h1><p>Upload ID: ",
            _escape(upload_id),
            "</p></div><div class='top-actions'>",
            "<a class='primary' href='",
            _escape(workspace.get("dashboard_root_url", f"/dashboard/{upload_id}")),
            "'>Dashboard home</a>",
            "<a href='",
            _escape(workspace.get("api_workspace_url", "")),
            "'>Workspace JSON</a>",
            "<a href='",
            _escape(workspace.get("artifact_api_url", "")),
            "'>Artifact JSON</a>",
            "</div></header><section class='content'>",
            page_body,
            "<div class='footer-note'>",
            _escape(
                workspace.get(
                    "dashboard_footer_note",
                    "Dashboard and API routes are separated. Dashboard pages live under /dashboard and APIs remain under /api.",
                )
            ),
            "</div></section></main></div></body></html>",
        ]
    )
