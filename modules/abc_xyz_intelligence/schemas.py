# Project:      RetailOps Data & AI Platform
# Module:       modules.abc_xyz_intelligence
# File:         schemas.py
# Path:         modules/abc_xyz_intelligence/schemas.py
#
# Summary:      Defines schemas for the abc xyz intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the abc xyz intelligence layer.
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
#   - Main types: AbcXyzSummaryResponse, AbcXyzSkuResponse, AbcXyzArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class AbcXyzSummaryResponse(BaseModel):
    sku_count: int
    a_class_sku_count: int
    z_class_sku_count: int
    a_class_revenue_share: float
    high_variability_sku_count: int


class AbcXyzSkuResponse(BaseModel):
    sku: str
    category: str
    order_count: int
    quantity: float
    revenue: float
    revenue_share: float
    abc_class: str
    xyz_class: str
    combined_class: str
    demand_coefficient_variation: float


class AbcXyzArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: AbcXyzSummaryResponse
    skus: list[AbcXyzSkuResponse] = Field(default_factory=list)
