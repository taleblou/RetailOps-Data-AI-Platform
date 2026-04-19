# Project:      RetailOps Data & AI Platform
# Module:       modules.dashboard_hub
# File:         router.py
# Path:         modules/dashboard_hub/router.py
#
# Summary:      Defines API and dashboard UI routes for the dashboard hub module.
# Purpose:      Exposes JSON artifacts and a separated /dashboard admin UI.
# Scope:        public API
# Status:       stable

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from .admin_ui import render_dashboard_html
from .schemas import (
    DashboardWorkspaceArtifactResponse,
    DashboardWorkspacePublishRequest,
    DashboardWorkspaceResponse,
)
from .service import (
    build_dashboard_workspace,
    load_dashboard_workspace_artifact,
    publish_dashboard_workspace,
)

router = APIRouter(tags=["dashboard-hub"])
api_router = APIRouter(prefix="/api/v1/dashboard-hub", tags=["dashboard-hub"])


def _workspace_payload(
    *,
    upload_id: str,
    uploads_dir: str,
    artifact_root: str,
    refresh: bool,
    max_rows: int,
) -> dict[str, object]:
    return build_dashboard_workspace(
        upload_id=upload_id,
        uploads_dir=Path(uploads_dir),
        artifact_root=Path(artifact_root),
        refresh=refresh,
        max_rows=max_rows,
    )


@api_router.get("/workspace", response_model=DashboardWorkspaceResponse)
async def get_dashboard_workspace(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_root: str = Query(default="data/artifacts/dashboard_hub"),
    refresh: bool = Query(default=False),
    max_rows: int = Query(default=8, ge=3, le=20),
) -> DashboardWorkspaceResponse:
    try:
        payload = _workspace_payload(
            upload_id=upload_id,
            uploads_dir=uploads_dir,
            artifact_root=artifact_root,
            refresh=refresh,
            max_rows=max_rows,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DashboardWorkspaceResponse.model_validate(payload)


@api_router.post("/publish", response_model=DashboardWorkspaceArtifactResponse)
async def publish_workspace(
    payload: DashboardWorkspacePublishRequest,
) -> DashboardWorkspaceArtifactResponse:
    try:
        result = publish_dashboard_workspace(
            upload_id=payload.upload_id,
            uploads_dir=Path(payload.uploads_dir),
            artifact_root=Path(payload.artifact_root),
            refresh=payload.refresh,
            max_rows=payload.max_rows,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DashboardWorkspaceArtifactResponse.model_validate(result)


@api_router.get("/artifact/{upload_id}", response_model=DashboardWorkspaceArtifactResponse)
async def get_published_workspace_artifact(
    upload_id: str,
    artifact_root: str = Query(default="data/artifacts/dashboard_hub"),
) -> DashboardWorkspaceArtifactResponse:
    try:
        payload = load_dashboard_workspace_artifact(
            upload_id=upload_id,
            artifact_root=Path(artifact_root),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DashboardWorkspaceArtifactResponse.model_validate(payload)


@api_router.get("/{upload_id}/view")
async def redirect_dashboard_workspace_html(upload_id: str) -> RedirectResponse:
    return RedirectResponse(url=f"/dashboard/{upload_id}", status_code=307)


def _dashboard_page_response(
    *,
    upload_id: str,
    page: str,
    uploads_dir: str,
    artifact_root: str,
    refresh: bool,
    max_rows: int,
) -> HTMLResponse:
    try:
        workspace = _workspace_payload(
            upload_id=upload_id,
            uploads_dir=uploads_dir,
            artifact_root=artifact_root,
            refresh=refresh,
            max_rows=max_rows,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    html = render_dashboard_html(
        workspace=workspace,
        page=page,
        project_root=Path.cwd(),
    )
    return HTMLResponse(html)


@router.get("/dashboard/{upload_id}", response_class=HTMLResponse)
async def get_dashboard_root(
    upload_id: str,
    uploads_dir: str = Query(default="data/uploads"),
    artifact_root: str = Query(default="data/artifacts/dashboard_hub"),
    refresh: bool = Query(default=False),
    max_rows: int = Query(default=8, ge=3, le=20),
) -> HTMLResponse:
    return _dashboard_page_response(
        upload_id=upload_id,
        page="overview",
        uploads_dir=uploads_dir,
        artifact_root=artifact_root,
        refresh=refresh,
        max_rows=max_rows,
    )


@router.get("/dashboard/{upload_id}/{page}", response_class=HTMLResponse)
async def get_dashboard_page(
    upload_id: str,
    page: str,
    uploads_dir: str = Query(default="data/uploads"),
    artifact_root: str = Query(default="data/artifacts/dashboard_hub"),
    refresh: bool = Query(default=False),
    max_rows: int = Query(default=8, ge=3, le=20),
) -> HTMLResponse:
    return _dashboard_page_response(
        upload_id=upload_id,
        page=page,
        uploads_dir=uploads_dir,
        artifact_root=artifact_root,
        refresh=refresh,
        max_rows=max_rows,
    )


router.include_router(api_router)
