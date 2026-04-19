# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_margin_and_assortment_modules.py
# Path:         tests/business/test_margin_and_assortment_modules.py
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
#   - Key APIs: test_margin_and_assortment_modules_return_expected_payloads, test_margin_and_assortment_detail_routes_work
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_margin_and_assortment_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "margin_and_assortment_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,order_date,customer_id,sku,category,quantity,unit_price,list_price,unit_cost,promo_code",
                "2001,2026-03-01,CUST-01,SKU-001,beverages,2,10,12,6,SPRING10",
                "2001,2026-03-01,CUST-01,SKU-002,snacks,1,6,6,3,",
                "2002,2026-03-02,CUST-02,SKU-001,beverages,1,10,12,6,SPRING10",
                "2002,2026-03-02,CUST-02,SKU-003,household,1,20,25,22,",
                "2003,2026-03-03,CUST-03,SKU-001,beverages,1,10,12,6,SPRING10",
                "2003,2026-03-03,CUST-03,SKU-002,snacks,2,6,6,3,",
                "2004,2026-03-04,CUST-04,SKU-004,personal_care,1,8,10,2,CARE20",
                "2005,2026-03-05,CUST-05,SKU-005,beverages,1,5,6,0,",
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


def test_margin_and_assortment_modules_return_expected_payloads(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_margin_and_assortment_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    routes = [
        (
            "/api/v1/assortment-intelligence/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["sku_count"] == 5,
        ),
        (
            "/api/v1/basket-affinity/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["pair_count"] >= 2,
        ),
        (
            "/api/v1/profitability-intelligence/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["loss_making_sku_count"] == 1,
        ),
    ]

    for endpoint, params, check in routes:
        response = client.get(endpoint, params=params)
        assert response.status_code == 200, response.text
        assert check(response.json())


def test_margin_and_assortment_detail_routes_work(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_margin_and_assortment_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    assortment = client.get(
        "/api/v1/assortment-intelligence/skus/SKU-001",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert assortment.status_code == 200
    assert assortment.json()["movement_class"] == "hero"

    basket = client.get(
        "/api/v1/basket-affinity/pairs/SKU-001/SKU-002",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert basket.status_code == 200
    assert basket.json()["pair_order_count"] == 2

    profitability = client.get(
        "/api/v1/profitability-intelligence/skus/SKU-003",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert profitability.status_code == 200
    assert profitability.json()["margin_band"] == "loss_making"
