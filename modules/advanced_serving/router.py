# Project:      RetailOps Data & AI Platform
# Module:       modules.advanced_serving
# File:         router.py
# Path:         modules/advanced_serving/router.py
#
# Summary:      Defines API routes for the advanced-serving module.
# Purpose:      Exposes HTTP endpoints for advanced-serving deployment bundles.
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

from .schemas import AdvancedServingBlueprintResponse
from .service import build_advanced_serving_artifact

router = APIRouter(prefix="/api/v1/pro/advanced-serving", tags=["advanced-serving"])


@router.get("/bundle", response_model=AdvancedServingBlueprintResponse)
@router.get("/blueprint", response_model=AdvancedServingBlueprintResponse)
async def get_advanced_serving_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/advanced_serving"),
    refresh: bool = Query(default=False),
) -> AdvancedServingBlueprintResponse:
    try:
        payload = build_advanced_serving_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AdvancedServingBlueprintResponse.model_validate(payload)
