# Project:      RetailOps Data & AI Platform
# Module:       modules.analytics_kpi
# File:         schemas.py
# Path:         modules/analytics_kpi/schemas.py
#
# Summary:      Defines schemas for the analytics kpi data contracts.
# Purpose:      Standardizes structured payloads used by the analytics kpi layer.
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
#   - Main types: DashboardCardResponse, DashboardArtifactResponse, DailySalesPoint, RevenueByCategoryPoint, InventoryHealthItem, ShipmentItem, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DashboardCardResponse(BaseModel):
    title: str
    value: str
    description: str


class DashboardArtifactResponse(BaseModel):
    dashboard_id: str
    dashboard_title: str
    dashboard_url: str
    artifact_path: str
    cards: list[DashboardCardResponse]


class DailySalesPoint(BaseModel):
    sales_date: str
    revenue: float = 0.0
    order_count: int = 0


class RevenueByCategoryPoint(BaseModel):
    category: str
    revenue: float = 0.0
    order_count: int = 0


class InventoryHealthItem(BaseModel):
    sku: str
    on_hand: float = 0.0
    days_of_cover: float = 0.0
    low_stock: bool = False


class ShipmentItem(BaseModel):
    shipment_id: str | None = None
    promised_date: str | None = None
    delivered_date: str | None = None
    delayed: bool = False
    delay_days: float = 0.0


class KpiOverviewResponse(BaseModel):
    total_orders: int
    total_quantity: float
    total_revenue: float
    avg_order_value: float
    sales_days: int
    delayed_shipments: int
    low_stock_items: int


class ShipmentSummaryResponse(BaseModel):
    total_shipments: int
    delayed_shipments: int
    on_time_shipments: int
    on_time_rate: float
    avg_delay_days: float


class TransformSummaryPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_orders: int = 0
    total_quantity: float = 0.0
    total_revenue: float = 0.0
    avg_order_value: float | None = None
    daily_sales: list[DailySalesPoint] = Field(default_factory=list)
    revenue_by_category: list[RevenueByCategoryPoint] = Field(default_factory=list)
    inventory_health: list[InventoryHealthItem] = Field(default_factory=list)
    shipments: list[ShipmentItem] = Field(default_factory=list)


class DashboardPublishRequest(BaseModel):
    upload_id: str
    filename: str
    transform_summary: TransformSummaryPayload
    artifact_dir: str = "artifacts/analytics_kpi"


class DashboardArtifactLookup(BaseModel):
    upload_id: str
    dashboard_id: str
    artifact_dir: str = "artifacts/analytics_kpi"
