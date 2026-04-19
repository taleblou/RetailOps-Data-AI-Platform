# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_shopify
# File:         schemas.py
# Path:         modules/connector_shopify/schemas.py
#
# Summary:      Defines schemas for the connector shopify data contracts.
# Purpose:      Standardizes structured payloads used by the connector shopify layer.
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
#   - Main types: ShopifyConnectorConfig
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from pydantic import BaseModel, Field


class ShopifyConnectorConfig(BaseModel):
    """Configuration for extracting Shopify resources through the Admin API."""

    store_url: str = Field(description="Base store URL, for example https://example.myshopify.com.")
    access_token: str = Field(description="Admin API access token for the store.")
    api_version: str = Field(default="2024-01", description="Shopify Admin API version.")
    resource: str = Field(default="orders", description="Primary Shopify resource to extract.")
