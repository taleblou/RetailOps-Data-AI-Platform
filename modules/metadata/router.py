# Project:      RetailOps Data & AI Platform
# Module:       modules.metadata
# File:         router.py
# Path:         modules/metadata/router.py
#
# Summary:      Defines API routes for the metadata module.
# Purpose:      Exposes HTTP endpoints for metadata deployment bundles.
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

from .schemas import MetadataBlueprintResponse
from .service import build_metadata_artifact

router = APIRouter(prefix="/api/v1/pro/metadata", tags=["metadata"])


@router.get("/bundle", response_model=MetadataBlueprintResponse)
@router.get("/blueprint", response_model=MetadataBlueprintResponse)
async def get_metadata_blueprint(
    artifact_dir: str = Query(default="data/artifacts/pro_platform/metadata"),
    refresh: bool = Query(default=False),
) -> MetadataBlueprintResponse:
    try:
        payload = build_metadata_artifact(
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MetadataBlueprintResponse.model_validate(payload)
