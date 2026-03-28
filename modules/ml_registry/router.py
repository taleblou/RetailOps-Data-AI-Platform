from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    ModelRegistryDetailsResponse,
    ModelRegistryPromotionRequest,
    ModelRegistryRollbackRequest,
    Phase15ModelRegistrySummaryResponse,
)
from .service import (
    ModelRegistryNotFoundError,
    get_phase15_registry_details,
    get_phase15_registry_summary,
    promote_phase15_registry_model,
    rollback_phase15_registry_model,
)

router = APIRouter(prefix="/api/v1/ml-registry", tags=["ml-registry"])


@router.get("/summary", response_model=Phase15ModelRegistrySummaryResponse)
async def get_model_registry_summary(
    artifact_dir: str = Query(default="data/artifacts/model_registry"),
    refresh: bool = Query(default=False),
) -> Phase15ModelRegistrySummaryResponse:
    try:
        payload = get_phase15_registry_summary(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Phase15ModelRegistrySummaryResponse.model_validate(payload)


@router.get("/models/{registry_name}", response_model=ModelRegistryDetailsResponse)
async def get_model_registry_details(
    registry_name: str,
    artifact_dir: str = Query(default="data/artifacts/model_registry"),
    refresh: bool = Query(default=False),
) -> ModelRegistryDetailsResponse:
    try:
        payload = get_phase15_registry_details(
            registry_name=registry_name,
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except ModelRegistryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ModelRegistryDetailsResponse.model_validate(payload)


@router.post("/models/{registry_name}/promote", response_model=ModelRegistryDetailsResponse)
async def promote_model_registry_candidate(
    registry_name: str,
    payload: ModelRegistryPromotionRequest,
    artifact_dir: str = Query(default="data/artifacts/model_registry"),
) -> ModelRegistryDetailsResponse:
    try:
        result = promote_phase15_registry_model(
            registry_name=registry_name,
            candidate_alias=payload.candidate_alias,
            artifact_dir=Path(artifact_dir),
        )
    except ModelRegistryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ModelRegistryDetailsResponse.model_validate(result)


@router.post("/models/{registry_name}/rollback", response_model=ModelRegistryDetailsResponse)
async def rollback_model_registry_candidate(
    registry_name: str,
    payload: ModelRegistryRollbackRequest,
    artifact_dir: str = Query(default="data/artifacts/model_registry"),
) -> ModelRegistryDetailsResponse:
    try:
        result = rollback_phase15_registry_model(
            registry_name=registry_name,
            artifact_dir=Path(artifact_dir),
            target_version=payload.target_version,
        )
    except ModelRegistryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ModelRegistryDetailsResponse.model_validate(result)
