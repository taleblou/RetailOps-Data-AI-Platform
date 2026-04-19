# Project:      RetailOps Data & AI Platform
# Module:       modules.feature_store
# File:         router.py
# Path:         modules/feature_store/router.py
#
# Summary:      Defines API routes for the feature-store module.
# Purpose:      Exposes HTTP endpoints for feature-store deployment bundles.
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

from .schemas import FeatureStoreBlueprintResponse
from .service import build_feature_store_artifact

router = APIRouter(prefix="/api/v1/pro/feature-store", tags=["feature-store"])


@router.get("/bundle", response_model=FeatureStoreBlueprintResponse)
@router.get("/blueprint", response_model=FeatureStoreBlueprintResponse)
async def get_feature_store_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/feature_store"),
    refresh: bool = Query(default=False),
) -> FeatureStoreBlueprintResponse:
    try:
        payload = build_feature_store_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FeatureStoreBlueprintResponse.model_validate(payload)
