# Project:      RetailOps Data & AI Platform
# Module:       modules.ml_registry
# File:         router.py
# Path:         modules/ml_registry/router.py
#
# Summary:      Defines API routes for the ml registry module.
# Purpose:      Exposes HTTP endpoints for ml registry capabilities.
# Scope:        public API
# Status:       stable
#
# Author(s):    Morteza Taleblou
# Website:      https://taleblou.ir/
# Repository:   https://github.com/taleblou/RetailOps-Data-AI-Platform
#
# License:      Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
# Copyright:    (c) 2025 Morteza Taleblou
#
# Notes:
#   - Main types: None.
#   - Key APIs: router, get_model_registry_summary_endpoint, get_model_registry_details_endpoint, promote_model_registry_candidate, rollback_model_registry_candidate
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    ModelRegistryDetailsResponse,
    ModelRegistryPromotionRequest,
    ModelRegistryRollbackRequest,
    ModelRegistrySummaryResponse,
)
from .service import (
    ModelRegistryNotFoundError,
    promote_registry_model,
    rollback_registry_model,
)
from .service import (
    get_model_registry_details as fetch_model_registry_details,
)
from .service import (
    get_model_registry_summary as fetch_model_registry_summary,
)

router = APIRouter(prefix="/api/v1/ml-registry", tags=["ml-registry"])


@router.get("/summary", response_model=ModelRegistrySummaryResponse)
async def get_model_registry_summary_endpoint(
    artifact_dir: str = Query(default="data/artifacts/model_registry"),
    refresh: bool = Query(default=False),
) -> ModelRegistrySummaryResponse:
    try:
        payload = fetch_model_registry_summary(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ModelRegistrySummaryResponse.model_validate(payload)


@router.get("/models/{registry_name}", response_model=ModelRegistryDetailsResponse)
async def get_model_registry_details_endpoint(
    registry_name: str,
    artifact_dir: str = Query(default="data/artifacts/model_registry"),
    refresh: bool = Query(default=False),
) -> ModelRegistryDetailsResponse:
    try:
        payload = fetch_model_registry_details(
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
        result = promote_registry_model(
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
        result = rollback_registry_model(
            registry_name=registry_name,
            artifact_dir=Path(artifact_dir),
            target_version=payload.target_version,
        )
    except ModelRegistryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ModelRegistryDetailsResponse.model_validate(result)
