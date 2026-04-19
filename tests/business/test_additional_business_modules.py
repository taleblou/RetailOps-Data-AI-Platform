# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_additional_business_modules.py
# Path:         tests/business/test_additional_business_modules.py
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
#   - Key APIs: test_additional_business_module_routes_return_artifacts
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_business_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "commercial_foundations_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,order_date,customer_id,sku,category,quantity,unit_price,list_price,discount_amount,promo_code,supplier_id,supplier_name,ordered_qty,received_qty,lead_time_days,supplier_moq,payment_provider,paid_amount,refund_amount,total_amount",
                "1001,2026-03-01,CUST-01,SKU-001,beverages,2,9.0,10.0,1.0,SPRING10,SUP-01,Nordic Foods,20,18,9,12,stripe,18,0,18",
                "1002,2026-03-05,CUST-01,SKU-002,snacks,3,5.0,5.0,0.0,,SUP-02,Baltic Supply,30,30,6,10,adyen,15,0,15",
                "1003,2026-03-10,CUST-02,SKU-001,beverages,1,9.0,10.0,1.0,SPRING10,SUP-01,Nordic Foods,12,10,11,12,stripe,9,0,9",
                "1004,2025-12-01,CUST-03,SKU-003,household,1,25.0,30.0,5.0,WINTER5,SUP-03,Slow Vendor,8,5,14,4,paypal,10,0,25",
                "1005,2026-03-12,CUST-02,SKU-004,beverages,2,12.0,12.0,0.0,,SUP-02,Baltic Supply,24,24,5,8,stripe,24,4,24",
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


def test_additional_business_module_routes_return_artifacts(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_business_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    routes = [
        (
            "/api/v1/promotion-pricing/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["promoted_rows"] >= 1,
        ),
        (
            "/api/v1/supplier-procurement/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["supplier_count"] == 3,
        ),
        (
            "/api/v1/customer-intelligence/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["customer_count"] == 3,
        ),
        (
            "/api/v1/payment-reconciliation/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["order_count"] == 5,
        ),
    ]

    for endpoint, params, check in routes:
        response = client.get(endpoint, params=params)
        assert response.status_code == 200, response.text
        assert check(response.json())
