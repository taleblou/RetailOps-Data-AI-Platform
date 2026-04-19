# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_db
# File:         schemas.py
# Path:         modules/connector_db/schemas.py
#
# Summary:      Defines schemas for the connector db data contracts.
# Purpose:      Standardizes structured payloads used by the connector db layer.
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
#   - Main types: DatabaseConnectorConfig
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from pydantic import BaseModel, Field


class DatabaseConnectorConfig(BaseModel):
    """Configuration for extracting rows from a relational database source."""

    database_url: str = Field(description="Connection string for the source database.")
    query: str = Field(description="SQL query used to extract source rows.")
    sample_limit: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of preview rows returned during dry-run inspection.",
    )
