# Project:      RetailOps Data & AI Platform
# Module:       modules.analytics_kpi
# File:         __init__.py
# Path:         modules/analytics_kpi/__init__.py
#
# Summary:      Defines the modules.analytics_kpi package surface and package-level exports.
# Purpose:      Marks modules.analytics_kpi as a Python package and centralizes its package-level imports.
# Scope:        internal
# Status:       internal
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
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, router, service
#   - Constraints: Package exports should stay lightweight and avoid introducing import cycles.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from .router import router
from .service import (
    build_dashboard_cards,
    build_inventory_health,
    build_overview,
    build_revenue_by_category,
    build_sales_daily,
    build_shipment_summary,
    load_dashboard_artifact,
    load_transform_summary_from_upload,
    publish_first_dashboard,
)

__all__ = [
    "router",
    "build_dashboard_cards",
    "build_inventory_health",
    "build_overview",
    "build_revenue_by_category",
    "build_sales_daily",
    "build_shipment_summary",
    "load_dashboard_artifact",
    "load_transform_summary_from_upload",
    "publish_first_dashboard",
]
