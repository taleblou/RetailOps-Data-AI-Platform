# Project:      RetailOps Data & AI Platform
# Module:       modules.customer_cohort_intelligence
# File:         router.py
# Path:         modules/customer_cohort_intelligence/router.py
#
# Summary:      Defines API routes for the customer cohort intelligence module.
# Purpose:      Exposes HTTP endpoints for customer cohort intelligence capabilities.
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
#   - Key APIs: router, get_customer_cohort_summary, get_customer_cohort_detail
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import CustomerCohortArtifactResponse, CustomerCohortDetailResponse
from .service import get_cohort_artifact, get_cohort_detail

router = APIRouter(prefix="/api/v1/customer-cohorts", tags=["customer-cohorts"])


@router.get("/summary", response_model=CustomerCohortArtifactResponse)
async def get_customer_cohort_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/customer_cohort_intelligence"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> CustomerCohortArtifactResponse:
    try:
        payload = get_cohort_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerCohortArtifactResponse.model_validate(payload)


@router.get("/cohorts/{cohort_month}", response_model=CustomerCohortDetailResponse)
async def get_customer_cohort_detail(
    cohort_month: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/customer_cohort_intelligence"),
    refresh: bool = Query(default=False),
) -> CustomerCohortDetailResponse:
    try:
        payload = get_cohort_detail(
            upload_id=upload_id,
            cohort_month=cohort_month,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerCohortDetailResponse.model_validate(payload)
