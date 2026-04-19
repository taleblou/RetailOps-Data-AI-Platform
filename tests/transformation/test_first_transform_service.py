# Project:      RetailOps Data & AI Platform
# Module:       tests.transformation
# File:         test_first_transform_service.py
# Path:         tests/transformation/test_first_transform_service.py
#
# Summary:      Contains automated tests for the transformation workflows and behaviors.
# Purpose:      Validates transformation behavior and protects the repository against regressions.
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
#   - Key APIs: test_run_first_transform_accepts_positional_rows
#   - Dependencies: pathlib, core.transformations.service
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from pathlib import Path

from core.transformations.service import run_first_transform


def test_run_first_transform_accepts_positional_rows(tmp_path: Path) -> None:
    rows = [
        {
            "order_id": "1001",
            "order_date": "2026-03-20T10:00:00",
            "customer_id": "5001",
            "sku": "SKU-001",
            "quantity": "2",
            "unit_price": "10.50",
        },
        {
            "order_id": "1002",
            "order_date": "2026-03-21T11:00:00",
            "customer_id": "5002",
            "sku": "SKU-002",
            "quantity": "1",
            "unit_price": "15.00",
        },
    ]

    artifact = run_first_transform(rows, artifact_dir=tmp_path, upload_id="upload_123")

    assert artifact.input_row_count == 2
    assert artifact.output_row_count == 2
    assert artifact.total_orders == 2
    assert artifact.daily_sales[0].total_revenue == 21.0
