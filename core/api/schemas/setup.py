# Project:      RetailOps Data & AI Platform
# Module:       core.api.schemas
# File:         setup.py
# Path:         core/api/schemas/setup.py
#
# Summary:      Provides implementation support for the API schemas workflow.
# Purpose:      Supports the API schemas layer inside the modular repository architecture.
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
#   - Main types: SetupLogEntry, SetupStepState, SetupSessionResponse, SetupSessionCreateRequest, SetupStoreRequest, SetupSourceRequest, ...
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, typing, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.12+ with repository configuration dependencies.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from core.ingestion.base.models import SourceType


class SetupLogEntry(BaseModel):
    timestamp: str
    step: str
    level: str
    message: str


class SetupStepState(BaseModel):
    key: str
    label: str
    status: str
    attempts: int = 0
    message: str | None = None
    artifact_path: str | None = None
    last_updated_at: str | None = None


class SetupSessionResponse(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    sample_mode: bool
    store: dict[str, Any] = Field(default_factory=dict)
    source: dict[str, Any] = Field(default_factory=dict)
    mapping: dict[str, str] = Field(default_factory=dict)
    enabled_modules: list[str] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
    transform_summary: dict[str, Any] | None = None
    dashboard_summary: dict[str, Any] | None = None
    forecast_summary: dict[str, Any] | None = None
    training_summary: dict[str, Any] | None = None
    steps: list[SetupStepState] = Field(default_factory=list)
    logs: list[SetupLogEntry] = Field(default_factory=list)
    progress_percent: int = 0
    next_step: str | None = None


class SetupSessionCreateRequest(BaseModel):
    store_name: str | None = None
    store_code: str | None = None
    sample_mode: bool = False


class SetupStoreRequest(BaseModel):
    store_name: str
    store_code: str
    currency: str = "EUR"
    timezone: str = "Europe/Helsinki"


class SetupSourceRequest(BaseModel):
    source_type: SourceType
    source_name: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class SetupMappingRequest(BaseModel):
    mappings: dict[str, str] = Field(default_factory=dict)


class SetupModulesRequest(BaseModel):
    modules: list[str] = Field(default_factory=list)
