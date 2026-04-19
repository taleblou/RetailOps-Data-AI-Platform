# Project:      RetailOps Data & AI Platform
# Module:       modules.lakehouse
# File:         router.py
# Path:         modules/lakehouse/router.py
#
# Summary:      Defines API routes for the lakehouse module.
# Purpose:      Exposes HTTP endpoints for lakehouse deployment bundles.
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

from .schemas import LakehouseBlueprintResponse
from .service import build_lakehouse_artifact

router = APIRouter(prefix="/api/v1/pro/lakehouse", tags=["lakehouse"])


@router.get("/bundle", response_model=LakehouseBlueprintResponse)
@router.get("/blueprint", response_model=LakehouseBlueprintResponse)
async def get_lakehouse_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/lakehouse"),
    refresh: bool = Query(default=False),
) -> LakehouseBlueprintResponse:
    try:
        payload = build_lakehouse_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return LakehouseBlueprintResponse.model_validate(payload)
