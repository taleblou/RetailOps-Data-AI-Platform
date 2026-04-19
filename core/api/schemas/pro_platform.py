# Project:      RetailOps Data & AI Platform
# Module:       core.api.schemas
# File:         pro_platform.py
# Path:         core/api/schemas/pro_platform.py
#
# Summary:      Defines shared API schemas for Pro platform summary, readiness, and deployment-plan endpoints.
# Purpose:      Standardizes high-level platform-extension payloads exposed through the public API.
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

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProPlatformModuleReadinessResponse(BaseModel):
    module_name: str
    status: str
    readiness_checks: dict[str, bool] = Field(default_factory=dict)
    generated_files: dict[str, str] = Field(default_factory=dict)


class ProPlatformSummaryResponse(BaseModel):
    platform_surface: str
    platform_name: str
    module_count: int
    deployment_ready_count: int
    artifact_root: str
    modules: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ProPlatformReadinessResponse(BaseModel):
    platform_surface: str
    platform_name: str
    module_count: int
    deployment_ready_count: int
    artifact_root: str
    modules: list[ProPlatformModuleReadinessResponse] = Field(default_factory=list)


class ProPlatformDeploymentPlanResponse(BaseModel):
    platform_surface: str
    platform_name: str
    artifact_root: str
    generated_at: str
    compose_chain: list[str] = Field(default_factory=list)
    compose_command: str
    environment_variables: list[str] = Field(default_factory=list)
    module_count: int
    deployment_ready_count: int
    modules: dict[str, dict[str, Any]] = Field(default_factory=dict)
    operator_checklist: list[str] = Field(default_factory=list)
