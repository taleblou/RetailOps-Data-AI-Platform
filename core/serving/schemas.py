# Project:      RetailOps Data & AI Platform
# Module:       core.serving
# File:         schemas.py
# Path:         core/serving/schemas.py
#
# Summary:      Defines schemas for the serving data contracts.
# Purpose:      Standardizes structured payloads used by the serving layer.
# Scope:        internal
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
#   - Main types: ServingBatchRunRequest, ServingBatchJobResponse, ServingBatchArtifactResponse, ServingPredictionResponse, ServingExplainResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, typing, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ServingBatchRunRequest(BaseModel):
    upload_id: str
    uploads_dir: str = "data/uploads"
    forecast_artifact_dir: str = "data/artifacts/forecasts"
    shipment_artifact_dir: str = "data/artifacts/shipment_risk"
    stockout_artifact_dir: str = "data/artifacts/stockout_risk"
    artifact_dir: str = "data/artifacts/serving"
    refresh: bool = False


class ServingBatchJobResponse(BaseModel):
    job_name: str
    prediction_type: str
    source_module: str
    status: str
    records_served: int
    generated_at: str
    artifact_path: str


class ServingBatchArtifactResponse(BaseModel):
    serving_run_id: str
    upload_id: str
    generated_at: str
    status: str
    jobs: list[ServingBatchJobResponse] = Field(default_factory=list)
    available_online_endpoints: list[str] = Field(default_factory=list)
    standard_response_fields: list[str] = Field(default_factory=list)
    artifact_path: str


class ServingPredictionResponse(BaseModel):
    serving_type: str
    entity_id: str
    prediction: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    interval: dict[str, Any] | None = None
    model_version: str
    feature_timestamp: str
    explanation_summary: str
    source_artifact: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServingExplainResponse(BaseModel):
    serving_type: str
    entity_id: str
    explanation_summary: str
    top_factors: list[str] = Field(default_factory=list)
    supporting_signals: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str | None = None
    model_version: str
    feature_timestamp: str
    source_artifact: str
