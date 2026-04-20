# Project:      RetailOps Data & AI Platform
# Module:       core.api
# File:         error_logging.py
# Path:         core/api/error_logging.py
#
# Summary:      Captures and renders recent request errors for HTML and API flows.
# Purpose:      Provides a small shared error log that pages can display directly.
# Scope:        internal
# Status:       stable

from __future__ import annotations

import html
import json
import traceback
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Request

ERROR_LOG_DIR = Path("data/logs")
ERROR_LOG_FILE = ERROR_LOG_DIR / "recent_errors.jsonl"
MAX_LOG_ENTRIES = 400


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_text(value: Any, default: str = "") -> str:
    if value in {None, ""}:
        return default
    return str(value)


def is_html_request(request: Request) -> bool:
    accept = str(request.headers.get("accept", "")).lower()
    return "text/html" in accept or request.url.path.startswith(("/dashboard", "/easy-csv", "/setup"))


def _normalize_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if not context:
        return payload
    for key, value in context.items():
        payload[str(key)] = value if isinstance(value, (str, int, float, bool, list, dict)) or value is None else str(value)
    return payload


def _trim_log_file() -> None:
    if not ERROR_LOG_FILE.exists():
        return
    try:
        lines = ERROR_LOG_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    if len(lines) <= MAX_LOG_ENTRIES:
        return
    ERROR_LOG_FILE.write_text("\n".join(lines[-MAX_LOG_ENTRIES:]) + "\n", encoding="utf-8")


def log_error(
    *,
    request: Request | None,
    title: str,
    detail: str,
    status_code: int,
    exc: BaseException | None = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _utc_now_iso(),
        "title": _safe_text(title, "Application error"),
        "detail": _safe_text(detail, "Unexpected application error."),
        "status_code": int(status_code),
        "path": _safe_text(getattr(getattr(request, "url", None), "path", None), "n/a"),
        "method": _safe_text(getattr(request, "method", None), "n/a"),
        "request_id": _safe_text(getattr(getattr(request, "state", None), "request_id", None), "n/a"),
        "context": _normalize_context(context),
    }
    if exc is not None:
        entry["exception_type"] = type(exc).__name__
        entry["traceback"] = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-12000:]
    else:
        entry["traceback"] = ""
    with ERROR_LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _trim_log_file()
    return entry


def recent_errors(limit: int = 12) -> list[dict[str, Any]]:
    if not ERROR_LOG_FILE.exists():
        return []
    try:
        lines = ERROR_LOG_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    entries: list[dict[str, Any]] = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            entries.append(item)
        if len(entries) >= max(1, limit):
            break
    return entries


def clear_recent_errors() -> None:
    if ERROR_LOG_FILE.exists():
        ERROR_LOG_FILE.unlink()


