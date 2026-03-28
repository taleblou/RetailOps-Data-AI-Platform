from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import Phase20CdcBlueprintResponse
from .service import build_phase20_cdc_artifact

router = APIRouter(prefix="/api/v1/pro/cdc", tags=["phase20-cdc"])


@router.get("/blueprint", response_model=Phase20CdcBlueprintResponse)
async def get_cdc_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/cdc"),
    refresh: bool = Query(default=False),
) -> Phase20CdcBlueprintResponse:
    try:
        payload = build_phase20_cdc_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Phase20CdcBlueprintResponse.model_validate(payload)
