# Project:      RetailOps Data & AI Platform
# Module:       modules.inventory_aging_intelligence
# File:         schemas.py
# Path:         modules/inventory_aging_intelligence/schemas.py
#
# Summary:      Defines schemas for the inventory aging intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the inventory aging intelligence layer.
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
#   - Main types: InventoryAgingSummaryResponse, InventoryAgingSkuResponse, InventoryAgingArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class InventoryAgingSummaryResponse(BaseModel):
    sku_count: int
    stale_sku_count: int
    critical_aging_count: int
    inventory_coverage_rate: float
    average_days_since_last_sale: float


class InventoryAgingSkuResponse(BaseModel):
    sku: str
    category: str
    order_count: int
    quantity_sold: float
    revenue: float
    on_hand_units: float
    days_since_last_sale: int
    average_daily_units: float
    days_of_cover: float | None = None
    aging_band: str


class InventoryAgingArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: InventoryAgingSummaryResponse
    skus: list[InventoryAgingSkuResponse] = Field(default_factory=list)
