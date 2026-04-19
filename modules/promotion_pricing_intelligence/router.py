# Project:      RetailOps Data & AI Platform
# Module:       modules.promotion_pricing_intelligence
# File:         router.py
# Path:         modules/promotion_pricing_intelligence/router.py
#
# Summary:      Defines API routes for the promotion pricing intelligence module.
# Purpose:      Exposes HTTP endpoints for promotion pricing intelligence capabilities.
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
#   - Key APIs: router, get_promotion_summary, get_promotion_sku
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import PromotionPricingArtifactResponse, PromotionSkuResponse
from .service import get_promotion_pricing_artifact, get_promotion_pricing_sku

router = APIRouter(prefix="/api/v1/promotion-pricing", tags=["promotion-pricing"])


@router.get("/summary", response_model=PromotionPricingArtifactResponse)
async def get_promotion_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/promotion_pricing"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> PromotionPricingArtifactResponse:
    try:
        payload = get_promotion_pricing_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PromotionPricingArtifactResponse.model_validate(payload)


@router.get("/skus/{sku}", response_model=PromotionSkuResponse)
async def get_promotion_sku(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/promotion_pricing"),
    refresh: bool = Query(default=False),
) -> PromotionSkuResponse:
    try:
        payload = get_promotion_pricing_sku(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PromotionSkuResponse.model_validate(payload)
