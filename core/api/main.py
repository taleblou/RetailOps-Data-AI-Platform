from __future__ import annotations

from fastapi import FastAPI

from config.settings import get_settings
from core.api.routes.easy_csv import router as easy_csv_router
from core.api.routes.monitoring import router as monitoring_router
from core.api.routes.pro_platform import router as pro_platform_router
from core.api.routes.serving import router as serving_router
from core.api.routes.setup import router as setup_router
from core.api.routes.sources import router as sources_router
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.registry import build_default_registry
from core.ingestion.base.repository import (
    MemoryRepository,
    RepositoryProtocol,
    SqlRepository,
)
from core.ingestion.base.state_store import StateStore
from modules.advanced_serving.router import router as advanced_serving_router
from modules.analytics_kpi import router as analytics_kpi_router
from modules.cdc.router import router as cdc_router
from modules.feature_store.router import router as feature_store_router
from modules.forecasting.router import router as forecasting_router
from modules.lakehouse.router import router as lakehouse_router
from modules.metadata.router import router as metadata_router
from modules.ml_registry.router import router as ml_registry_router
from modules.query_layer.router import router as query_layer_router
from modules.reorder_engine.router import router as reorder_engine_router
from modules.returns_intelligence.router import router as returns_intelligence_router
from modules.shipment_risk.router import router as shipment_risk_router
from modules.stockout_intelligence.router import router as stockout_intelligence_router
from modules.streaming.router import router as streaming_router


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


def create_app(repository: RepositoryProtocol | None = None) -> FastAPI:
    repo = repository or build_repository()
    app = FastAPI(
        title="RetailOps Data & AI Platform API",
        version="0.1.0",
        description=(
            "Phases 5 to 15 API for connectors, easy CSV onboarding, KPI analytics, "
            "forecasting, shipment risk, stockout intelligence, reorder recommendations, "
            "returns intelligence, ML registry lifecycle controls, a phase 16 serving "
            "layer with batch jobs and explain endpoints, and a phase 17 monitoring "
            "layer for governance, drift checks, and manual override logging, "
            "plus a phase 18 setup wizard for onboarding, stateful progress, "
            "retry-aware steps, and sample-data startup, and a phase 20 Pro "
            "data-platform layer for CDC, streaming, lakehouse, query federation, "
            "metadata, feature-store, and advanced-serving blueprints."
        ),
    )
    app.state.repository = repo
    app.state.state_store = StateStore(repo)
    app.state.raw_loader = RawLoader(repo)
    app.state.registry = build_default_registry()
    app.include_router(sources_router)
    app.include_router(easy_csv_router)
    app.include_router(analytics_kpi_router)
    app.include_router(forecasting_router)
    app.include_router(shipment_risk_router)
    app.include_router(stockout_intelligence_router)
    app.include_router(reorder_engine_router)
    app.include_router(returns_intelligence_router)
    app.include_router(ml_registry_router)
    app.include_router(serving_router)
    app.include_router(monitoring_router)
    app.include_router(setup_router)
    app.include_router(cdc_router)
    app.include_router(streaming_router)
    app.include_router(lakehouse_router)
    app.include_router(query_layer_router)
    app.include_router(metadata_router)
    app.include_router(feature_store_router)
    app.include_router(advanced_serving_router)
    app.include_router(pro_platform_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
