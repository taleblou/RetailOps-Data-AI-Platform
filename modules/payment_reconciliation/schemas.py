# Project:      RetailOps Data & AI Platform
# Module:       modules.payment_reconciliation
# File:         schemas.py
# Path:         modules/payment_reconciliation/schemas.py
#
# Summary:      Defines schemas for the payment reconciliation data contracts.
# Purpose:      Standardizes structured payloads used by the payment reconciliation layer.
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
#   - Main types: PaymentSummaryResponse, PaymentOrderResponse, PaymentReconciliationArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class PaymentSummaryResponse(BaseModel):
    order_count: int
    matched_orders: int
    missing_payment_orders: int
    refunded_orders: int
    total_order_amount: float
    total_paid_amount: float
    total_refund_amount: float


class PaymentOrderResponse(BaseModel):
    order_id: str
    payment_provider: str
    order_amount: float
    paid_amount: float
    refund_amount: float
    variance_amount: float
    reconciliation_status: str


class PaymentReconciliationArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: PaymentSummaryResponse
    orders: list[PaymentOrderResponse] = Field(default_factory=list)
