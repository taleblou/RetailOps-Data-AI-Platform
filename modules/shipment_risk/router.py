# Project:      RetailOps Data & AI Platform
# Module:       modules.shipment_risk
# File:         router.py
# Path:         modules/shipment_risk/router.py
#
# Summary:      Defines API routes for the shipment risk module.
# Purpose:      Exposes HTTP endpoints for shipment risk capabilities.
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
#   - Key APIs: router, get_shipment_risk_open_orders, get_shipment_risk_for_shipment, post_predict_shipment_delay, post_manual_review_decision
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    ManualReviewDecisionResponse,
    ShipmentDelayPredictRequest,
    ShipmentRiskOpenOrdersResponse,
    ShipmentRiskPredictionResponse,
)
from .service import (
    ShipmentRiskArtifactNotFoundError,
    build_manual_review_decision,
    get_open_order_prediction,
    get_open_order_predictions,
    predict_shipment_delay,
)

router = APIRouter(prefix="/api/v1", tags=["shipment-risk"])


@router.get("/shipment-risk/open-orders", response_model=ShipmentRiskOpenOrdersResponse)
async def get_shipment_risk_open_orders(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/shipment_risk"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> ShipmentRiskOpenOrdersResponse:
    try:
        payload = get_open_order_predictions(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ShipmentRiskOpenOrdersResponse.model_validate(payload)


@router.get(
    "/shipment-risk/open-orders/{shipment_id}",
    response_model=ShipmentRiskPredictionResponse,
)
async def get_shipment_risk_for_shipment(
    shipment_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/shipment_risk"),
    refresh: bool = Query(default=False),
) -> ShipmentRiskPredictionResponse:
    try:
        payload = get_open_order_prediction(
            upload_id=upload_id,
            shipment_id=shipment_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except ShipmentRiskArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ShipmentRiskPredictionResponse.model_validate(payload)


@router.post("/predict/shipment-delay", response_model=ShipmentRiskPredictionResponse)
async def post_predict_shipment_delay(
    payload: ShipmentDelayPredictRequest,
) -> ShipmentRiskPredictionResponse:
    return ShipmentRiskPredictionResponse.model_validate(
        predict_shipment_delay(payload.model_dump())
    )


@router.post("/shipment-risk/manual-review", response_model=ManualReviewDecisionResponse)
async def post_manual_review_decision(
    payload: ShipmentDelayPredictRequest,
) -> ManualReviewDecisionResponse:
    return ManualReviewDecisionResponse.model_validate(
        build_manual_review_decision(payload.model_dump())
    )
