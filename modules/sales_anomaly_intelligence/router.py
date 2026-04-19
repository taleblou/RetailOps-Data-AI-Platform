# Project:      RetailOps Data & AI Platform
# Module:       modules.sales_anomaly_intelligence
# File:         router.py
# Path:         modules/sales_anomaly_intelligence/router.py
#
# Summary:      Defines API routes for the sales anomaly intelligence module.
# Purpose:      Exposes HTTP endpoints for sales anomaly intelligence capabilities.
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
#   - Key APIs: router, get_sales_anomaly_summary, get_sales_anomaly_detail
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import SalesAnomalyArtifactResponse, SalesAnomalyDetailResponse
from .service import get_sales_anomaly_artifact, get_sales_anomaly_day

router = APIRouter(prefix="/api/v1/sales-anomalies", tags=["sales-anomalies"])


@router.get("/summary", response_model=SalesAnomalyArtifactResponse)
async def get_sales_anomaly_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/sales_anomaly_intelligence"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=90, ge=1, le=1000),
) -> SalesAnomalyArtifactResponse:
    try:
        payload = get_sales_anomaly_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SalesAnomalyArtifactResponse.model_validate(payload)


@router.get("/days/{order_date}", response_model=SalesAnomalyDetailResponse)
async def get_sales_anomaly_detail(
    order_date: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/sales_anomaly_intelligence"),
    refresh: bool = Query(default=False),
) -> SalesAnomalyDetailResponse:
    try:
        payload = get_sales_anomaly_day(
            upload_id=upload_id,
            order_date=order_date,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SalesAnomalyDetailResponse.model_validate(payload)
