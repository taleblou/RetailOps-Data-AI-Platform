from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import Phase20FeatureStoreBlueprintResponse
from .service import build_phase20_feature_store_artifact

router = APIRouter(prefix="/api/v1/pro/feature-store", tags=["phase20-feature-store"])


@router.get("/blueprint", response_model=Phase20FeatureStoreBlueprintResponse)
async def get_feature_store_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/feature_store"),
    refresh: bool = Query(default=False),
) -> Phase20FeatureStoreBlueprintResponse:
    try:
        payload = build_phase20_feature_store_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Phase20FeatureStoreBlueprintResponse.model_validate(payload)