def _error_items(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "<p class='error-muted'>No recent errors were recorded.</p>"
    parts: list[str] = ["<div class='error-log-list'>"]
    for item in entries:
        context = item.get("context") or {}
        context_html = ""
        if context:
            context_parts = []
            for key, value in context.items():
                context_parts.append(
                    f"<li><strong>{html.escape(str(key))}:</strong> {html.escape(str(value))}</li>"
                )
            context_html = "<ul class='error-context'>" + "".join(context_parts) + "</ul>"
        traceback_text = _safe_text(item.get("traceback"))
        trace_html = (
            "<details><summary>Traceback</summary>"
            f"<pre>{html.escape(traceback_text)}</pre></details>"
            if traceback_text
            else ""
        )
        parts.append(
            "<article class='error-item'>"
            f"<div class='error-head'><span class='error-status'>HTTP {html.escape(str(item.get('status_code', '')))}</span>"
            f"<span class='error-time'>{html.escape(_safe_text(item.get('timestamp')))}</span></div>"
            f"<h3>{html.escape(_safe_text(item.get('title'), 'Application error'))}</h3>"
            f"<p><strong>Path:</strong> {html.escape(_safe_text(item.get('method')))} {html.escape(_safe_text(item.get('path')))}</p>"
            f"<p>{html.escape(_safe_text(item.get('detail')))}</p>"
            f"<p><strong>Request ID:</strong> {html.escape(_safe_text(item.get('request_id')))}</p>"
            f"{context_html}{trace_html}</article>"
        )
    parts.append("</div>")
    return "".join(parts)


def error_log_css() -> str:
    return "\n".join(
        [
            ".error-log-panel { margin-top: 1rem; border: 1px solid #fecaca; background: #fff1f2; border-radius: 14px; padding: 1rem 1.1rem; }",
            ".error-log-panel h2, .error-log-panel h3 { margin-top: 0; color: #7f1d1d; }",
            ".error-log-panel p, .error-log-panel li, .error-log-panel summary { color: #7f1d1d; }",
            ".error-log-panel code { background: #ffe4e6; }",
            ".error-log-list { display: grid; gap: 0.85rem; }",
            ".error-item { border: 1px solid #fecdd3; background: white; border-radius: 12px; padding: 0.9rem; }",
            ".error-head { display: flex; justify-content: space-between; gap: 0.75rem; margin-bottom: 0.5rem; }",
            ".error-status { font-weight: 700; }",
            ".error-time { color: #9f1239; font-size: 0.88rem; }",
            ".error-context { margin: 0.5rem 0 0; padding-left: 1rem; }",
            ".error-muted { color: #9f1239; }",
            ".error-log-toolbar { display: flex; justify-content: space-between; gap: 1rem; align-items: center; margin-bottom: 0.75rem; }",
            ".error-log-toolbar a { color: #9f1239; text-decoration: none; font-weight: 600; }",
            ".error-page { max-width: 1100px; margin: 2rem auto; font-family: Arial, sans-serif; color: #111827; padding: 0 1rem; }",
            ".error-page .hero { border: 1px solid #fecaca; background: #fff7ed; border-radius: 16px; padding: 1rem 1.2rem; margin-bottom: 1rem; }",
            ".error-page .hero h1 { margin: 0 0 0.6rem; color: #7c2d12; }",
            ".error-page .hero p { margin: 0.3rem 0; }",
            ".error-page pre { white-space: pre-wrap; word-break: break-word; background: #111827; color: #f8fafc; padding: 0.9rem; border-radius: 12px; overflow-x: auto; }",
        ]
    )


def render_error_log_panel(*, title: str = "Recent errors", limit: int = 8) -> str:
    entries = recent_errors(limit=limit)
    return (
        "<section class='error-log-panel'>"
        "<div class='error-log-toolbar'>"
        f"<h2>{html.escape(title)}</h2>"
        "<a href='/debug/error-log'>Open full error log</a>"
        "</div>"
        "<p class='error-muted'>If a page or API fails, the latest details appear here.</p>"
        f"{_error_items(entries)}"
        "</section>"
    )


def render_error_page(*, title: str, detail: str, request: Request, status_code: int, entry: Mapping[str, Any] | None = None) -> str:
    recent_panel = render_error_log_panel(limit=10)
    entry_data = dict(entry or {})
    traceback_block = ""
    traceback_text = _safe_text(entry_data.get("traceback"))
    if traceback_text:
        traceback_block = (
            "<section class='error-log-panel'><h2>Latest traceback</h2>"
            f"<pre>{html.escape(traceback_text)}</pre></section>"
        )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{html.escape(title)}</title>"
        f"<style>{error_log_css()}</style></head><body>"
        "<main class='error-page'>"
        "<section class='hero'>"
        f"<h1>{html.escape(title)}</h1>"
        f"<p><strong>HTTP status:</strong> {html.escape(str(status_code))}</p>"
        f"<p><strong>Request:</strong> {html.escape(request.method)} {html.escape(request.url.path)}</p>"
        f"<p><strong>Detail:</strong> {html.escape(detail)}</p>"
        f"<p><strong>Request ID:</strong> {html.escape(_safe_text(getattr(request.state, 'request_id', None), 'n/a'))}</p>"
        "<p><a href='/debug/error-log'>Open recent error log</a></p>"
        "</section>"
        f"{traceback_block}{recent_panel}</main></body></html>"
    )
