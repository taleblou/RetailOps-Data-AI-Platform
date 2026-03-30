# Project:      RetailOps Data & AI Platform
# Module:       core.ai.dataset_builders
# File:         models.py
# Path:         core/ai/dataset_builders/models.py
#
# Summary:      Defines domain models for the AI dataset builders module.
# Purpose:      Provides typed structures used by AI dataset builders processing and exchange flows.
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
#   - Main types: FreshnessPolicy, FeatureContract
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, dataclasses, pathlib, typing
#   - Constraints: File-system paths and serialized artifact formats
#     must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FreshnessPolicy:
    warn_after_hours: int
    error_after_hours: int


@dataclass(slots=True)
class FeatureContract:
    name: str
    description: str
    entity: list[str]
    relation: str
    sql_file: str
    timestamp_column: str
    feature_columns: list[str]
    transformation: str
    materialization: str
    freshness: FreshnessPolicy
    null_handling: dict[str, Any]
    owner: str
    training_serving_parity: bool
    serving_join_keys: list[str]
    leakage_prevention: list[str]
    labels_relation: str | None = None
    labels_timestamp_column: str | None = None
    source_path: Path | None = None
