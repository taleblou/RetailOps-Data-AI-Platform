# Project:      RetailOps Data & AI Platform
# Module:       modules.cdc
# File:         router.py
# Path:         modules/cdc/router.py
#
# Summary:      Defines API routes for the CDC module.
# Purpose:      Exposes HTTP endpoints for CDC deployment bundles.
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

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import CdcBlueprintResponse
from .service import build_cdc_artifact

router = APIRouter(prefix="/api/v1/pro/cdc", tags=["cdc"])


@router.get("/bundle", response_model=CdcBlueprintResponse)
@router.get("/blueprint", response_model=CdcBlueprintResponse)
async def get_cdc_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/cdc"),
    refresh: bool = Query(default=False),
) -> CdcBlueprintResponse:
    try:
        payload = build_cdc_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CdcBlueprintResponse.model_validate(payload)
