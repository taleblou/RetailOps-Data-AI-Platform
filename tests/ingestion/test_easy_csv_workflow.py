# Project:      RetailOps Data & AI Platform
# Module:       tests.ingestion
# File:         test_easy_csv_workflow.py
# Path:         tests/ingestion/test_easy_csv_workflow.py
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
#   - Key APIs: test_easy_csv_json_workflow, test_easy_csv_wizard_html_flow
#   - Dependencies: pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def test_easy_csv_json_workflow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    repository = MemoryRepository()
    app = create_app(repository=repository)
    client = TestClient(app)

    csv_content = (
        "Order Number,Date,Customer,SKU Code,Qty,Price\n"
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
                "order_id": "Order Number",
                "order_date": "Date",
                "customer_id": "Customer",
                "sku": "SKU Code",
                "quantity": "Qty",
                "unit_price": "Price",
            }
        },
    )
    assert mapping_response.status_code == 200, mapping_response.text
    assert mapping_response.json()["required_missing"] == []

    validation_response = client.post(f"/easy-csv/{upload_id}/validate")
    assert validation_response.status_code == 200, validation_response.text
    validation_payload = validation_response.json()
    assert validation_payload["can_import"] is True
    assert validation_payload["blocking_errors"] == []

    import_response = client.post(f"/easy-csv/{upload_id}/import")
    assert import_response.status_code == 200, import_response.text
    import_payload = import_response.json()
    assert import_payload["rows_loaded"] == 2
    assert import_payload["source_status"] == "ready"
    assert len(repository.raw_rows) == 2

    transform_response = client.post(f"/easy-csv/{upload_id}/transform")
    assert transform_response.status_code == 200, transform_response.text
    transform_payload = transform_response.json()
    assert transform_payload["total_orders"] == 2
    assert transform_payload["output_row_count"] == 2

    dashboard_response = client.post(f"/easy-csv/{upload_id}/dashboard")
    assert dashboard_response.status_code == 200, dashboard_response.text
    dashboard_payload = dashboard_response.json()
    assert dashboard_payload["dashboard_url"] == f"/easy-csv/{upload_id}/dashboard/view"
    assert len(dashboard_payload["cards"]) == 4

    forecast_response = client.post(f"/easy-csv/{upload_id}/forecast")
    assert forecast_response.status_code == 200, forecast_response.text
    forecast_payload = forecast_response.json()
    assert forecast_payload["baseline_method"] == "daily_average_baseline"
    assert [item["horizon_days"] for item in forecast_payload["horizons"]] == [7, 14, 30]


def test_easy_csv_wizard_html_flow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    repository = MemoryRepository()
    app = create_app(repository=repository)
    client = TestClient(app)

    home_response = client.get("/easy-csv/wizard")
    assert home_response.status_code == 200
    assert "RetailOps Easy CSV Wizard" in home_response.text

    csv_content = (
        "order_id,order_date,sku,quantity,unit_price\n1001,2026-03-20T10:00:00,SKU-001,2,10.50\n"
    )

    upload_response = client.post(
        "/easy-csv/wizard/upload",
        files={"file": ("orders.csv", csv_content.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    assert upload_response.status_code == 303
    redirect_url = upload_response.headers["location"]
    assert "/easy-csv/" in redirect_url and "message=Upload%20completed." in redirect_url

    detail_response = client.get(redirect_url)
    assert detail_response.status_code == 200
    assert "Current file" in detail_response.text
    assert "Rows loaded:" in detail_response.text
