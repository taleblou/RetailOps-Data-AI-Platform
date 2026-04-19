# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         schemas.py
# Path:         modules/business_review_reporting/schemas.py
#
# Summary:      Defines schemas for the business review reporting data contracts.
# Purpose:      Standardizes structured payloads used by the business review reporting layer.
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
#   - Main types: ReportIndexItem, BusinessReportCatalogResponse, ReportingPeriodResponse, MetricCardResponse, RiskItemResponse, ActionItemResponse, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, typing, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReportIndexItem(BaseModel):
    report_name: str
    endpoint: str


class BusinessReportCatalogResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_index: list[ReportIndexItem] = Field(default_factory=list)


class ReportingPeriodResponse(BaseModel):
    start_date: str
    end_date: str
    day_count: int


class MetricCardResponse(BaseModel):
    label: str
    value: int | float | str
    context: str


class RiskItemResponse(BaseModel):
    title: str
    impact: int | float | str
    rationale: str
    recommended_action: str


class ActionItemResponse(BaseModel):
    title: str
    owner: str
    expected_outcome: str


class WatchlistSkuResponse(BaseModel):
    sku: str
    category: str
    priority: str
    priority_score: float
    revenue: float
    gross_margin_rate: float
    days_since_last_sale: float
    return_rate: float
    delay_rate: float
    recommended_action: str


class CommercialSummaryResponse(BaseModel):
    total_orders: int
    total_customers: int
    total_units: float
    gross_profit: float
    avg_order_value: float
    repeat_customer_rate: float


class InventorySummaryResponse(BaseModel):
    sku_count: int
    slow_mover_count: int
    long_tail_revenue_share: float
    stale_sku_count: int
    critical_aging_count: int


class FulfillmentSummaryResponse(BaseModel):
    delayed_order_count: int
    open_breach_risk_count: int
    on_time_rate: float
    average_delay_days: float


class CustomerSummaryResponse(BaseModel):
    customer_count: int
    high_risk_customer_count: int
    lost_customer_count: int
    repeat_customer_count: int


class ExecutiveBusinessReviewResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    headline: str
    reporting_period: ReportingPeriodResponse
    metric_cards: list[MetricCardResponse] = Field(default_factory=list)
    commercial_summary: CommercialSummaryResponse
    inventory_summary: InventorySummaryResponse
    fulfillment_summary: FulfillmentSummaryResponse
    customer_summary: CustomerSummaryResponse
    top_risks: list[RiskItemResponse] = Field(default_factory=list)
    top_actions: list[ActionItemResponse] = Field(default_factory=list)
    watchlist_skus: list[WatchlistSkuResponse] = Field(default_factory=list)


class StorePerformanceRowResponse(BaseModel):
    store_code: str | None = None
    region: str | None = None
    order_count: int
    customer_count: int
    sku_count: int
    units: float
    revenue: float
    gross_profit: float
    gross_margin_rate: float
    avg_order_value: float
    on_time_rate: float
    delayed_order_count: int
    open_breach_order_count: int
    return_rate: float
    promo_dependency_rate: float
    performance_band: str
    recommended_action: str


class StorePerformanceSummaryResponse(BaseModel):
    grouping_dimension: str
    group_count: int
    leader_count: int
    underperformer_count: int
    average_on_time_rate: float
    average_margin_rate: float
    top_group: str


class StorePerformancePackResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: StorePerformanceSummaryResponse
    rows: list[StorePerformanceRowResponse] = Field(default_factory=list)


class CategoryReviewRowResponse(BaseModel):
    category: str
    sku_count: int
    order_count: int
    units: float
    revenue: float
    gross_profit: float
    gross_margin_rate: float
    discount_rate: float
    promo_dependency_rate: float
    return_rate: float
    delayed_order_rate: float
    hero_sku_count: int
    slow_mover_sku_count: int
    movement_signal: str
    recommended_action: str


class CategoryReviewSummaryResponse(BaseModel):
    category_count: int
    promo_led_category_count: int
    slow_tail_category_count: int
    healthy_core_category_count: int
    top_category: str


class CategoryMerchandisingReviewResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: CategoryReviewSummaryResponse
    categories: list[CategoryReviewRowResponse] = Field(default_factory=list)


class MetricBucketResponse(BaseModel):
    order_count: int | None = None
    customer_count: int | None = None
    units: float | None = None
    revenue: float | None = None
    gross_profit: float | None = None
    gross_margin_rate: float | None = None
    average_unit_price: float | None = None
    on_hand_units: float | None = None
    days_since_last_sale: float | None = None
    days_of_cover: float | None = None
    movement_class: str | None = None
    seasonality_band: str | None = None
    delay_rate: float | None = None
    open_breach_rate: float | None = None
    return_rate: float | None = None
    promo_dependency_rate: float | None = None
    store_count: int | None = None
    region_count: int | None = None


class SkuDeepDiveResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    sku: str
    category: str
    priority: str
    priority_score: float
    commercial_metrics: MetricBucketResponse
    inventory_metrics: MetricBucketResponse
    operational_metrics: MetricBucketResponse
    risk_flags: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    supporting_signals: dict[str, Any] = Field(default_factory=dict)
