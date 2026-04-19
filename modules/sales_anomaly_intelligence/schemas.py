# Project:      RetailOps Data & AI Platform
# Module:       modules.sales_anomaly_intelligence
# File:         schemas.py
# Path:         modules/sales_anomaly_intelligence/schemas.py
#
# Summary:      Defines schemas for the sales anomaly intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the sales anomaly intelligence layer.
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
#   - Main types: SalesAnomalySummaryResponse, SalesAnomalyDetailResponse, SalesAnomalyArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class SalesAnomalySummaryResponse(BaseModel):
    day_count: int
    anomaly_count: int
    spike_count: int
    drop_count: int
    largest_positive_delta_ratio: float
    largest_negative_delta_ratio: float


class SalesAnomalyDetailResponse(BaseModel):
    order_date: str
    revenue: float
    order_count: int
    quantity: float
    dominant_category: str
    baseline_revenue: float
    delta_ratio: float
    anomaly_type: str


class SalesAnomalyArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: SalesAnomalySummaryResponse
    days: list[SalesAnomalyDetailResponse] = Field(default_factory=list)
