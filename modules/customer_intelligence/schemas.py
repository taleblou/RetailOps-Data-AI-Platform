# Project:      RetailOps Data & AI Platform
# Module:       modules.customer_intelligence
# File:         schemas.py
# Path:         modules/customer_intelligence/schemas.py
#
# Summary:      Defines schemas for the customer intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the customer intelligence layer.
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
#   - Main types: CustomerSummaryResponse, CustomerSegmentResponse, CustomerIntelligenceArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerSummaryResponse(BaseModel):
    customer_count: int
    repeat_customer_count: int
    repeat_customer_rate: float
    average_order_value: float
    average_orders_per_customer: float


class CustomerSegmentResponse(BaseModel):
    customer_id: str
    order_count: int
    total_revenue: float
    average_order_value: float
    total_quantity: float
    recency_days: int
    segment: str
    expected_ltv: float


class CustomerIntelligenceArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: CustomerSummaryResponse
    customers: list[CustomerSegmentResponse] = Field(default_factory=list)
