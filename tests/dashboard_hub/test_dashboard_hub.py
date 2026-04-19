# Project:      RetailOps Data & AI Platform
# Module:       tests.dashboard_hub
# File:         test_dashboard_hub.py
# Path:         tests/dashboard_hub/test_dashboard_hub.py
#
# Summary:      Contains automated tests for the dashboard hub workflows and behaviors.
# Purpose:      Validates dashboard hub behavior and protects the repository against regressions.
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
#   - Key APIs: test_dashboard_workspace_routes_return_unified_payload, test_dashboard_workspace_publish_and_html_view
#   - Dependencies: pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _prepare_upload_with_transform(client: TestClient) -> str:
    csv_content = (
        "order_id,order_date,customer_id,sku,quantity,unit_price,unit_cost,category,"
        "store_code,region,promo_code,discount_rate,returned,promised_date,"
        "actual_delivery_date,available_qty,inbound_qty,lead_time_days\n"
        "1001,2026-03-20,5001,SKU-001,2,25.0,14.0,electronics,"
        "HELSINKI,SOUTH,SPRING10,0.10,false,2026-03-23,2026-03-22,30,5,4\n"
        "1002,2026-03-21,5002,SKU-002,1,80.0,48.0,fashion,TURKU,WEST,,0.00,"
        "true,2026-03-24,2026-03-27,5,0,6\n"
        "1003,2026-03-22,5001,SKU-001,3,25.0,14.0,electronics,"
        "HELSINKI,SOUTH,SPRING10,0.10,false,2026-03-25,2026-03-26,18,10,4\n"
        "1004,2026-03-23,5003,SKU-003,4,12.0,7.0,home,OULU,NORTH,,0.00,"
        "false,2026-03-27,2026-03-27,80,25,5\n"
        "1005,2026-03-24,5004,SKU-004,2,60.0,30.0,beauty,TAMPERE,SOUTH,"
        "BEAUTY15,0.15,true,2026-03-28,2026-03-29,12,3,7\n"
        "1006,2026-03-25,5005,SKU-005,1,140.0,90.0,electronics,HELSINKI,"
        "SOUTH,,0.00,false,2026-03-29,2026-03-30,4,0,8\n"
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
                "store_code": "store_code",
            }
        },
    )
    assert mapping_response.status_code == 200, mapping_response.text
    assert client.post(f"/easy-csv/{upload_id}/validate").status_code == 200
    assert client.post(f"/easy-csv/{upload_id}/import").status_code == 200
    assert client.post(f"/easy-csv/{upload_id}/transform").status_code == 200
    return upload_id


def test_dashboard_workspace_routes_return_unified_payload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    repository = MemoryRepository()
    client = TestClient(create_app(repository=repository))
    upload_id = _prepare_upload_with_transform(client)
    artifact_root = tmp_path / "dashboard-artifacts"

    response = client.get(
        "/api/v1/dashboard-hub/workspace",
        params={
            "upload_id": upload_id,
            "artifact_root": str(artifact_root),
            "max_rows": 6,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["upload_id"] == upload_id
    assert payload["workspace_title"] == "RetailOps Professional Dashboard Workspace"
    assert payload["report_count"] >= 20
    assert payload["overview"]["total_orders"] == 6
    assert payload["available_module_count"] >= 4
    module_keys = {item["module_key"] for item in payload["module_status"]}
    assert {"forecasting", "stockout_intelligence", "reorder_engine"}.issubset(module_keys)
    assert "/api/v1/business-reports/executive-review" in {
        item["endpoint"] for item in payload["endpoint_catalog"]
    }


def test_dashboard_workspace_publish_and_html_view(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    repository = MemoryRepository()
    client = TestClient(create_app(repository=repository))
    upload_id = _prepare_upload_with_transform(client)
    artifact_root = tmp_path / "published-workspace"

    publish_response = client.post(
        "/api/v1/dashboard-hub/publish",
        json={
            "upload_id": upload_id,
            "artifact_root": str(artifact_root),
            "max_rows": 5,
        },
    )
    assert publish_response.status_code == 200, publish_response.text
    publish_payload = publish_response.json()

    assert Path(publish_payload["artifact_path"]).exists()
    assert Path(publish_payload["html_artifact_path"]).exists()

    artifact_response = client.get(
        f"/api/v1/dashboard-hub/artifact/{upload_id}",
        params={"artifact_root": str(artifact_root)},
    )
    assert artifact_response.status_code == 200, artifact_response.text
    assert artifact_response.json()["workspace"]["workspace_url"].endswith(
        f"/dashboard/{upload_id}"
    )

    redirect_response = client.get(
        f"/api/v1/dashboard-hub/{upload_id}/view",
        follow_redirects=False,
    )
    assert redirect_response.status_code == 307, redirect_response.text
    assert redirect_response.headers["location"].endswith(f"/dashboard/{upload_id}")

    html_response = client.get(
        f"/dashboard/{upload_id}/operations",
        params={"artifact_root": str(artifact_root), "max_rows": 5},
    )
    assert html_response.status_code == 200, html_response.text
    assert "Operational Analytics" in html_response.text
    assert "Runtime Without Services" in html_response.text
