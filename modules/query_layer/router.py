# Project:      RetailOps Data & AI Platform
# Module:       modules.query_layer
# File:         router.py
# Path:         modules/query_layer/router.py
#
# Summary:      Defines API routes for the query-layer module.
# Purpose:      Exposes HTTP endpoints for query-layer deployment bundles.
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

from .schemas import QueryLayerBlueprintResponse
from .service import build_query_layer_artifact

router = APIRouter(prefix="/api/v1/pro/query-layer", tags=["query-layer"])


@router.get("/bundle", response_model=QueryLayerBlueprintResponse)
@router.get("/blueprint", response_model=QueryLayerBlueprintResponse)
async def get_query_layer_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/query_layer"),
    refresh: bool = Query(default=False),
) -> QueryLayerBlueprintResponse:
    try:
        payload = build_query_layer_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QueryLayerBlueprintResponse.model_validate(payload)
