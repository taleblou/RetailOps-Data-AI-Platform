# Project:      RetailOps Data & AI Platform
# Module:       modules.customer_cohort_intelligence
# File:         schemas.py
# Path:         modules/customer_cohort_intelligence/schemas.py
#
# Summary:      Defines schemas for the customer cohort intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the customer cohort intelligence layer.
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
#   - Main types: CustomerCohortSummaryResponse, CustomerCohortDetailResponse, CustomerCohortArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerCohortSummaryResponse(BaseModel):
    cohort_count: int
    customer_count: int
    repeat_customer_count: int
    repeat_customer_rate: float
    largest_cohort_month: str
    largest_cohort_size: int


class CustomerCohortDetailResponse(BaseModel):
    cohort_month: str
    customer_count: int
    repeat_customer_count: int
    repeat_customer_rate: float
    order_count: int
    revenue: float
    average_orders_per_customer: float
    average_revenue_per_customer: float


class CustomerCohortArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: CustomerCohortSummaryResponse
    cohorts: list[CustomerCohortDetailResponse] = Field(default_factory=list)
