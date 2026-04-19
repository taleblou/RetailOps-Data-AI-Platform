# Project:      RetailOps Data & AI Platform
# Module:       modules.shipment_risk
# File:         schemas.py
# Path:         modules/shipment_risk/schemas.py
#
# Summary:      Defines schemas for the shipment risk data contracts.
# Purpose:      Standardizes structured payloads used by the shipment risk layer.
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
#   - Main types: ShipmentRiskMetricsResponse, ShipmentRiskPredictionResponse, ShipmentRiskSummaryResponse, ShipmentRiskOpenOrdersResponse, ShipmentDelayPredictRequest, ManualReviewDecisionResponse, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class ShipmentRiskMetricsResponse(BaseModel):
    roc_auc: float
    pr_auc: float
    calibration_gap: float
    precision_at_threshold: float
    recall_at_threshold: float


class ShipmentRiskPredictionResponse(BaseModel):
    shipment_id: str
    order_id: str
    store_code: str
    carrier: str
    shipment_status: str
    promised_date: str
    actual_delivery_date: str
    probability: float
    risk_band: str
    top_factors: list[str] = Field(default_factory=list)
    recommended_action: str
    manual_review_required: bool
    manual_review_reason: str
    feature_timestamp: str
    model_version: str
    overdue_days: float
    explanation_summary: str


class ShipmentRiskSummaryResponse(BaseModel):
    open_orders: int
    high_risk_orders: int
    manual_review_orders: int
    risk_band_counts: dict[str, int] = Field(default_factory=dict)
    carriers: list[str] = Field(default_factory=list)
    breach_definition: str


class ShipmentRiskOpenOrdersResponse(BaseModel):
    shipment_risk_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: ShipmentRiskSummaryResponse
    evaluation_metrics: ShipmentRiskMetricsResponse
    open_orders: list[ShipmentRiskPredictionResponse] = Field(default_factory=list)
    artifact_path: str


class ShipmentDelayPredictRequest(BaseModel):
    shipment_id: str | None = None
    order_id: str | None = None
    store_code: str | None = None
    carrier: str | None = None
    shipment_status: str = "processing"
    promised_date: str
    actual_delivery_date: str | None = None
    order_date: str | None = None
    inventory_lag_days: float = 0.0
    warehouse_backlog_7d: float = 0.0
    carrier_delay_rate_30d: float = 0.0
    region_delay_trend_30d: float = 0.0
    reference_date: str | None = None


class ManualReviewDecisionResponse(BaseModel):
    shipment_id: str
    probability: float
    risk_band: str
    manual_review_required: bool
    reason: str
    suggested_owner: str
