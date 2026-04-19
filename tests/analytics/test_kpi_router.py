# Project:      RetailOps Data & AI Platform
# Module:       tests.analytics
# File:         test_kpi_router.py
# Path:         tests/analytics/test_kpi_router.py
#
# Summary:      Contains automated tests for the analytics workflows and behaviors.
# Purpose:      Validates analytics behavior and protects the repository against regressions.
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
#   - Key APIs: test_kpi_router_is_mounted_on_main_app, test_kpi_get_endpoints_support_json_and_csv
#   - Dependencies: pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _prepare_upload_with_transform(client: TestClient) -> str:
    csv_content = (
        "order_id,order_date,customer_id,sku,quantity,unit_price\n"
        "1001,2026-03-20T10:00:00,5001,SKU-001,2,10.50\n"
        "1002,2026-03-21T11:00:00,5002,SKU-002,1,15.00\n"
    )
    upload_response = client.post(
        "/easy-csv/upload",
        files={"file": ("orders.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert upload_response.status_code == 200, upload_response.text
    upload_id = upload_response.json()["upload_id"]

    mapping_response = client.post(
        f"/easy-csv/{upload_id}/mapping",
        json={
            "mappings": {
                "order_id": "order_id",
                "order_date": "order_date",
                "customer_id": "customer_id",
                "sku": "sku",
                "quantity": "quantity",
                "unit_price": "unit_price",
            }
        },
    )
    assert mapping_response.status_code == 200, mapping_response.text

    validation_response = client.post(f"/easy-csv/{upload_id}/validate")
    assert validation_response.status_code == 200, validation_response.text

    import_response = client.post(f"/easy-csv/{upload_id}/import")
    assert import_response.status_code == 200, import_response.text

    transform_response = client.post(f"/easy-csv/{upload_id}/transform")
    assert transform_response.status_code == 200, transform_response.text
    return upload_id


def test_kpi_router_is_mounted_on_main_app(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    repository = MemoryRepository()
    app = create_app(repository=repository)
    client = TestClient(app)

    upload_id = _prepare_upload_with_transform(client)
    response = client.get(f"/api/v1/kpis/overview?upload_id={upload_id}")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total_orders"] == 2
    assert payload["sales_days"] == 2


def test_kpi_get_endpoints_support_json_and_csv(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    repository = MemoryRepository()
    app = create_app(repository=repository)
    client = TestClient(app)

    upload_id = _prepare_upload_with_transform(client)

    sales_response = client.get(f"/api/v1/kpis/sales-daily?upload_id={upload_id}")
    assert sales_response.status_code == 200, sales_response.text
    sales_payload = sales_response.json()
    assert len(sales_payload) == 2
    assert sales_payload[0]["sales_date"] == "2026-03-20"

    csv_response = client.get(f"/api/v1/kpis/inventory-health?upload_id={upload_id}&format=csv")
    assert csv_response.status_code == 200, csv_response.text
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "sku,on_hand,days_of_cover,low_stock" in csv_response.text
