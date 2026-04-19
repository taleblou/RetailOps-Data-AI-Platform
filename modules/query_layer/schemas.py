# Project:      RetailOps Data & AI Platform
# Module:       modules.query_layer
# File:         schemas.py
# Path:         modules/query_layer/schemas.py
#
# Summary:      Defines schemas for query-layer deployment bundles.
# Purpose:      Standardizes structured query-layer payloads exposed through the Pro platform API.
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


class QueryCatalogResponse(BaseModel):
    name: str
    connector_name: str
    target: str


class QueryLayerBlueprintResponse(PlatformExtensionDeploymentFields):
    module_name: str
    platform_surface: str
    status: str
    generated_at: str
    artifact_path: str
    module_version: str
    engine: str
    catalogs: list[QueryCatalogResponse] = Field(default_factory=list)
    federation_queries: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
