# Project:      RetailOps Data & AI Platform
# Module:       tests.ingestion
# File:         test_validator.py
# Path:         tests/ingestion/test_validator.py
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
#   - Key APIs: test_validator_detects_missing_and_duplicate_values
#   - Dependencies: core.ingestion.base.validator
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from core.ingestion.base.validator import DataValidator


def test_validator_detects_missing_and_duplicate_values() -> None:
    validator = DataValidator()
    result = validator.validate(
        rows=[
            {"order_id": "1001", "quantity": "1"},
            {"order_id": "1001", "quantity": ""},
        ],
        required_columns=["order_id", "quantity"],
        type_hints={"quantity": "int"},
        unique_key_columns=["order_id"],
    )
    assert not result.valid
    codes = {issue.code for issue in result.errors}
    assert "required_missing" in codes
    assert "duplicate_key" in codes
