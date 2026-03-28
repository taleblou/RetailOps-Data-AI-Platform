from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import Phase20LakehouseBlueprintResponse
from .service import build_phase20_lakehouse_artifact

router = APIRouter(prefix="/api/v1/pro/lakehouse", tags=["phase20-lakehouse"])


@router.get("/blueprint", response_model=Phase20LakehouseBlueprintResponse)
async def get_lakehouse_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/lakehouse"),
    refresh: bool = Query(default=False),
) -> Phase20LakehouseBlueprintResponse:
    try:
        payload = build_phase20_lakehouse_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Phase20LakehouseBlueprintResponse.model_validate(payload)
