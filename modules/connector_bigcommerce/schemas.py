# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_bigcommerce
# File:         schemas.py
# Path:         modules/connector_bigcommerce/schemas.py
#
# Summary:      Defines schemas for the connector bigcommerce data contracts.
# Purpose:      Standardizes structured payloads used by the connector bigcommerce layer.
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
#   - Main types: BigCommerceConnectorConfig
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from pydantic import BaseModel, Field


class BigCommerceConnectorConfig(BaseModel):
    store_hash: str
    access_token: str
    resource: str = "orders"
    api_version: str = "v3"
    page_size: int = Field(default=50, ge=1, le=250)
    api_root: str = "https://api.bigcommerce.com/stores"
