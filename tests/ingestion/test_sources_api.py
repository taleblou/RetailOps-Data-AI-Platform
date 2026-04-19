# Project:      RetailOps Data & AI Platform
# Module:       tests.ingestion
# File:         test_sources_api.py
# Path:         tests/ingestion/test_sources_api.py
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
#   - Key APIs: test_sources_api_can_register_test_and_import_csv
#   - Dependencies: pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def test_sources_api_can_register_test_and_import_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text(
        "order_id,order_date,customer_id,sku,quantity,unit_price\n"
        "1001,2026-03-20T10:00:00,5001,SKU-001,2,10.50\n",
        encoding="utf-8",
    )
    repository = MemoryRepository()
    app = create_app(repository=repository)
    client = TestClient(app)

    create_response = client.post(
        "/sources",
        json={
            "name": "orders-csv",
            "type": "csv",
            "config": {"file_path": str(csv_path)},
        },
    )
    assert create_response.status_code == 201
    source_id = create_response.json()["source_id"]

    test_response = client.post(f"/sources/{source_id}/test")
    assert test_response.status_code == 200
    assert test_response.json()["ok"] is True

    import_response = client.post(
        f"/sources/{source_id}/import",
        json={
            "required_columns": [
                "order_id",
                "order_date",
                "customer_id",
                "sku",
                "quantity",
                "unit_price",
            ],
            "type_hints": {"quantity": "int", "unit_price": "float"},
            "unique_key_columns": ["order_id"],
        },
    )
    assert import_response.status_code == 200, import_response.text
    assert import_response.json()["rows_loaded"] == 1

    status_response = client.get(f"/sources/{source_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["source"]["status"] == "ready"
