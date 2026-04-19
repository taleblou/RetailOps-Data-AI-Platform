# Project:      RetailOps Data & AI Platform
# Module:       modules.supplier_procurement_intelligence
# File:         schemas.py
# Path:         modules/supplier_procurement_intelligence/schemas.py
#
# Summary:      Defines schemas for the supplier procurement intelligence data contracts.
# Purpose:      Standardizes structured payloads used by the supplier procurement intelligence layer.
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
#   - Main types: SupplierSummaryResponse, SupplierProcurementResponse, SupplierProcurementArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class SupplierSummaryResponse(BaseModel):
    supplier_count: int
    total_ordered_qty: float
    total_received_qty: float
    average_fill_rate: float
    average_lead_time_days: float
    high_risk_suppliers: int


class SupplierProcurementResponse(BaseModel):
    supplier_id: str
    supplier_name: str
    rows: int
    total_ordered_qty: float
    total_received_qty: float
    fill_rate: float
    average_lead_time_days: float
    lead_time_variability_days: float
    average_moq: float
    procurement_risk_band: str
    recommended_action: str


class SupplierProcurementArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: SupplierSummaryResponse
    suppliers: list[SupplierProcurementResponse] = Field(default_factory=list)
