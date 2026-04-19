# Project:      RetailOps Data & AI Platform
# Module:       modules.inventory_aging_intelligence
# File:         router.py
# Path:         modules/inventory_aging_intelligence/router.py
#
# Summary:      Defines API routes for the inventory aging intelligence module.
# Purpose:      Exposes HTTP endpoints for inventory aging intelligence capabilities.
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
#   - Key APIs: router, get_inventory_aging_summary, get_inventory_aging_detail
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import InventoryAgingArtifactResponse, InventoryAgingSkuResponse
from .service import get_inventory_aging_artifact, get_inventory_aging_sku

router = APIRouter(prefix="/api/v1/inventory-aging", tags=["inventory-aging"])


@router.get("/summary", response_model=InventoryAgingArtifactResponse)
async def get_inventory_aging_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/inventory_aging_intelligence"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> InventoryAgingArtifactResponse:
    try:
        payload = get_inventory_aging_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InventoryAgingArtifactResponse.model_validate(payload)


@router.get("/skus/{sku}", response_model=InventoryAgingSkuResponse)
async def get_inventory_aging_detail(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/inventory_aging_intelligence"),
    refresh: bool = Query(default=False),
) -> InventoryAgingSkuResponse:
    try:
        payload = get_inventory_aging_sku(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InventoryAgingSkuResponse.model_validate(payload)
