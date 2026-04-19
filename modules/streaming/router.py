# Project:      RetailOps Data & AI Platform
# Module:       modules.streaming
# File:         router.py
# Path:         modules/streaming/router.py
#
# Summary:      Defines API routes for the streaming module.
# Purpose:      Exposes HTTP endpoints for streaming deployment bundles.
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

from .schemas import StreamingBlueprintResponse
from .service import build_streaming_artifact

router = APIRouter(prefix="/api/v1/pro/streaming", tags=["streaming"])


@router.get("/bundle", response_model=StreamingBlueprintResponse)
@router.get("/blueprint", response_model=StreamingBlueprintResponse)
async def get_streaming_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/streaming"),
    refresh: bool = Query(default=False),
) -> StreamingBlueprintResponse:
    try:
        payload = build_streaming_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StreamingBlueprintResponse.model_validate(payload)
