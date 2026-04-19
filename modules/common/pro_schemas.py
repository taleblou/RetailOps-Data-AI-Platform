# Project:      RetailOps Data & AI Platform
# Module:       modules.common
# File:         pro_schemas.py
# Path:         modules/common/pro_schemas.py
#
# Summary:      Defines shared response schemas for platform-extension modules.
# Purpose:      Keeps Pro module API contracts consistent across CDC, streaming, lakehouse, metadata, feature store, query layer, and advanced serving.
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
#   - Main types: ComposeServiceResponse, PlatformExtensionDeploymentFields
#   - Key APIs: None; shared Pydantic models only.
#   - Dependencies: __future__, pydantic
#   - Constraints: Shared field names must remain stable because multiple routers expose them.
#   - Compatibility: Python 3.11+ with repository API dependencies.

from __future__ import annotations

from pydantic import BaseModel, Field


class ComposeServiceResponse(BaseModel):
    name: str
    image: str
    depends_on: list[str] = Field(default_factory=list)
    has_healthcheck: bool
    volume_count: int
    port_count: int


class PlatformExtensionDeploymentFields(BaseModel):
    compose_file: str
    service_inventory: list[ComposeServiceResponse] = Field(default_factory=list)
    bootstrap_commands: list[str] = Field(default_factory=list)
    health_checks: list[str] = Field(default_factory=list)
    readiness_checks: dict[str, bool] = Field(default_factory=dict)
    generated_files: dict[str, str] = Field(default_factory=dict)
