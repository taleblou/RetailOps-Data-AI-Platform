# Project:      RetailOps Data & AI Platform
# Module:       modules.customer_churn_intelligence
# File:         router.py
# Path:         modules/customer_churn_intelligence/router.py
#
# Summary:      Defines API routes for the customer churn intelligence module.
# Purpose:      Exposes HTTP endpoints for customer churn intelligence capabilities.
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
#   - Key APIs: router, get_customer_churn_summary, get_customer_churn_customer
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import CustomerChurnArtifactResponse, CustomerChurnDetailResponse
from .service import get_customer_churn_artifact, get_customer_churn_detail

router = APIRouter(prefix="/api/v1/customer-churn", tags=["customer-churn"])


@router.get("/summary", response_model=CustomerChurnArtifactResponse)
async def get_customer_churn_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/customer_churn_intelligence"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> CustomerChurnArtifactResponse:
    try:
        payload = get_customer_churn_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerChurnArtifactResponse.model_validate(payload)


@router.get("/customers/{customer_id}", response_model=CustomerChurnDetailResponse)
async def get_customer_churn_customer(
    customer_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/customer_churn_intelligence"),
    refresh: bool = Query(default=False),
) -> CustomerChurnDetailResponse:
    try:
        payload = get_customer_churn_detail(
            upload_id=upload_id,
            customer_id=customer_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerChurnDetailResponse.model_validate(payload)
