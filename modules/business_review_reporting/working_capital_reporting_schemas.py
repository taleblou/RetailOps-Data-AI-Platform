# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         working_capital_reporting_schemas.py
# Path:         modules/business_review_reporting/working_capital_reporting_schemas.py
#
# Summary:      Provides implementation support for the business review reporting workflow.
# Purpose:      Supports the business review reporting layer inside the modular repository architecture.
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
#   - Main types: InventoryInvestmentRowResponse, InventoryInvestmentSummaryResponse, InventoryInvestmentReportResponse, RevenueDriverContributionResponse, RevenueSegmentContributionResponse, RevenueRootCauseSummaryResponse, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class InventoryInvestmentRowResponse(BaseModel):
    sku: str
    category: str
    on_hand_units: float
    unit_cost_estimate: float
    inventory_value: float
    overstock_value: float
    dead_stock_value: float
    days_since_last_sale: float
    days_of_cover: float | None = None
    aging_band: str
    movement_class: str | None = None
    margin_band: str | None = None
    recommended_action: str


class InventoryInvestmentSummaryResponse(BaseModel):
    sku_count: int
    total_inventory_value: float
    overstock_value: float
    dead_stock_value: float
    stale_stock_value: float
    trapped_working_capital: float
    liquidation_candidate_count: int
    working_capital_pressure_band: str
    average_days_of_cover: float


class InventoryInvestmentReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: InventoryInvestmentSummaryResponse
    rows: list[InventoryInvestmentRowResponse] = Field(default_factory=list)


class RevenueDriverContributionResponse(BaseModel):
    factor: str
    impact_value: float
    direction: str
    share_of_delta: float
    explanation: str


class RevenueSegmentContributionResponse(BaseModel):
    segment_type: str
    segment_name: str
    previous_revenue: float
    current_revenue: float
    delta_revenue: float
    explanation: str


class RevenueRootCauseSummaryResponse(BaseModel):
    window_days: int
    previous_period_revenue: float
    current_period_revenue: float
    revenue_delta: float
    revenue_delta_rate: float
    previous_period_start: str
    previous_period_end: str
    current_period_start: str
    current_period_end: str


class RevenueRootCauseReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: RevenueRootCauseSummaryResponse
    methodology_note: str
    contributions: list[RevenueDriverContributionResponse] = Field(default_factory=list)
    segment_highlights: list[RevenueSegmentContributionResponse] = Field(default_factory=list)


class ForecastQualityGroupMetricResponse(BaseModel):
    group_name: str
    product_count: int
    mae: float
    rmse: float
    mape: float
    bias: float


class ForecastQualityProductResponse(BaseModel):
    product_id: str
    category: str
    product_group: str
    selected_model: str
    mae: float
    rmse: float
    mape: float
    bias: float
    point_forecast_14d: float
    interval_width_14d: float
    stockout_probability_14d: float
    quality_band: str
    reliability_band: str
    recommended_action: str


class ForecastQualitySummaryResponse(BaseModel):
    product_count: int
    reliable_product_count: int
    unstable_product_count: int
    biased_product_count: int
    low_confidence_product_count: int
    dominant_model: str
    average_mae: float
    average_rmse: float
    average_mape: float
    average_bias: float
    average_interval_width_14d: float


class ForecastQualityReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: ForecastQualitySummaryResponse
    category_metrics: list[ForecastQualityGroupMetricResponse] = Field(default_factory=list)
    product_group_metrics: list[ForecastQualityGroupMetricResponse] = Field(default_factory=list)
    products: list[ForecastQualityProductResponse] = Field(default_factory=list)


class ReplenishmentReviewRowResponse(BaseModel):
    sku: str
    store_code: str
    urgency: str
    reorder_date: str
    reorder_quantity: float
    current_inventory: float
    demand_forecast_14d: float
    demand_forecast_30d: float
    stockout_probability: float
    days_to_stockout: float
    supplier_moq: float
    service_level_target: float
    expected_lost_sales_estimate: float
    estimated_reorder_value: float
    margin_band: str | None = None
    flags: list[str] = Field(default_factory=list)
    rationale: str
    recommended_action: str


class ReplenishmentReviewSummaryResponse(BaseModel):
    total_recommendations: int
    critical_action_count: int
    recommended_today_count: int
    moq_conflict_count: int
    lead_time_pressure_count: int
    excess_cover_risk_count: int
    estimated_reorder_value: float
    estimated_lost_sales_exposure: float


class ReplenishmentDecisionReviewResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: ReplenishmentReviewSummaryResponse
    rows: list[ReplenishmentReviewRowResponse] = Field(default_factory=list)
