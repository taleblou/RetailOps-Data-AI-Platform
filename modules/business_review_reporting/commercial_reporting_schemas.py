# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         commercial_reporting_schemas.py
# Path:         modules/business_review_reporting/commercial_reporting_schemas.py
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
#   - Main types: SupplierProcurementPackRowResponse, SupplierProcurementPackSummaryResponse, SupplierProcurementPackResponse, ReturnsLeakageWaterfallResponse, ReturnsProfitLeakageCategoryResponse, ReturnsProfitLeakageSummaryResponse, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class SupplierProcurementPackRowResponse(BaseModel):
    supplier_id: str
    supplier_name: str
    order_line_count: int
    fill_rate: float
    on_time_delivery_rate: float
    sla_breach_rate: float
    average_lead_time_days: float
    lead_time_variability_days: float
    average_moq: float
    spend_estimate: float
    delayed_receipt_qty: float
    procurement_risk_band: str
    recommended_action: str


class SupplierProcurementPackSummaryResponse(BaseModel):
    supplier_count: int
    high_risk_supplier_count: int
    total_spend_estimate: float
    average_fill_rate: float
    average_on_time_delivery_rate: float
    average_lead_time_days: float
    spend_at_risk: float
    dominant_risk_band: str


class SupplierProcurementPackResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: SupplierProcurementPackSummaryResponse
    rows: list[SupplierProcurementPackRowResponse] = Field(default_factory=list)


class ReturnsLeakageWaterfallResponse(BaseModel):
    component: str
    amount: float
    rationale: str


class ReturnsProfitLeakageCategoryResponse(BaseModel):
    category: str
    order_count: int
    returned_order_count: int
    return_rate: float
    expected_return_cost: float
    actual_return_cost: float
    delayed_return_cost: float
    discount_linked_return_cost: float
    net_revenue: float
    leakage_rate: float
    leakage_band: str
    recommended_action: str


class ReturnsProfitLeakageSummaryResponse(BaseModel):
    total_orders: int
    returned_order_count: int
    total_expected_return_cost: float
    total_actual_return_cost: float
    delay_linked_return_cost: float
    discount_linked_return_cost: float
    high_loss_category_count: int
    leakage_pressure_band: str


class ReturnsProfitLeakageReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: ReturnsProfitLeakageSummaryResponse
    waterfall: list[ReturnsLeakageWaterfallResponse] = Field(default_factory=list)
    categories: list[ReturnsProfitLeakageCategoryResponse] = Field(default_factory=list)


class PromotionEffectivenessRowResponse(BaseModel):
    promo_code: str
    category: str
    promoted_order_count: int
    sku_count: int
    gross_revenue: float
    net_revenue: float
    discount_value: float
    discount_rate: float
    price_realization: float
    promo_margin_rate: float
    non_promo_margin_rate: float
    margin_gap: float
    uplift_proxy: float
    effectiveness_band: str
    recommended_action: str


class PromotionPricingCategoryResponse(BaseModel):
    category: str
    promo_order_share: float
    promo_revenue_share: float
    promo_discount_rate: float
    promo_margin_gap: float
    promo_dependency_band: str
    recommended_action: str


class PromotionPricingEffectivenessSummaryResponse(BaseModel):
    promoted_order_count: int
    promo_code_count: int
    promo_revenue: float
    discount_value: float
    average_discount_rate: float
    average_uplift_proxy: float
    strong_promo_count: int
    weak_promo_count: int


class PromotionPricingEffectivenessReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: PromotionPricingEffectivenessSummaryResponse
    promotions: list[PromotionEffectivenessRowResponse] = Field(default_factory=list)
    categories: list[PromotionPricingCategoryResponse] = Field(default_factory=list)


class CohortRetentionRowResponse(BaseModel):
    cohort_month: str
    customer_count: int
    repeat_customer_count: int
    repeat_customer_rate: float
    retained_60d_count: int
    retained_60d_rate: float
    at_risk_customer_count: int
    lost_customer_count: int
    revenue: float
    average_revenue_per_customer: float
    cohort_health_band: str
    recommended_action: str


class CustomerRetentionFocusResponse(BaseModel):
    customer_id: str
    cohort_month: str
    segment: str
    churn_risk_band: str
    recency_days: int
    total_revenue: float
    recommended_action: str


class CustomerCohortRetentionSummaryResponse(BaseModel):
    cohort_count: int
    customer_count: int
    repeat_customer_rate: float
    retained_60d_rate: float
    high_risk_customer_count: int
    lost_customer_count: int
    retention_pressure_band: str
    strongest_cohort_month: str
    weakest_cohort_month: str


class CustomerCohortRetentionReviewResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: CustomerCohortRetentionSummaryResponse
    cohorts: list[CohortRetentionRowResponse] = Field(default_factory=list)
    focus_customers: list[CustomerRetentionFocusResponse] = Field(default_factory=list)
