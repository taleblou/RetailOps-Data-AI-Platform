# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_adobe_commerce
# File:         schemas.py
# Path:         modules/connector_adobe_commerce/schemas.py
#
# Summary:      Defines schemas for the connector adobe commerce data contracts.
# Purpose:      Standardizes structured payloads used by the connector adobe commerce layer.
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
#   - Main types: AdobeCommerceConnectorConfig
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from pydantic import BaseModel, Field


class AdobeCommerceConnectorConfig(BaseModel):
    base_url: str
    access_token: str
    resource: str = "orders"
    store_code: str = "default"
    page_size: int = Field(default=50, ge=1, le=200)
    search_criteria: dict[str, str | int | float] = Field(default_factory=dict)
