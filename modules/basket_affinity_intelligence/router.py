# Project:      RetailOps Data & AI Platform
# Module:       modules.basket_affinity_intelligence
# File:         router.py
# Path:         modules/basket_affinity_intelligence/router.py
#
# Summary:      Defines API routes for the basket affinity intelligence module.
# Purpose:      Exposes HTTP endpoints for basket affinity intelligence capabilities.
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
#   - Key APIs: router, get_basket_summary, get_basket_pair_detail
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import BasketAffinityArtifactResponse, BasketPairResponse
from .service import get_basket_affinity_artifact, get_basket_pair

router = APIRouter(prefix="/api/v1/basket-affinity", tags=["basket-affinity"])


@router.get("/summary", response_model=BasketAffinityArtifactResponse)
async def get_basket_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/basket_affinity"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> BasketAffinityArtifactResponse:
    try:
        payload = get_basket_affinity_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BasketAffinityArtifactResponse.model_validate(payload)


@router.get("/pairs/{left_sku}/{right_sku}", response_model=BasketPairResponse)
async def get_basket_pair_detail(
    left_sku: str,
    right_sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/basket_affinity"),
    refresh: bool = Query(default=False),
) -> BasketPairResponse:
    try:
        payload = get_basket_pair(
            upload_id=upload_id,
            left_sku=left_sku,
            right_sku=right_sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BasketPairResponse.model_validate(payload)
