# Project:      RetailOps Data & AI Platform
# Module:       modules.fulfillment_sla_intelligence
# File:         schemas.py
# Path:         modules/fulfillment_sla_intelligence/schemas.py
#
# Summary:      Defines schemas for the fulfillment sla intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the fulfillment sla intelligence layer.
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
#   - Main types: FulfillmentSlaSummaryResponse, FulfillmentSlaOrderResponse, FulfillmentSlaArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class FulfillmentSlaSummaryResponse(BaseModel):
    order_count: int
    delivered_order_count: int
    delayed_order_count: int
    open_breach_risk_count: int
    on_time_rate: float
    average_delay_days: float


class FulfillmentSlaOrderResponse(BaseModel):
    order_id: str
    carrier: str
    region: str
    shipment_status: str
    promised_date: str
    actual_delivery_date: str
    delay_days: float
    sla_band: str
    recommended_action: str


class FulfillmentSlaArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: FulfillmentSlaSummaryResponse
    orders: list[FulfillmentSlaOrderResponse] = Field(default_factory=list)
