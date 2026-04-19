# Project:      RetailOps Data & AI Platform
# Module:       modules.profitability_intelligence
# File:         schemas.py
# Path:         modules/profitability_intelligence/schemas.py
#
# Summary:      Defines schemas for the profitability intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the profitability intelligence layer.
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
#   - Main types: ProfitabilitySummaryResponse, ProfitabilitySkuResponse, ProfitabilityArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfitabilitySummaryResponse(BaseModel):
    sku_count: int
    order_count: int
    revenue: float
    gross_profit: float
    gross_margin_rate: float
    margin_data_coverage: float
    loss_making_sku_count: int


class ProfitabilitySkuResponse(BaseModel):
    sku: str
    category: str
    quantity: float
    revenue: float
    cost: float
    gross_profit: float
    gross_margin_rate: float
    discount_rate: float
    margin_band: str


class ProfitabilityArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: ProfitabilitySummaryResponse
    skus: list[ProfitabilitySkuResponse] = Field(default_factory=list)
