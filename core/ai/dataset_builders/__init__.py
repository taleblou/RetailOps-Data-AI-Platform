# Project:      RetailOps Data & AI Platform
# Module:       core.ai.dataset_builders
# File:         __init__.py
# Path:         core/ai/dataset_builders/__init__.py
#
# Summary:      Defines the core.ai.dataset_builders package surface and package-level exports.
# Purpose:      Marks core.ai.dataset_builders as a Python package and centralizes its package-level imports.
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
#   - Dependencies: builder, contracts, freshness, models
#   - Constraints: Package exports should stay lightweight and avoid introducing import cycles.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

"""Utilities for loading feature contracts, building PIT datasets, and checking freshness."""

from .builder import DatasetWindow, build_backtest_windows, build_point_in_time_dataset_sql
from .contracts import DEFAULT_CONTRACTS_DIR, load_feature_contract, load_feature_contracts
from .freshness import FreshnessResult, evaluate_feature_freshness, evaluate_feature_freshness_map
from .models import FeatureContract

__all__ = [
    "DEFAULT_CONTRACTS_DIR",
    "DatasetWindow",
    "FeatureContract",
    "FreshnessResult",
    "build_backtest_windows",
    "build_point_in_time_dataset_sql",
    "evaluate_feature_freshness",
    "evaluate_feature_freshness_map",
    "load_feature_contract",
    "load_feature_contracts",
]
