# Project:      RetailOps Data & AI Platform
# Module:       modules.forecasting
# File:         router.py
# Path:         modules/forecasting/router.py
#
# Summary:      Defines API routes for the forecasting module.
# Purpose:      Exposes HTTP endpoints for forecasting capabilities.
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
#   - Key APIs: router, get_forecast_summary, get_forecast_product
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import ForecastProductResponse, ForecastSummaryResponse
from .service import (
    ForecastArtifactNotFoundError,
    get_or_create_batch_forecast_artifact,
    get_product_forecast,
)

router = APIRouter(prefix="/api/v1/forecast", tags=["forecasting"])


@router.get("/summary", response_model=ForecastSummaryResponse)
async def get_forecast_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/forecasts"),
    refresh: bool = Query(default=False),
) -> ForecastSummaryResponse:
    try:
        artifact = get_or_create_batch_forecast_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    summary = artifact.get("summary")
    if not isinstance(summary, dict):
        raise HTTPException(
            status_code=500, detail="Forecast artifact is missing the summary block."
        )

    response_payload = {
        "forecast_run_id": artifact.get("forecast_run_id"),
        "upload_id": artifact.get("upload_id"),
        "generated_at": artifact.get("generated_at"),
        "model_version": artifact.get("model_version"),
        "active_products": summary.get("active_products", 0),
        "categories": summary.get("categories") or [],
        "product_groups": summary.get("product_groups") or [],
        "nightly_batch_job": summary.get("nightly_batch_job", ""),
        "model_candidates": summary.get("model_candidates") or [],
        "champion_model_counts": summary.get("champion_model_counts") or {},
        "average_metrics": summary.get("average_metrics")
        or {
            "mae": 0.0,
            "rmse": 0.0,
            "mape": 0.0,
            "bias": 0.0,
        },
        "category_metrics": artifact.get("category_metrics") or [],
        "product_group_metrics": artifact.get("product_group_metrics") or [],
        "artifact_path": artifact.get("artifact_path", ""),
    }
    return ForecastSummaryResponse.model_validate(response_payload)


@router.get("/products/{product_id}", response_model=ForecastProductResponse)
async def get_forecast_product(
    product_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/forecasts"),
    refresh: bool = Query(default=False),
) -> ForecastProductResponse:
    try:
        product = get_product_forecast(
            upload_id=upload_id,
            product_id=product_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except ForecastArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ForecastProductResponse.model_validate(product)
