from __future__ import annotations

from fastapi import FastAPI

from config.settings import get_settings
from core.api.routes.sources import router as sources_router
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.registry import build_default_registry
from core.ingestion.base.repository import (
    MemoryRepository,
    RepositoryProtocol,
    SqlRepository,
)
from core.ingestion.base.state_store import StateStore


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
        title="RetailOps Connector API",
        version="0.1.0",
        description="Phase 5 connector framework for RetailOps.",
    )
    app.state.repository = repo
    app.state.state_store = StateStore(repo)
    app.state.raw_loader = RawLoader(repo)
    app.state.registry = build_default_registry()
    app.include_router(sources_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
