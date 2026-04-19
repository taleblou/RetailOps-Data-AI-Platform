# Project:      RetailOps Data & AI Platform
# Module:       modules.supplier_procurement_intelligence
# File:         router.py
# Path:         modules/supplier_procurement_intelligence/router.py
#
# Summary:      Defines API routes for the supplier procurement intelligence module.
# Purpose:      Exposes HTTP endpoints for supplier procurement intelligence capabilities.
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
#   - Key APIs: router, get_supplier_summary, get_supplier_detail
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import SupplierProcurementArtifactResponse, SupplierProcurementResponse
from .service import get_supplier_procurement_artifact, get_supplier_procurement_item

router = APIRouter(prefix="/api/v1/supplier-procurement", tags=["supplier-procurement"])


@router.get("/summary", response_model=SupplierProcurementArtifactResponse)
async def get_supplier_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/supplier_procurement"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> SupplierProcurementArtifactResponse:
    try:
        payload = get_supplier_procurement_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SupplierProcurementArtifactResponse.model_validate(payload)


@router.get("/suppliers/{supplier_id}", response_model=SupplierProcurementResponse)
async def get_supplier_detail(
    supplier_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/supplier_procurement"),
    refresh: bool = Query(default=False),
) -> SupplierProcurementResponse:
    try:
        payload = get_supplier_procurement_item(
            upload_id=upload_id,
            supplier_id=supplier_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SupplierProcurementResponse.model_validate(payload)
