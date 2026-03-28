from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import ReorderRecommendationListResponse, ReorderRecommendationResponse
from .service import (
    ReorderArtifactNotFoundError,
    get_reorder_recommendation,
    get_reorder_recommendations,
)

router = APIRouter(prefix="/api/v1/reorder", tags=["reorder"])


@router.get("/recommendations", response_model=ReorderRecommendationListResponse)
async def list_reorder_recommendations(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    forecast_artifact_dir: str = Query(default="data/artifacts/forecasts"),
    stockout_artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    artifact_dir: str = Query(default="data/artifacts/reorder"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
    store_code: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
) -> ReorderRecommendationListResponse:
    try:
        payload = get_reorder_recommendations(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            forecast_artifact_dir=Path(forecast_artifact_dir),
            stockout_artifact_dir=Path(stockout_artifact_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
            store_code=store_code,
            urgency=urgency,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReorderRecommendationListResponse.model_validate(payload)


@router.get("/{sku}", response_model=ReorderRecommendationResponse)
async def get_reorder_sku(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    forecast_artifact_dir: str = Query(default="data/artifacts/forecasts"),
    stockout_artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    artifact_dir: str = Query(default="data/artifacts/reorder"),
    refresh: bool = Query(default=False),
    store_code: str | None = Query(default=None),
) -> ReorderRecommendationResponse:
    try:
        payload = get_reorder_recommendation(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            forecast_artifact_dir=Path(forecast_artifact_dir),
            stockout_artifact_dir=Path(stockout_artifact_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            store_code=store_code,
        )
    except ReorderArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReorderRecommendationResponse.model_validate(payload)
