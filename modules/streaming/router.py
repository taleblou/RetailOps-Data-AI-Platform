from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import Phase20StreamingBlueprintResponse
from .service import build_phase20_streaming_artifact

router = APIRouter(prefix="/api/v1/pro/streaming", tags=["phase20-streaming"])


@router.get("/blueprint", response_model=Phase20StreamingBlueprintResponse)
async def get_streaming_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/streaming"),
    refresh: bool = Query(default=False),
) -> Phase20StreamingBlueprintResponse:
    try:
        payload = build_phase20_streaming_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Phase20StreamingBlueprintResponse.model_validate(payload)
