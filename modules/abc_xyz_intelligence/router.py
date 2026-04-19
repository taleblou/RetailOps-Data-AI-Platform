# Project:      RetailOps Data & AI Platform
# Module:       modules.abc_xyz_intelligence
# File:         router.py
# Path:         modules/abc_xyz_intelligence/router.py
#
# Summary:      Defines API routes for the abc xyz intelligence module.
# Purpose:      Exposes HTTP endpoints for abc xyz intelligence capabilities.
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
#   - Key APIs: router, get_abc_xyz_summary, get_abc_xyz_detail
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import AbcXyzArtifactResponse, AbcXyzSkuResponse
from .service import get_abc_xyz_artifact, get_abc_xyz_sku

router = APIRouter(prefix="/api/v1/abc-xyz", tags=["abc-xyz"])


@router.get("/summary", response_model=AbcXyzArtifactResponse)
async def get_abc_xyz_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/abc_xyz_intelligence"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> AbcXyzArtifactResponse:
    try:
        payload = get_abc_xyz_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AbcXyzArtifactResponse.model_validate(payload)


@router.get("/skus/{sku}", response_model=AbcXyzSkuResponse)
async def get_abc_xyz_detail(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/abc_xyz_intelligence"),
    refresh: bool = Query(default=False),
) -> AbcXyzSkuResponse:
    try:
        payload = get_abc_xyz_sku(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AbcXyzSkuResponse.model_validate(payload)
