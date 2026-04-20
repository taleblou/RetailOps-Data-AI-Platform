# Project:      RetailOps Data & AI Platform
# Module:       core.api.routes
# File:         error_log.py
# Path:         core/api/routes/error_log.py
#
# Summary:      Exposes recent application errors for browser inspection.
# Purpose:      Provides a simple error log page and JSON feed for failed pages.
# Scope:        public API
# Status:       stable

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from core.api.error_logging import error_log_css, recent_errors, render_error_log_panel

router = APIRouter(tags=["error-log"])
api_router = APIRouter(prefix="/api/v1/error-log", tags=["error-log"])


@api_router.get("/recent")
def get_recent_errors(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
    return {
        "entries": recent_errors(limit=limit),
        "count": len(recent_errors(limit=limit)),
    }


@router.get("/debug/error-log", response_class=HTMLResponse)
def get_error_log_page(limit: int = Query(default=25, ge=1, le=100)) -> HTMLResponse:
    body = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>RetailOps Error Log</title>"
        f"<style>{error_log_css()}</style></head><body>"
        "<main class='error-page'>"
        "<section class='hero'>"
        "<h1>RetailOps error log</h1>"
        "<p>This page shows the latest recorded page and API errors.</p>"
        "<p>Refresh the page after reproducing an error.</p>"
        "</section>"
        f"{render_error_log_panel(title='Latest recorded errors', limit=limit)}"
        "</main></body></html>"
    )
    return HTMLResponse(body)


router.include_router(api_router)
