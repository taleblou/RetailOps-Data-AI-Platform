# Project:      RetailOps Data & AI Platform
# Module:       core.api.routes
# File:         monitoring.py
# Path:         core/api/routes/monitoring.py
#
# Summary:      Defines public API routes and request handling for the API routes surface.
# Purpose:      Exposes HTTP entry points for API routes workflows.
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
#   - Key APIs: router, run_monitoring_checks, get_monitoring_summary,
#     post_manual_override, get_override_summary_endpoint
#   - Dependencies: __future__, pathlib, fastapi, core.monitoring.schemas,
#     core.monitoring.service
#   - Constraints: Public request and response behavior should remain backward
#     compatible with documented API flows.
#   - Compatibility: Python 3.12+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from core.monitoring.schemas import (
    MonitoringArtifactResponse,
    MonitoringOverrideEntryResponse,
    MonitoringOverrideRequest,
    MonitoringOverrideSummaryResponse,
)
from core.monitoring.service import (
    get_or_create_monitoring_artifact,
    get_override_summary as fetch_override_summary,
    log_manual_override as record_manual_override,
)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.post("/run", response_model=MonitoringArtifactResponse)
async def run_monitoring_checks(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    forecast_artifact_dir: str = Query(default="data/artifacts/forecasts"),
    shipment_artifact_dir: str = Query(default="data/artifacts/shipment_risk"),
    stockout_artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    serving_artifact_dir: str = Query(default="data/artifacts/serving"),
    registry_artifact_dir: str = Query(default="data/artifacts/model_registry"),
    artifact_dir: str = Query(default="data/artifacts/monitoring"),
    override_dir: str = Query(default="data/artifacts/monitoring/overrides"),
    refresh: bool = Query(default=False),
) -> MonitoringArtifactResponse:
    try:
        payload = get_or_create_monitoring_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            forecast_artifact_dir=Path(forecast_artifact_dir),
            shipment_artifact_dir=Path(shipment_artifact_dir),
            stockout_artifact_dir=Path(stockout_artifact_dir),
            serving_artifact_dir=Path(serving_artifact_dir),
            registry_artifact_dir=Path(registry_artifact_dir),
            artifact_dir=Path(artifact_dir),
            override_dir=Path(override_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MonitoringArtifactResponse.model_validate(payload)


@router.get("/summary", response_model=MonitoringArtifactResponse)
async def get_monitoring_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    forecast_artifact_dir: str = Query(default="data/artifacts/forecasts"),
    shipment_artifact_dir: str = Query(default="data/artifacts/shipment_risk"),
    stockout_artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    serving_artifact_dir: str = Query(default="data/artifacts/serving"),
    registry_artifact_dir: str = Query(default="data/artifacts/model_registry"),
    artifact_dir: str = Query(default="data/artifacts/monitoring"),
    override_dir: str = Query(default="data/artifacts/monitoring/overrides"),
    refresh: bool = Query(default=False),
) -> MonitoringArtifactResponse:
    try:
        payload = get_or_create_monitoring_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            forecast_artifact_dir=Path(forecast_artifact_dir),
            shipment_artifact_dir=Path(shipment_artifact_dir),
            stockout_artifact_dir=Path(stockout_artifact_dir),
            serving_artifact_dir=Path(serving_artifact_dir),
            registry_artifact_dir=Path(registry_artifact_dir),
            artifact_dir=Path(artifact_dir),
            override_dir=Path(override_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MonitoringArtifactResponse.model_validate(payload)


@router.post("/overrides", response_model=MonitoringOverrideEntryResponse)
async def post_manual_override(
    payload: MonitoringOverrideRequest,
) -> MonitoringOverrideEntryResponse:
    try:
        result = record_manual_override(
            upload_id=payload.upload_id,
            prediction_type=payload.prediction_type,
            entity_id=payload.entity_id,
            original_decision=payload.original_decision,
            override_decision=payload.override_decision,
            reason=payload.reason,
            override_dir=Path(payload.override_dir),
            feedback_label=payload.feedback_label,
            user_id=payload.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MonitoringOverrideEntryResponse.model_validate(result)


@router.get("/overrides", response_model=MonitoringOverrideSummaryResponse)
async def get_override_summary_endpoint(
    upload_id: str = Query(...),
    override_dir: str = Query(default="data/artifacts/monitoring/overrides"),
) -> MonitoringOverrideSummaryResponse:
    try:
        payload = fetch_override_summary(
            upload_id=upload_id,
            override_dir=Path(override_dir),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MonitoringOverrideSummaryResponse.model_validate(payload)
