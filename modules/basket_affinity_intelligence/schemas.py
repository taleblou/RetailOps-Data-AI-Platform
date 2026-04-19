# Project:      RetailOps Data & AI Platform
# Module:       modules.basket_affinity_intelligence
# File:         schemas.py
# Path:         modules/basket_affinity_intelligence/schemas.py
#
# Summary:      Defines schemas for the basket affinity intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the basket affinity intelligence layer.
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
#   - Main types: BasketAffinitySummaryResponse, BasketPairResponse, BasketAffinityArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class BasketAffinitySummaryResponse(BaseModel):
    order_count: int
    multi_item_order_count: int
    pair_count: int
    strongest_pair_support: float
    strongest_pair_confidence: float


class BasketPairResponse(BaseModel):
    left_sku: str
    right_sku: str
    pair_order_count: int
    support: float
    confidence: float
    lift: float


class BasketAffinityArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: BasketAffinitySummaryResponse
    pairs: list[BasketPairResponse] = Field(default_factory=list)
