# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         executive_scorecard_schemas.py
# Path:         modules/business_review_reporting/executive_scorecard_schemas.py
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
#   - Main types: ScorecardPillarResponse, OperatingExecutiveScorecardSummaryResponse, OperatingExecutiveScorecardReportResponse, BenchmarkEntityResponse, InternalBenchmarkingSummaryResponse, InternalBenchmarkingReportResponse, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class ScorecardPillarResponse(BaseModel):
    pillar_name: str
    score: float
    target_score: float
    gap_to_target: float
    leading_metric_name: str
    leading_metric_value: float
    watchout: str
    recommended_action: str


class OperatingExecutiveScorecardSummaryResponse(BaseModel):
    pillar_count: int
    overall_score: float
    top_pillar: str
    weakest_pillar: str
    pillars_below_target: int
    critical_alert_count: int


class OperatingExecutiveScorecardReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: OperatingExecutiveScorecardSummaryResponse
    pillars: list[ScorecardPillarResponse] = Field(default_factory=list)


class BenchmarkEntityResponse(BaseModel):
    entity_type: str
    entity_id: str
    revenue: float
    gross_margin_rate: float
    service_level: float
    return_rate: float
    revenue_index: float
    margin_index: float
    service_index: float
    composite_score: float
    quartile: str
    improvement_focus: str


class InternalBenchmarkingSummaryResponse(BaseModel):
    store_count: int
    category_count: int
    top_store: str
    lowest_store: str
    top_category: str
    widest_gap_points: float


class InternalBenchmarkingReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: InternalBenchmarkingSummaryResponse
    store_benchmarks: list[BenchmarkEntityResponse] = Field(default_factory=list)
    category_benchmarks: list[BenchmarkEntityResponse] = Field(default_factory=list)


class MarkdownCandidateResponse(BaseModel):
    sku: str
    category: str
    aging_band: str
    combined_class: str
    seasonality_band: str
    days_of_cover: float
    gross_margin_rate: float
    stockout_probability: float
    suggested_markdown_rate: float
    expected_cash_release: float
    clearance_priority: str
    rationale: str


class MarkdownClearanceOptimizationSummaryResponse(BaseModel):
    sku_count: int
    clearance_candidate_count: int
    critical_candidate_count: int
    expected_cash_release: float
    top_clearance_category: str


class MarkdownClearanceOptimizationReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: MarkdownClearanceOptimizationSummaryResponse
    candidates: list[MarkdownCandidateResponse] = Field(default_factory=list)


class RiskZoneSummaryResponse(BaseModel):
    risk_zone: str
    sku_count: int
    forecast_share: float
    average_stockout_probability: float
    average_reorder_urgency: float
    response_play: str


class DemandSupplyFocusSkuResponse(BaseModel):
    sku: str
    category: str
    supplier_name: str
    supplier_risk_band: str
    seasonality_band: str
    forecast_30d: float
    days_of_cover: float
    stockout_probability: float
    reorder_urgency_score: float
    risk_zone: str
    recommended_action: str


class DemandSupplyRiskMatrixSummaryResponse(BaseModel):
    sku_count: int
    risk_zone_count: int
    red_zone_count: int
    inventory_heavy_count: int
    balanced_count: int
    top_risk_sku: str


class DemandSupplyRiskMatrixReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: DemandSupplyRiskMatrixSummaryResponse
    risk_zones: list[RiskZoneSummaryResponse] = Field(default_factory=list)
    focus_skus: list[DemandSupplyFocusSkuResponse] = Field(default_factory=list)


class JourneyStageResponse(BaseModel):
    stage_name: str
    incident_count: int
    customer_count: int
    revenue_at_risk: float
    average_friction_score: float
    response_play: str


class FrictionCustomerResponse(BaseModel):
    customer_id: str
    segment: str
    churn_risk_band: str
    friction_score: float
    payment_issue_count: int
    fulfillment_issue_count: int
    return_issue_count: int
    revenue_at_risk: float
    primary_friction_stage: str
    recommended_action: str


class CustomerJourneyFrictionSummaryResponse(BaseModel):
    customer_count: int
    friction_customer_count: int
    high_friction_customer_count: int
    revenue_at_risk: float
    primary_friction_stage: str


class CustomerJourneyFrictionReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: CustomerJourneyFrictionSummaryResponse
    stages: list[JourneyStageResponse] = Field(default_factory=list)
    customers: list[FrictionCustomerResponse] = Field(default_factory=list)


class CashRiskDriverResponse(BaseModel):
    driver_name: str
    exposure_amount: float
    exposure_share: float
    severity: str
    mitigation: str


class CashRiskEntityResponse(BaseModel):
    entity_type: str
    entity_id: str
    driver_name: str
    exposure_amount: float
    severity: str
    recommended_action: str


class CashConversionRiskSummaryResponse(BaseModel):
    total_cash_risk: float
    inventory_cash_lock: float
    payment_variance_exposure: float
    returns_exposure: float
    discount_leakage: float
    top_driver: str


class CashConversionRiskReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: CashConversionRiskSummaryResponse
    drivers: list[CashRiskDriverResponse] = Field(default_factory=list)
    focus_entities: list[CashRiskEntityResponse] = Field(default_factory=list)
