# Project:      RetailOps Data & AI Platform
# Module:       modules.reorder_engine
# File:         schemas.py
# Path:         modules/reorder_engine/schemas.py
#
# Summary:      Defines schemas for the reorder engine data contracts.
# Purpose:      Standardizes structured payloads used by the reorder engine layer.
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
#   - Main types: ReorderRecommendationResponse, ReorderSummaryResponse, ReorderRecommendationListResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class ReorderRecommendationResponse(BaseModel):
    sku: str
    store_code: str
    as_of_date: str
    reorder_date: str
    reorder_quantity: float
    urgency: str
    urgency_score: float
    rationale: str
    current_inventory: float
    inbound_qty: float
    lead_time_days: float
    supplier_moq: float
    service_level_target: float
    demand_forecast_7d: float
    demand_forecast_14d: float
    demand_forecast_30d: float
    avg_daily_demand_7d: float
    stockout_probability: float
    days_to_stockout: float
    expected_lost_sales_estimate: float
    stockout_risk_band: str
    recommended_action: str
    feature_timestamp: str
    model_version: str


class ReorderSummaryResponse(BaseModel):
    total_skus: int
    urgent_skus: int
    recommended_today: int
    total_reorder_quantity: float
    average_reorder_quantity: float
    average_stockout_probability: float
    output_table: str


class ReorderRecommendationListResponse(BaseModel):
    reorder_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: ReorderSummaryResponse
    recommendations: list[ReorderRecommendationResponse] = Field(default_factory=list)
    artifact_path: str
