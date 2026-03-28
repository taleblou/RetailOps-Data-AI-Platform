from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import Phase20MetadataBlueprintResponse
from .service import build_phase20_metadata_artifact

router = APIRouter(prefix="/api/v1/pro/metadata", tags=["phase20-metadata"])


@router.get("/blueprint", response_model=Phase20MetadataBlueprintResponse)
async def get_metadata_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/metadata"),
    refresh: bool = Query(default=False),
) -> Phase20MetadataBlueprintResponse:
    try:
        payload = build_phase20_metadata_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Phase20MetadataBlueprintResponse.model_validate(payload)
