# Project:      RetailOps Data & AI Platform
# Module:       modules.feature_store.repo
# File:         feature_views.py
# Path:         modules/feature_store/repo/feature_views.py
#
# Summary:      Provides implementation support for the feature store repo workflow.
# Purpose:      Supports the feature store repo layer inside the modular repository architecture.
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
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, datetime, feast, feast.types
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from datetime import timedelta

from feast import Entity, FeatureView, Field
from feast.types import Float32, Int64

sku = Entity(name="sku", join_keys=["sku"])
shipment_id = Entity(name="shipment_id", join_keys=["shipment_id"])

stockout_features_view = FeatureView(
    name="stockout_features_view",
    entities=[sku],
    ttl=timedelta(days=14),
    schema=[
        Field(name="avg_daily_demand_7d", dtype=Float32),
        Field(name="days_to_stockout", dtype=Float32),
        Field(name="reorder_urgency_score", dtype=Float32),
    ],
    online=True,
)

shipment_delay_features_view = FeatureView(
    name="shipment_delay_features_view",
    entities=[shipment_id],
    ttl=timedelta(days=7),
    schema=[
        Field(name="inventory_lag_days", dtype=Int64),
        Field(name="carrier_delay_rate_30d", dtype=Float32),
        Field(name="region_delay_trend_30d", dtype=Float32),
    ],
    online=True,
)
