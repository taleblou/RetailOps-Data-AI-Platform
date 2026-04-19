# Project:      RetailOps Data & AI Platform
# Module:       modules.returns_intelligence
# File:         router.py
# Path:         modules/returns_intelligence/router.py
#
# Summary:      Defines API routes for the returns intelligence module.
# Purpose:      Exposes HTTP endpoints for returns intelligence capabilities.
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
#   - Key APIs: router, list_return_risk_orders, get_return_risk_order_detail, list_return_risk_products
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import ReturnRiskArtifactResponse, ReturnRiskPredictionResponse
from .service import (
    ReturnRiskArtifactNotFoundError,
    get_return_risk_order,
    get_return_risk_products,
    get_return_risk_scores,
)

router = APIRouter(prefix="/api/v1/returns-risk", tags=["returns-risk"])


@router.get("/orders", response_model=ReturnRiskArtifactResponse)
async def list_return_risk_orders(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/returns_risk"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    store_code: str | None = Query(default=None),
    risk_band: str | None = Query(default=None),
) -> ReturnRiskArtifactResponse:
    try:
        payload = get_return_risk_scores(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
            store_code=store_code,
            risk_band=risk_band,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReturnRiskArtifactResponse.model_validate(payload)


@router.get("/orders/{order_id}", response_model=ReturnRiskPredictionResponse)
async def get_return_risk_order_detail(
    order_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/returns_risk"),
    refresh: bool = Query(default=False),
) -> ReturnRiskPredictionResponse:
    try:
        payload = get_return_risk_order(
            upload_id=upload_id,
            order_id=order_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except ReturnRiskArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReturnRiskPredictionResponse.model_validate(payload)


@router.get("/products", response_model=ReturnRiskArtifactResponse)
async def list_return_risk_products(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/returns_risk"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    store_code: str | None = Query(default=None),
    min_probability: float = Query(default=0.0, ge=0.0, le=1.0),
) -> ReturnRiskArtifactResponse:
    try:
        payload = get_return_risk_products(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
            store_code=store_code,
            min_probability=min_probability,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReturnRiskArtifactResponse.model_validate(payload)
