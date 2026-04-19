# Project:      RetailOps Data & AI Platform
# Module:       modules.fulfillment_sla_intelligence
# File:         router.py
# Path:         modules/fulfillment_sla_intelligence/router.py
#
# Summary:      Defines API routes for the fulfillment sla intelligence module.
# Purpose:      Exposes HTTP endpoints for fulfillment sla intelligence capabilities.
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
#   - Key APIs: router, get_fulfillment_sla_summary, get_fulfillment_sla_detail
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import FulfillmentSlaArtifactResponse, FulfillmentSlaOrderResponse
from .service import get_fulfillment_sla_artifact, get_fulfillment_sla_order

router = APIRouter(prefix="/api/v1/fulfillment-sla", tags=["fulfillment-sla"])


@router.get("/summary", response_model=FulfillmentSlaArtifactResponse)
async def get_fulfillment_sla_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/fulfillment_sla_intelligence"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> FulfillmentSlaArtifactResponse:
    try:
        payload = get_fulfillment_sla_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FulfillmentSlaArtifactResponse.model_validate(payload)


@router.get("/orders/{order_id}", response_model=FulfillmentSlaOrderResponse)
async def get_fulfillment_sla_detail(
    order_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/fulfillment_sla_intelligence"),
    refresh: bool = Query(default=False),
) -> FulfillmentSlaOrderResponse:
    try:
        payload = get_fulfillment_sla_order(
            upload_id=upload_id,
            order_id=order_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FulfillmentSlaOrderResponse.model_validate(payload)
