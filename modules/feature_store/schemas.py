# Project:      RetailOps Data & AI Platform
# Module:       modules.feature_store
# File:         schemas.py
# Path:         modules/feature_store/schemas.py
#
# Summary:      Defines schemas for feature-store deployment bundles.
# Purpose:      Standardizes structured feature-store payloads exposed through the Pro platform API.
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


class FeatureViewResponse(BaseModel):
    name: str
    entity: str
    ttl_days: int
    owner: str


class FeatureStoreBlueprintResponse(PlatformExtensionDeploymentFields):
    module_name: str
    platform_surface: str
    status: str
    generated_at: str
    artifact_path: str
    module_version: str
    engine: str
    offline_store: str
    online_store: str
    feature_views: list[FeatureViewResponse] = Field(default_factory=list)
    materialization_jobs: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
