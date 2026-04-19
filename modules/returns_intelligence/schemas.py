# Project:      RetailOps Data & AI Platform
# Module:       modules.returns_intelligence
# File:         schemas.py
# Path:         modules/returns_intelligence/schemas.py
#
# Summary:      Defines schemas for the returns intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the returns intelligence layer.
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
#   - Main types: ReturnRiskPredictionResponse, ReturnRiskProductResponse, ReturnRiskSummaryResponse, ReturnRiskArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class ReturnRiskPredictionResponse(BaseModel):
    order_id: str
    customer_id: str
    sku: str
    store_code: str
    order_date: str
    category: str
    quantity: float
    unit_price: float
    gross_revenue: float
    discount_rate: float
    discount_level: str
    shipment_delay_days: float
    customer_return_rate_180d: float
    sku_return_rate_180d: float
    return_probability: float
    expected_return_cost: float
    return_cost_band: str
    risk_band: str
    top_factors: list[str] = Field(default_factory=list)
    recommended_action: str
    label_return_within_days: int
    feature_timestamp: str
    model_version: str
    explanation_summary: str


class ReturnRiskProductResponse(BaseModel):
    sku: str
    store_code: str
    category: str
    orders_scored: int
    average_return_probability: float
    total_expected_return_cost: float
    risk_band: str
    return_cost_band: str


class ReturnRiskSummaryResponse(BaseModel):
    total_orders: int
    high_risk_orders: int
    risky_products_count: int
    average_return_probability: float
    total_expected_return_cost: float
    output_features_table: str
    output_predictions_table: str


class ReturnRiskArtifactResponse(BaseModel):
    return_risk_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: ReturnRiskSummaryResponse
    scores: list[ReturnRiskPredictionResponse] = Field(default_factory=list)
    risky_products: list[ReturnRiskProductResponse] = Field(default_factory=list)
    artifact_path: str
