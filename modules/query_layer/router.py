from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import Phase20QueryLayerBlueprintResponse
from .service import build_phase20_query_layer_artifact

router = APIRouter(prefix="/api/v1/pro/query-layer", tags=["phase20-query-layer"])


@router.get("/blueprint", response_model=Phase20QueryLayerBlueprintResponse)
async def get_query_layer_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/query_layer"),
    refresh: bool = Query(default=False),
) -> Phase20QueryLayerBlueprintResponse:
    try:
        payload = build_phase20_query_layer_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Phase20QueryLayerBlueprintResponse.model_validate(payload)
