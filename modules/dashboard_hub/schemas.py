# Project:      RetailOps Data & AI Platform
# Module:       modules.dashboard_hub
# File:         schemas.py
# Path:         modules/dashboard_hub/schemas.py
#
# Summary:      Defines schemas for the dashboard hub data contracts.
# Purpose:      Standardizes structured payloads used by the dashboard hub layer.
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
#   - Main types: DashboardWorkspaceResponse, DashboardWorkspacePublishRequest, DashboardWorkspaceArtifactResponse
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, typing, pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DashboardWorkspaceResponse(BaseModel):
    upload_id: str
    generated_at: str
    refresh_used: bool = False
    workspace_title: str
    workspace_url: str
    report_count: int = 0
    available_module_count: int = 0
    unavailable_module_count: int = 0
    artifact_root: str
    overview: dict[str, Any] = Field(default_factory=dict)
    scorecard_summary: dict[str, Any] = Field(default_factory=dict)
    executive_review: dict[str, Any] = Field(default_factory=dict)
    charts: dict[str, Any] = Field(default_factory=dict)
    module_status: list[dict[str, Any]] = Field(default_factory=list)
    action_center: list[dict[str, Any]] = Field(default_factory=list)
    report_catalog: dict[str, Any] = Field(default_factory=dict)
    endpoint_catalog: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DashboardWorkspacePublishRequest(BaseModel):
    upload_id: str
    uploads_dir: str = "data/uploads"
    artifact_root: str = "data/artifacts/dashboard_hub"
    refresh: bool = False
    max_rows: int = 8


class DashboardWorkspaceArtifactResponse(BaseModel):
    upload_id: str
    artifact_path: str
    html_artifact_path: str
    workspace_url: str
    workspace: DashboardWorkspaceResponse
