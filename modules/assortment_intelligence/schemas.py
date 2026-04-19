# Project:      RetailOps Data & AI Platform
# Module:       modules.assortment_intelligence
# File:         schemas.py
# Path:         modules/assortment_intelligence/schemas.py
#
# Summary:      Defines schemas for the assortment intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the assortment intelligence layer.
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
#   - Main types: AssortmentSummaryResponse, AssortmentSkuResponse, AssortmentArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class AssortmentSummaryResponse(BaseModel):
    sku_count: int
    category_count: int
    order_count: int
    long_tail_revenue_share: float
    hero_sku_share: float
    slow_mover_count: int


class AssortmentSkuResponse(BaseModel):
    sku: str
    category: str
    order_count: int
    quantity: float
    revenue: float
    average_unit_price: float
    revenue_share: float
    movement_class: str


class AssortmentArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: AssortmentSummaryResponse
    skus: list[AssortmentSkuResponse] = Field(default_factory=list)
