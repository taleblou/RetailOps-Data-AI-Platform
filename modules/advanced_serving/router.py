from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import Phase20AdvancedServingBlueprintResponse
from .service import build_phase20_advanced_serving_artifact

router = APIRouter(prefix="/api/v1/pro/advanced-serving", tags=["phase20-advanced-serving"])


@router.get("/blueprint", response_model=Phase20AdvancedServingBlueprintResponse)
async def get_advanced_serving_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/advanced_serving"),
    refresh: bool = Query(default=False),
) -> Phase20AdvancedServingBlueprintResponse:
    try:
        payload = build_phase20_advanced_serving_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Phase20AdvancedServingBlueprintResponse.model_validate(payload)
