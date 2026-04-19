# Project:      RetailOps Data & AI Platform
# Module:       modules.metadata
# File:         schemas.py
# Path:         modules/metadata/schemas.py
#
# Summary:      Defines schemas for metadata deployment bundles.
# Purpose:      Standardizes structured metadata payloads exposed through the Pro platform API.
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


class MetadataWorkflowResponse(BaseModel):
    name: str
    source_type: str
    output: str


class MetadataServiceConnectionResponse(BaseModel):
    name: str
    kind: str
    connection_ref: str


class MetadataBlueprintResponse(PlatformExtensionDeploymentFields):
    module_name: str
    platform_surface: str
    status: str
    generated_at: str
    artifact_path: str
    module_version: str
    platform: str
    lineage_enabled: bool
    workflows: list[MetadataWorkflowResponse] = Field(default_factory=list)
    service_connections: list[MetadataServiceConnectionResponse] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
