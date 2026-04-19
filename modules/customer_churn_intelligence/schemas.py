# Project:      RetailOps Data & AI Platform
# Module:       modules.customer_churn_intelligence
# File:         schemas.py
# Path:         modules/customer_churn_intelligence/schemas.py
#
# Summary:      Defines schemas for the customer churn intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the customer churn intelligence layer.
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
#   - Main types: CustomerChurnSummaryResponse, CustomerChurnDetailResponse, CustomerChurnArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerChurnSummaryResponse(BaseModel):
    customer_count: int
    high_risk_customer_count: int
    lost_customer_count: int
    average_recency_days: float
    average_churn_score: float


class CustomerChurnDetailResponse(BaseModel):
    customer_id: str
    order_count: int
    total_revenue: float
    first_order_date: str
    last_order_date: str
    recency_days: int
    average_gap_days: float
    churn_score: float
    churn_risk_band: str
    recommended_action: str


class CustomerChurnArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: CustomerChurnSummaryResponse
    customers: list[CustomerChurnDetailResponse] = Field(default_factory=list)
