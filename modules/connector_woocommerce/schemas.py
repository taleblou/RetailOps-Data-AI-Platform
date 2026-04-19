# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_woocommerce
# File:         schemas.py
# Path:         modules/connector_woocommerce/schemas.py
#
# Summary:      Defines schemas for the connector woocommerce data contracts.
# Purpose:      Standardizes structured payloads used by the connector woocommerce layer.
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
#   - Main types: WooCommerceConnectorConfig
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from pydantic import BaseModel, Field


class WooCommerceConnectorConfig(BaseModel):
    store_url: str
    consumer_key: str
    consumer_secret: str
    resource: str = "orders"
    api_version: str = "wc/v3"
    verify_ssl: bool = True
    default_status: str | None = None
    page_size: int = Field(default=50, ge=1, le=100)
