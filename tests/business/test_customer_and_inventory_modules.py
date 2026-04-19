# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_customer_and_inventory_modules.py
# Path:         tests/business/test_customer_and_inventory_modules.py
#
# Summary:      Contains automated tests for the business workflows and behaviors.
# Purpose:      Validates business behavior and protects the repository against regressions.
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
#   - Key APIs: test_customer_and_inventory_modules_return_expected_payloads, test_customer_inventory_detail_routes_work
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_customer_inventory_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "customer_inventory_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,order_date,customer_id,sku,category,quantity,unit_price,on_hand_units",
                "3001,2026-01-05,CUST-01,SKU-A,beverages,10,10,5",
                "3002,2026-02-10,CUST-01,SKU-A,beverages,8,10,5",
                "3003,2026-03-15,CUST-02,SKU-B,snacks,9,12,40",
                "3004,2026-01-20,CUST-03,SKU-C,home,15,4,60",
                "3005,2026-03-18,CUST-03,SKU-C,home,1,4,60",
                "3006,2025-11-10,CUST-04,SKU-D,beauty,1,20,25",
                "3007,2026-03-10,CUST-05,SKU-A,beverages,9,10,5",
                "3008,2026-01-12,CUST-06,SKU-B,snacks,1,12,40",
            ]
        ),
        encoding="utf-8",
    )
    metadata_path = uploads_dir / f"{upload_id}.json"
    metadata_path.write_text(
        json.dumps(
            {
                "upload_id": upload_id,
                "filename": "orders.csv",
                "stored_path": str(csv_path),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return upload_id, uploads_dir


def test_customer_and_inventory_modules_return_expected_payloads(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_customer_inventory_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    routes = [
        (
            "/api/v1/customer-cohorts/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["largest_cohort_month"] == "2026-01",
        ),
        (
            "/api/v1/inventory-aging/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["critical_aging_count"] == 1,
        ),
        (
            "/api/v1/abc-xyz/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["z_class_sku_count"] == 3,
        ),
    ]

    for endpoint, params, check in routes:
        response = client.get(endpoint, params=params)
        assert response.status_code == 200, response.text
        assert check(response.json())


def test_customer_inventory_detail_routes_work(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_customer_inventory_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    cohorts = client.get(
        "/api/v1/customer-cohorts/cohorts/2026-01",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert cohorts.status_code == 200
    assert cohorts.json()["customer_count"] == 3
    assert cohorts.json()["repeat_customer_count"] == 2

    inventory = client.get(
        "/api/v1/inventory-aging/skus/SKU-D",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert inventory.status_code == 200
    assert inventory.json()["aging_band"] == "critical"

    abc_xyz = client.get(
        "/api/v1/abc-xyz/skus/SKU-B",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert abc_xyz.status_code == 200
    assert abc_xyz.json()["abc_class"] == "B"
    assert abc_xyz.json()["xyz_class"] == "Z"
