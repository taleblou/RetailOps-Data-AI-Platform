# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         portfolio_reporting_schemas.py
# Path:         modules/business_review_reporting/portfolio_reporting_schemas.py
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
#   - Main types: WaterfallStageResponse, CategoryLeakageResponse, ProfitabilityMarginWaterfallSummaryResponse, ProfitabilityMarginWaterfallReportResponse, InventoryPolicyClassResponse, InventoryPolicySkuResponse, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class WaterfallStageResponse(BaseModel):
    stage_name: str
    amount: float
    delta_to_net: float
    insight: str


class CategoryLeakageResponse(BaseModel):
    category: str
    revenue: float
    gross_margin_rate: float
    expected_return_cost: float
    discount_rate: float
    leakage_value: float
    action_priority: str


class ProfitabilityMarginWaterfallSummaryResponse(BaseModel):
    sku_count: int
    revenue: float
    gross_profit: float
    gross_margin_rate: float
    margin_leakage_value: float
    return_cost_ratio: float
    loss_making_sku_count: int


class ProfitabilityMarginWaterfallReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: ProfitabilityMarginWaterfallSummaryResponse
    waterfall: list[WaterfallStageResponse] = Field(default_factory=list)
    category_leakage: list[CategoryLeakageResponse] = Field(default_factory=list)


class InventoryPolicyClassResponse(BaseModel):
    combined_class: str
    sku_count: int
    revenue_share: float
    service_level_target: float
    review_cadence: str
    safety_stock_posture: str
    recommended_action: str


class InventoryPolicySkuResponse(BaseModel):
    sku: str
    category: str
    combined_class: str
    stockout_probability: float
    days_of_cover: float
    reorder_urgency_score: float
    policy_action: str


class AbcXyzInventoryPolicySummaryResponse(BaseModel):
    sku_count: int
    class_count: int
    ax_revenue_share: float
    cz_sku_count: int
    high_attention_sku_count: int


class AbcXyzInventoryPolicyReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: AbcXyzInventoryPolicySummaryResponse
    policy_grid: list[InventoryPolicyClassResponse] = Field(default_factory=list)
    focus_skus: list[InventoryPolicySkuResponse] = Field(default_factory=list)


class CrossSellOpportunityResponse(BaseModel):
    left_sku: str
    right_sku: str
    support: float
    confidence: float
    lift: float
    bundle_margin_rate: float
    estimated_incremental_revenue: float
    campaign_type: str
    recommended_action: str


class BasketCrossSellSummaryResponse(BaseModel):
    pair_count: int
    high_confidence_pair_count: int
    average_lift: float
    estimated_incremental_monthly_revenue: float
    top_bundle: str


class BasketCrossSellOpportunityReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: BasketCrossSellSummaryResponse
    opportunities: list[CrossSellOpportunityResponse] = Field(default_factory=list)


class ChurnRiskBandResponse(BaseModel):
    risk_band: str
    customer_count: int
    revenue_at_risk: float
    average_churn_score: float
    primary_play: str


class ChurnRecoveryCustomerResponse(BaseModel):
    customer_id: str
    segment: str
    churn_risk_band: str
    churn_score: float
    total_revenue: float
    expected_ltv: float
    recommended_action: str
    revenue_at_risk: float


class CustomerChurnRecoverySummaryResponse(BaseModel):
    customer_count: int
    high_risk_customer_count: int
    lost_customer_count: int
    recovery_value_at_risk: float
    primary_recovery_segment: str


class CustomerChurnRecoveryReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: CustomerChurnRecoverySummaryResponse
    risk_bands: list[ChurnRiskBandResponse] = Field(default_factory=list)
    customers: list[ChurnRecoveryCustomerResponse] = Field(default_factory=list)


class PaymentProviderScorecardResponse(BaseModel):
    payment_provider: str
    order_count: int
    mismatch_count: int
    variance_amount: float
    refund_amount: float
    assurance_priority: str


class PaymentExceptionResponse(BaseModel):
    order_id: str
    payment_provider: str
    reconciliation_status: str
    order_amount: float
    paid_amount: float
    refund_amount: float
    variance_amount: float
    recommended_action: str


class PaymentRevenueAssuranceSummaryResponse(BaseModel):
    order_count: int
    mismatch_order_count: int
    missing_payment_orders: int
    refunded_orders: int
    gross_cash_exposure: float


class PaymentRevenueAssuranceReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: PaymentRevenueAssuranceSummaryResponse
    provider_scorecards: list[PaymentProviderScorecardResponse] = Field(default_factory=list)
    exceptions: list[PaymentExceptionResponse] = Field(default_factory=list)


class SeasonalityMonthResponse(BaseModel):
    peak_month: str
    sku_count: int
    revenue_share: float
    planning_message: str


class SeasonalSkuResponse(BaseModel):
    sku: str
    category: str
    seasonality_band: str
    peak_month: str
    peak_month_revenue_share: float
    forecast_30d: float
    readiness_action: str


class SeasonalityCalendarReadinessSummaryResponse(BaseModel):
    sku_count: int
    strong_seasonal_sku_count: int
    moderate_seasonal_sku_count: int
    most_common_peak_month: str
    readiness_action_count: int


class SeasonalityCalendarReadinessReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: SeasonalityCalendarReadinessSummaryResponse
    peak_months: list[SeasonalityMonthResponse] = Field(default_factory=list)
    focus_skus: list[SeasonalSkuResponse] = Field(default_factory=list)


class AssortmentCategoryActionResponse(BaseModel):
    category: str
    sku_count: int
    hero_revenue_share: float
    long_tail_revenue_share: float
    exit_candidate_count: int
    expand_candidate_count: int
    recommendation: str


class AssortmentSkuActionResponse(BaseModel):
    sku: str
    category: str
    movement_class: str
    combined_class: str
    gross_margin_rate: float
    days_of_cover: float
    action: str


class AssortmentRationalizationSummaryResponse(BaseModel):
    sku_count: int
    category_count: int
    hero_sku_share: float
    long_tail_revenue_share: float
    exit_candidate_count: int
    expand_candidate_count: int


class AssortmentRationalizationReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: AssortmentRationalizationSummaryResponse
    category_actions: list[AssortmentCategoryActionResponse] = Field(default_factory=list)
    sku_actions: list[AssortmentSkuActionResponse] = Field(default_factory=list)


class CustomerSegmentPriorityResponse(BaseModel):
    segment: str
    customer_count: int
    revenue_share: float
    expected_ltv_share: float
    primary_action: str


class PrioritizedCustomerResponse(BaseModel):
    customer_id: str
    segment: str
    churn_risk_band: str
    total_revenue: float
    expected_ltv: float
    recency_days: int
    next_best_action: str


class CustomerValueSegmentationSummaryResponse(BaseModel):
    customer_count: int
    repeat_customer_rate: float
    champion_customer_count: int
    at_risk_value: float
    priority_segment: str


class CustomerValueSegmentationReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: CustomerValueSegmentationSummaryResponse
    segment_mix: list[CustomerSegmentPriorityResponse] = Field(default_factory=list)
    prioritized_customers: list[PrioritizedCustomerResponse] = Field(default_factory=list)
