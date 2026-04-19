# Project:      RetailOps Data & AI Platform
# Module:       modules.stockout_intelligence
# File:         router.py
# Path:         modules/stockout_intelligence/router.py
#
# Summary:      Defines API routes for the stockout intelligence module.
# Purpose:      Exposes HTTP endpoints for stockout intelligence capabilities.
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
#   - Key APIs: router, get_stockout_risk_skus, get_stockout_risk_sku
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import StockoutRiskSkuListResponse, StockoutRiskSkuResponse
from .service import (
    StockoutArtifactNotFoundError,
    get_stockout_sku_prediction,
    get_stockout_sku_predictions,
)

router = APIRouter(prefix="/api/v1/stockout-risk", tags=["stockout-risk"])


@router.get("/skus", response_model=StockoutRiskSkuListResponse)
async def get_stockout_risk_skus(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
    store_code: str | None = Query(default=None),
) -> StockoutRiskSkuListResponse:
    try:
        payload = get_stockout_sku_predictions(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
            store_code=store_code,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StockoutRiskSkuListResponse.model_validate(payload)


@router.get("/{sku}", response_model=StockoutRiskSkuResponse)
async def get_stockout_risk_sku(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    refresh: bool = Query(default=False),
    store_code: str | None = Query(default=None),
) -> StockoutRiskSkuResponse:
    try:
        payload = get_stockout_sku_prediction(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            store_code=store_code,
        )
    except StockoutArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StockoutRiskSkuResponse.model_validate(payload)
