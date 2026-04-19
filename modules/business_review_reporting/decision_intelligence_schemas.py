# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         decision_intelligence_schemas.py
# Path:         modules/business_review_reporting/decision_intelligence_schemas.py
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
#   - Main types: ScenarioSimulationRowResponse, ScenarioFocusSkuResponse, ScenarioSimulationSummaryResponse, ScenarioSimulationReportResponse, PlaybookLaneResponse, AlertActionResponse, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class ScenarioSimulationRowResponse(BaseModel):
    scenario_name: str
    assumption_summary: str
    projected_revenue: float
    revenue_delta: float
    projected_gross_margin_rate: float
    margin_rate_delta: float
    projected_stockout_probability: float
    stockout_probability_delta: float
    projected_on_time_rate: float
    on_time_rate_delta: float
    incremental_reorder_quantity: float
    working_capital_delta: float
    scenario_score: float
    dominant_tradeoff: str
    recommended_action: str


class ScenarioFocusSkuResponse(BaseModel):
    scenario_name: str
    sku: str
    category: str
    current_stockout_probability: float
    projected_stockout_probability: float
    current_reorder_quantity: float
    projected_reorder_quantity: float
    impact_reason: str


class ScenarioSimulationSummaryResponse(BaseModel):
    scenario_count: int
    recommended_scenario: str
    worst_case_scenario: str
    base_projected_revenue: float
    base_gross_margin_rate: float
    base_stockout_probability: float
    base_on_time_rate: float


class ScenarioSimulationReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: ScenarioSimulationSummaryResponse
    scenarios: list[ScenarioSimulationRowResponse] = Field(default_factory=list)
    focus_skus: list[ScenarioFocusSkuResponse] = Field(default_factory=list)


class PlaybookLaneResponse(BaseModel):
    lane_name: str
    owner: str
    action_count: int
    critical_action_count: int
    total_expected_value: float
    objective: str


class AlertActionResponse(BaseModel):
    playbook_name: str
    action_title: str
    owner: str
    urgency: str
    entity_type: str
    entity_id: str
    reason: str
    expected_value: float
    deadline_days: int
    recommended_action: str


class AlertToActionPlaybookSummaryResponse(BaseModel):
    total_actions: int
    critical_action_count: int
    high_action_count: int
    action_backlog_value: float
    primary_owner: str
    top_playbook: str


class AlertToActionPlaybookReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: AlertToActionPlaybookSummaryResponse
    playbook_lanes: list[PlaybookLaneResponse] = Field(default_factory=list)
    actions: list[AlertActionResponse] = Field(default_factory=list)


class DecisionStrategySummaryResponse(BaseModel):
    strategy: str
    sku_count: int
    revenue_share: float
    estimated_value_at_stake: float
    strategy_goal: str


class CrossModuleDecisionRowResponse(BaseModel):
    sku: str
    category: str
    strategy: str
    confidence_band: str
    revenue_reference: float
    gross_margin_rate: float
    stockout_probability: float
    reorder_urgency_score: float
    average_return_probability: float
    days_of_cover: float
    supplier_risk_band: str
    estimated_value_at_stake: float
    rationale: str
    recommended_action: str


class CrossModuleDecisionSummaryResponse(BaseModel):
    sku_count: int
    strategy_count: int
    top_strategy: str
    total_estimated_value_at_stake: float
    invest_count: int
    protect_count: int
    fix_count: int
    harvest_count: int


class CrossModuleDecisionIntelligenceReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: CrossModuleDecisionSummaryResponse
    strategy_mix: list[DecisionStrategySummaryResponse] = Field(default_factory=list)
    decisions: list[CrossModuleDecisionRowResponse] = Field(default_factory=list)


class PortfolioQuadrantResponse(BaseModel):
    quadrant_name: str
    sku_count: int
    revenue_share: float
    average_margin_rate: float
    average_stockout_probability: float
    primary_goal: str
    recommended_action: str


class PortfolioOpportunityItemResponse(BaseModel):
    sku: str
    category: str
    quadrant: str
    revenue_reference: float
    gross_margin_rate: float
    stockout_probability: float
    average_return_probability: float
    days_of_cover: float
    opportunity_note: str


class PortfolioOpportunityMatrixSummaryResponse(BaseModel):
    quadrant_count: int
    dominant_quadrant: str
    high_priority_sku_count: int
    growth_revenue_share: float
    cash_recovery_revenue_share: float


class PortfolioOpportunityMatrixReportResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    summary: PortfolioOpportunityMatrixSummaryResponse
    quadrants: list[PortfolioQuadrantResponse] = Field(default_factory=list)
    focus_items: list[PortfolioOpportunityItemResponse] = Field(default_factory=list)


class BoardPackMetricResponse(BaseModel):
    label: str
    value: str
    context: str


class BoardPackSectionResponse(BaseModel):
    section_name: str
    headline: str
    primary_message: str


class BoardPackSummaryResponse(BaseModel):
    pdf_generated: bool
    pdf_page_count: int
    section_count: int
    primary_board_call: str
    board_readiness: str


class BoardStylePdfPackResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    report_name: str
    pdf_artifact_path: str
    summary: BoardPackSummaryResponse
    headline_metrics: list[BoardPackMetricResponse] = Field(default_factory=list)
    sections: list[BoardPackSectionResponse] = Field(default_factory=list)
    board_calls: list[str] = Field(default_factory=list)
