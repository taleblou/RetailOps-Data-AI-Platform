# Project:      RetailOps Data & AI Platform
# Module:       modules.streaming
# File:         schemas.py
# Path:         modules/streaming/schemas.py
#
# Summary:      Defines schemas for streaming deployment bundles.
# Purpose:      Standardizes structured streaming payloads exposed through the Pro platform API.
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


class StreamingTopicResponse(BaseModel):
    name: str
    partitions: int
    retention_hours: int
    cleanup_policy: str


class StreamingProcessorResponse(BaseModel):
    name: str
    input_topic: str
    output_topic: str
    responsibility: str


class StreamingConsumerGroupResponse(BaseModel):
    name: str
    purpose: str


class StreamingBlueprintResponse(PlatformExtensionDeploymentFields):
    module_name: str
    platform_surface: str
    status: str
    generated_at: str
    artifact_path: str
    module_version: str
    runtime: str
    topics: list[StreamingTopicResponse] = Field(default_factory=list)
    processors: list[StreamingProcessorResponse] = Field(default_factory=list)
    consumer_groups: list[StreamingConsumerGroupResponse] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
