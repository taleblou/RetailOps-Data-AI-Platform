# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_csv
# File:         schemas.py
# Path:         modules/connector_csv/schemas.py
#
# Summary:      Defines schemas for the connector csv data contracts.
# Purpose:      Standardizes structured payloads used by the connector csv layer.
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
#   - Main types: CsvConnectorConfig
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: pydantic
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ with repository configuration dependencies.

from pydantic import BaseModel, Field


class CsvConnectorConfig(BaseModel):
    """Configuration for extracting tabular rows from a local CSV file."""

    file_path: str = Field(description="Path to the CSV file that should be ingested.")
    delimiter: str = Field(default=",", min_length=1, max_length=1)
    encoding: str = Field(default="utf-8", description="Text encoding used by the source file.")
    has_header: bool = Field(
        default=True, description="Whether the first row contains column names."
    )
