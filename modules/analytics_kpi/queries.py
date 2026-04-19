# Project:      RetailOps Data & AI Platform
# Module:       modules.analytics_kpi
# File:         queries.py
# Path:         modules/analytics_kpi/queries.py
#
# Summary:      Provides implementation support for the analytics kpi workflow.
# Purpose:      Supports the analytics kpi layer inside the modular repository architecture.
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
#   - Main types: None.
#   - Key APIs: get_first_scalar, get_first_sequence
#   - Dependencies: __future__, collections.abc, typing
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

DAILY_SALES_KEYS: tuple[str, ...] = (
    "daily_sales",
    "sales_daily",
    "daily_revenue",
)
CATEGORY_REVENUE_KEYS: tuple[str, ...] = (
    "revenue_by_category",
    "category_sales",
    "category_revenue",
)
INVENTORY_HEALTH_KEYS: tuple[str, ...] = (
    "inventory_health",
    "inventory",
    "inventory_items",
)
SHIPMENT_KEYS: tuple[str, ...] = (
    "shipments",
    "shipment_rows",
    "shipment_items",
)

TOTAL_ORDER_KEYS: tuple[str, ...] = (
    "total_orders",
    "orders_total",
)
TOTAL_QUANTITY_KEYS: tuple[str, ...] = (
    "total_quantity",
    "quantity_total",
    "units_total",
)
TOTAL_REVENUE_KEYS: tuple[str, ...] = (
    "total_revenue",
    "revenue_total",
    "gross_revenue",
)
AVG_ORDER_VALUE_KEYS: tuple[str, ...] = (
    "avg_order_value",
    "average_order_value",
)

LOW_STOCK_DAYS_THRESHOLD = 7.0


def get_first_scalar(
    payload: Mapping[str, Any],
    keys: Sequence[str],
    *,
    default: object | None = None,
) -> object | None:
    for key in keys:
        if key in payload:
            return payload.get(key)
    return default


def get_first_sequence(
    payload: Mapping[str, Any],
    keys: Sequence[str],
) -> list[Mapping[str, Any]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
    return []
