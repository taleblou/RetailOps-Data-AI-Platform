# Project:      RetailOps Data & AI Platform
# Module:       modules.seasonality_intelligence
# File:         router.py
# Path:         modules/seasonality_intelligence/router.py
#
# Summary:      Defines API routes for the seasonality intelligence module.
# Purpose:      Exposes HTTP endpoints for seasonality intelligence capabilities.
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
#   - Key APIs: router, get_seasonality_summary, get_seasonality_detail
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import SeasonalityArtifactResponse, SeasonalitySkuResponse
from .service import get_seasonality_artifact, get_seasonality_sku

router = APIRouter(prefix="/api/v1/seasonality", tags=["seasonality"])


@router.get("/summary", response_model=SeasonalityArtifactResponse)
async def get_seasonality_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/seasonality_intelligence"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> SeasonalityArtifactResponse:
    try:
        payload = get_seasonality_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SeasonalityArtifactResponse.model_validate(payload)


@router.get("/skus/{sku}", response_model=SeasonalitySkuResponse)
async def get_seasonality_detail(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/seasonality_intelligence"),
    refresh: bool = Query(default=False),
) -> SeasonalitySkuResponse:
    try:
        payload = get_seasonality_sku(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SeasonalitySkuResponse.model_validate(payload)
