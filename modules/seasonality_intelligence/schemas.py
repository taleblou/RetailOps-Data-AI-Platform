# Project:      RetailOps Data & AI Platform
# Module:       modules.seasonality_intelligence
# File:         schemas.py
# Path:         modules/seasonality_intelligence/schemas.py
#
# Summary:      Defines schemas for the seasonality intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the seasonality intelligence layer.
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
#   - Main types: SeasonalitySummaryResponse, SeasonalitySkuResponse, SeasonalityArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class SeasonalitySummaryResponse(BaseModel):
    sku_count: int
    strong_seasonal_sku_count: int
    moderate_seasonal_sku_count: int
    steady_sku_count: int
    most_common_peak_month: str


class SeasonalitySkuResponse(BaseModel):
    sku: str
    category: str
    total_revenue: float
    active_month_count: int
    peak_month: str
    peak_month_revenue_share: float
    trough_month: str
    seasonality_band: str


class SeasonalityArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: SeasonalitySummaryResponse
    skus: list[SeasonalitySkuResponse] = Field(default_factory=list)
