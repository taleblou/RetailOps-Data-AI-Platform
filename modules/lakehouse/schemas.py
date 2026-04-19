# Project:      RetailOps Data & AI Platform
# Module:       modules.lakehouse
# File:         schemas.py
# Path:         modules/lakehouse/schemas.py
#
# Summary:      Defines schemas for lakehouse deployment bundles.
# Purpose:      Standardizes structured lakehouse payloads exposed through the Pro platform API.
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


class LakehouseLayerResponse(BaseModel):
    layer_name: str
    purpose: str
    tables: list[str] = Field(default_factory=list)


class LakehouseBlueprintResponse(PlatformExtensionDeploymentFields):
    module_name: str
    platform_surface: str
    status: str
    generated_at: str
    artifact_path: str
    module_version: str
    catalog_type: str
    table_format: str
    object_storage: str
    layers: list[LakehouseLayerResponse] = Field(default_factory=list)
    spark_jobs: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
