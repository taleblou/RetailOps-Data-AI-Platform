# Project:      RetailOps Data & AI Platform
# Module:       core.api
# File:         main.py
# Path:         core/api/main.py
#
# Summary:      Builds the public API surface for the API application.
# Purpose:      Provides the main application entry point and composes routers for API flows.
# Scope:        public API
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
#   - Key APIs: app, build_repository, create_app
#   - Dependencies: __future__, importlib, fastapi, config.settings,
#     core.ingestion.base.registry, core.ingestion.base.repository
#   - Constraints: Public request and response behavior should remain backward
#     compatible with documented API flows.
#   - Compatibility: Python 3.12+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from importlib import import_module
from typing import Any

import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from config.settings import get_settings
from core.api.error_logging import is_html_request, log_error, render_error_page
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.registry import build_default_registry
from core.ingestion.base.repository import MemoryRepository, RepositoryProtocol, SqlRepository
from core.ingestion.base.state_store import StateStore

OPTIONAL_ROUTER_DEPENDENCIES: dict[str, frozenset[str]] = {
    "modules.business_review_reporting.router:router": frozenset({"pypdf", "reportlab"}),
    "modules.feature_store.router:router": frozenset({"feast"}),
    "modules.advanced_serving.router:router": frozenset({"bentoml"}),
}


ROUTER_PATHS: tuple[str, ...] = (
    "core.api.routes.sources:router",
    "core.api.routes.easy_csv:router",
    "core.api.routes.error_log:router",
    "modules.analytics_kpi.router:router",
    "modules.customer_cohort_intelligence.router:router",
    "modules.customer_churn_intelligence.router:router",
    "modules.dashboard_hub.router:router",
    "modules.promotion_pricing_intelligence.router:router",
    "modules.supplier_procurement_intelligence.router:router",
    "modules.customer_intelligence.router:router",
    "modules.assortment_intelligence.router:router",
    "modules.basket_affinity_intelligence.router:router",
    "modules.business_review_reporting.router:router",
    "modules.payment_reconciliation.router:router",
    "modules.inventory_aging_intelligence.router:router",
    "modules.sales_anomaly_intelligence.router:router",
    "modules.profitability_intelligence.router:router",
    "modules.seasonality_intelligence.router:router",
    "modules.abc_xyz_intelligence.router:router",
    "modules.fulfillment_sla_intelligence.router:router",
    "modules.forecasting.router:router",
    "modules.shipment_risk.router:router",
    "modules.stockout_intelligence.router:router",
    "modules.reorder_engine.router:router",
    "modules.returns_intelligence.router:router",
    "modules.ml_registry.router:router",
    "core.api.routes.serving:router",
    "core.api.routes.monitoring:router",
    "core.api.routes.setup:router",
    "modules.cdc.router:router",
    "modules.streaming.router:router",
    "modules.lakehouse.router:router",
    "modules.query_layer.router:router",
    "modules.metadata.router:router",
    "modules.feature_store.router:router",
    "modules.advanced_serving.router:router",
    "core.api.routes.pro_platform:router",
)


def build_repository() -> RepositoryProtocol:
    settings = get_settings()
    database_url = settings.effective_database_url
    if database_url:
        try:
            repository: RepositoryProtocol = SqlRepository(database_url)
            repository.ensure_tables()
            return repository
        except Exception:
            pass

    repository = MemoryRepository()
    repository.ensure_tables()
    return repository


def _load_router(path: str) -> Any | None:
    module_path, attribute_name = path.split(":", 1)
    try:
        module = import_module(module_path)
    except ModuleNotFoundError as exc:
        optional_dependencies = OPTIONAL_ROUTER_DEPENDENCIES.get(path)
        missing_module = (exc.name or "").split(".", 1)[0]
        if optional_dependencies and missing_module in optional_dependencies:
            return None
        raise
    return getattr(module, attribute_name)


def create_app(repository: RepositoryProtocol | None = None) -> FastAPI:
    get_settings.cache_clear()
    settings = get_settings()
    repo = repository or build_repository()
    app = FastAPI(
        title="RetailOps Data & AI Platform API",
        version="0.1.0",
        description=(
            "Modular API for connectors, easy CSV onboarding, trusted transformations, "
            "KPI analytics, operational intelligence, model lifecycle controls, setup "
            "automation, business review reporting, and optional platform-extension "
            "services such as CDC, streaming, lakehouse, metadata, feature-store, "
            "query-layer, and advanced-serving deployment bundles."
        ),
    )
    app.state.repository = repo
    app.state.state_store = StateStore(repo)
    app.state.raw_loader = RawLoader(repo)
    app.state.registry = build_default_registry(settings.enabled_connector_values)
    @app.middleware("http")
    async def assign_request_id(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())[:8]
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    skipped_optional_routers: list[str] = []
    for router_path in ROUTER_PATHS:
        router = _load_router(router_path)
        if router is None:
            skipped_optional_routers.append(router_path)
            continue
        app.include_router(router)
    app.state.skipped_optional_routers = skipped_optional_routers

    @app.exception_handler(HTTPException)
    async def app_http_exception_handler(request: Request, exc: HTTPException):
        detail_text = str(exc.detail)
        if exc.status_code >= 500:
            entry = log_error(
                request=request,
                title="HTTP application error",
                detail=detail_text,
                status_code=exc.status_code,
                context={"handler": "http_exception"},
            )
        else:
            entry = None
        if is_html_request(request):
            page = render_error_page(
                title="RetailOps page error",
                detail=detail_text,
                request=request,
                status_code=exc.status_code,
                entry=entry,
            )
            return HTMLResponse(page, status_code=exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": getattr(request.state, "request_id", "n/a"),
            },
        )

    @app.exception_handler(Exception)
    async def app_unhandled_exception_handler(request: Request, exc: Exception):
        entry = log_error(
            request=request,
            title="Unhandled application exception",
            detail=str(exc) or "Internal Server Error",
            status_code=500,
            exc=exc,
            context={"handler": "exception"},
        )
        if is_html_request(request):
            page = render_error_page(
                title="RetailOps internal server error",
                detail=str(exc) or "Internal Server Error",
                request=request,
                status_code=500,
                entry=entry,
            )
            return HTMLResponse(page, status_code=500)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "request_id": getattr(request.state, "request_id", "n/a"),
            },
        )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "profile": settings.app_profile,
            "enabled_connectors": ",".join(settings.enabled_connector_values),
            "enabled_optional_extras": ",".join(settings.enabled_optional_extra_values) or "none",
            "skipped_optional_routers": ",".join(app.state.skipped_optional_routers) or "none",
        }

    return app


app = create_app()
