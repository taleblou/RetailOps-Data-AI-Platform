# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_prestashop
# File:         schemas.py
# Path:         modules/connector_prestashop/schemas.py
#
# Summary:      Defines schemas for the connector prestashop data contracts.
# Purpose:      Standardizes structured payloads used by the connector prestashop layer.
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
#   - Main types: PrestaShopConnectorConfig
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from pydantic import BaseModel, Field


class PrestaShopConnectorConfig(BaseModel):
    base_url: str
    api_key: str
    resource: str = "orders"
    page_size: int = Field(default=25, ge=1, le=100)
    display: str = "full"
