# Project:      RetailOps Data & AI Platform
# Module:       tests.ingestion
# File:         test_mapper.py
# Path:         tests/ingestion/test_mapper.py
#
# Summary:      Contains automated tests for the ingestion workflows and behaviors.
# Purpose:      Validates ingestion behavior and protects the repository against regressions.
# Scope:        test
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
#   - Main types: None.
#   - Key APIs: test_mapper_detects_aliases_and_required_columns
#   - Dependencies: core.ingestion.base.mapper
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from core.ingestion.base.mapper import ColumnMapper


def test_mapper_detects_aliases_and_required_columns() -> None:
    mapper = ColumnMapper()
    result = mapper.build_mapping(
        source_columns=["Order ID", "qty", "price_each"],
        required_columns=["order_id", "quantity", "unit_price"],
    )
    targets = {item.target for item in result.mappings}
    assert {"order_id", "quantity", "unit_price"}.issubset(targets)
    assert result.missing_required == []
