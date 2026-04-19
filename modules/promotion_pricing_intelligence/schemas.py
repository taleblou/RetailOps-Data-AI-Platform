# Project:      RetailOps Data & AI Platform
# Module:       modules.promotion_pricing_intelligence
# File:         schemas.py
# Path:         modules/promotion_pricing_intelligence/schemas.py
#
# Summary:      Defines schemas for the promotion pricing intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the promotion pricing intelligence layer.
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
#   - Main types: PromotionSummaryResponse, PromotionSkuResponse, PromotionPricingArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class PromotionSummaryResponse(BaseModel):
    total_rows: int
    promoted_rows: int
    promo_revenue_share: float
    average_discount_rate: float
    gross_revenue: float
    net_revenue: float
    discount_value: float
    top_promo_code: str


class PromotionSkuResponse(BaseModel):
    sku: str
    category: str
    promo_code: str
    rows: int
    quantity: float
    gross_revenue: float
    net_revenue: float
    discount_value: float
    discount_rate: float
    price_realization: float


class PromotionPricingArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: PromotionSummaryResponse
    skus: list[PromotionSkuResponse] = Field(default_factory=list)
