# Project:      RetailOps Data & AI Platform
# Module:       modules.advanced_serving
# File:         schemas.py
# Path:         modules/advanced_serving/schemas.py
#
# Summary:      Defines schemas for advanced-serving deployment bundles.
# Purpose:      Standardizes structured advanced-serving payloads exposed through the Pro platform API.
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

from pydantic import BaseModel, Field

from modules.common.pro_schemas import PlatformExtensionDeploymentFields


class AdvancedServingServiceResponse(BaseModel):
    name: str
    model_alias: str
    deployment_mode: str
    endpoint: str


class AdvancedServingBlueprintResponse(PlatformExtensionDeploymentFields):
    module_name: str
    platform_surface: str
    status: str
    generated_at: str
    artifact_path: str
    module_version: str
    platform: str
    services: list[AdvancedServingServiceResponse] = Field(default_factory=list)
    shadow_deployments: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
