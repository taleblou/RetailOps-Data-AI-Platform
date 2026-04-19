# Project:      RetailOps Data & AI Platform
# Module:       modules.cdc
# File:         schemas.py
# Path:         modules/cdc/schemas.py
#
# Summary:      Defines schemas for CDC deployment bundles.
# Purpose:      Standardizes structured CDC payloads exposed through the Pro platform API.
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


class CdcRouteResponse(BaseModel):
    source_table: str
    destination_topic: str
    storage_target: str


class CdcBlueprintResponse(PlatformExtensionDeploymentFields):
    module_name: str
    platform_surface: str
    status: str
    generated_at: str
    artifact_path: str
    module_version: str
    connector_name: str
    source_database: str
    kafka_compatible_runtime: str
    raw_event_topic_prefix: str
    snapshot_mode: str
    replication_slot: str
    publication_name: str
    tables: list[str] = Field(default_factory=list)
    routes: list[CdcRouteResponse] = Field(default_factory=list)
    connector_properties: dict[str, str | bool] = Field(default_factory=dict)
    config_templates: dict[str, str] = Field(default_factory=dict)
