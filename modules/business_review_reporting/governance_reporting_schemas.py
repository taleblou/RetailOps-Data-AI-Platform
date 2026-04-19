# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         governance_reporting_schemas.py
# Path:         modules/business_review_reporting/governance_reporting_schemas.py
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
#   - Main types: AnomalyInvestigationFindingResponse, AnomalyInvestigationSummaryResponse, AnomalyInvestigationReportResponse, FulfillmentControlTowerOrderResponse, FulfillmentCarrierScoreResponse, FulfillmentControlTowerSummaryResponse, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class AnomalyInvestigationFindingResponse(BaseModel):
    order_date: str
    anomaly_type: str
    severity: str
    affected_order_count: int
    revenue: float
    baseline_revenue: float
    estimated_revenue_gap: float
    delta_ratio: float
    dominant_category: str
    promo_order_share: float
    delayed_order_rate: float
    return_rate: float
    top_store: str
    likely_driver: str
    investigation_focus: str
    recommended_action: str


class AnomalyInvestigationSummaryResponse(BaseModel):
    day_count: int
    anomaly_count: int
    critical_anomaly_count: int
    spike_count: int
    drop_count: int
    largest_positive_delta_ratio: float
    largest_negative_delta_ratio: float
    highest_priority_date: str


class AnomalyInvestigationReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: AnomalyInvestigationSummaryResponse
    findings: list[AnomalyInvestigationFindingResponse] = Field(default_factory=list)


class FulfillmentControlTowerOrderResponse(BaseModel):
    order_id: str
    customer_id: str
    store_code: str
    region: str
    carrier: str
    shipment_status: str
    promised_date: str
    actual_delivery_date: str
    delay_days: float
    revenue_at_risk: float
    priority_band: str
    sla_band: str
    root_signal: str
    recommended_action: str


class FulfillmentCarrierScoreResponse(BaseModel):
    carrier: str
    order_count: int
    delayed_order_count: int
    open_breach_count: int
    on_time_rate: float
    average_delay_days: float
    escalation_rate: float
    recommended_action: str


class FulfillmentControlTowerSummaryResponse(BaseModel):
    open_order_count: int
    delayed_order_count: int
    breach_risk_order_count: int
    on_time_order_count: int
    average_delay_days: float
    revenue_at_risk: float
    critical_order_count: int
    worst_carrier: str


class FulfillmentControlTowerReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: FulfillmentControlTowerSummaryResponse
    carrier_scores: list[FulfillmentCarrierScoreResponse] = Field(default_factory=list)
    open_orders: list[FulfillmentControlTowerOrderResponse] = Field(default_factory=list)


class AiGovernanceRegistryResponse(BaseModel):
    registry_name: str
    champion_version: str
    challenger_version: str
    shadow_version: str
    primary_metric: str
    optimization_direction: str
    champion_metric_value: float
    baseline_metric_value: float
    calibration_error: float
    drift_score: float
    promotion_eligible: bool
    active_alert_count: int
    trust_band: str
    recommended_action: str


class AiGovernanceAlertResponse(BaseModel):
    category: str
    check_name: str
    severity: str
    metric_name: str
    metric_value: float
    threshold_value: float
    message: str
    recommended_action: str


class AiGovernanceMetricResponse(BaseModel):
    metric_name: str
    value: float
    unit: str
    status: str
    description: str


class AiGovernanceSummaryResponse(BaseModel):
    registry_count: int
    champion_registry_count: int
    promotion_ready_registry_count: int
    total_alerts: int
    critical_alerts: int
    override_count: int
    retrain_recommended: bool
    disable_prediction_recommended: bool
    average_calibration_error: float
    average_drift_score: float
    governance_band: str


class AiGovernanceTrustReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: AiGovernanceSummaryResponse
    registries: list[AiGovernanceRegistryResponse] = Field(default_factory=list)
    alert_highlights: list[AiGovernanceAlertResponse] = Field(default_factory=list)
    dashboard_metrics: list[AiGovernanceMetricResponse] = Field(default_factory=list)


class DataQualityCheckResponse(BaseModel):
    check_name: str
    status: str
    metric_name: str
    metric_value: float
    threshold_value: float
    message: str
    recommended_action: str
    evidence: str


class PipelineStageStatusResponse(BaseModel):
    stage_name: str
    status: str
    detail: str
    recommended_action: str


class DataQualityAlertResponse(BaseModel):
    category: str
    severity: str
    check_name: str
    message: str
    recommended_action: str


class DataQualityPipelineSummaryResponse(BaseModel):
    source_file_count: int
    source_row_count: int
    warning_check_count: int
    critical_check_count: int
    freshness_days: float
    latest_event_date: str
    pipeline_reliability_band: str
    schema_coverage_note: str


class DataQualityPipelineReliabilityReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: DataQualityPipelineSummaryResponse
    data_checks: list[DataQualityCheckResponse] = Field(default_factory=list)
    pipeline_stages: list[PipelineStageStatusResponse] = Field(default_factory=list)
    alert_highlights: list[DataQualityAlertResponse] = Field(default_factory=list)
