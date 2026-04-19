# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_risk_and_retention_modules.py
# Path:         tests/business/test_risk_and_retention_modules.py
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
#   - Key APIs: test_risk_and_retention_modules_return_expected_payloads, test_risk_retention_detail_routes_work
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_risk_retention_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "risk_retention_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,order_date,customer_id,sku,category,quantity,unit_price,promised_date,actual_delivery_date,shipment_status,carrier,region",
                "4001,2025-12-15,CUST-A,SKU-SEASON,winter,5,20,2025-12-20,2025-12-21,delivered,CarrierX,north",
                "4002,2026-01-10,CUST-A,SKU-BASE,core,2,15,2026-01-14,2026-01-14,delivered,CarrierX,north",
                "4003,2026-01-15,CUST-B,SKU-STEADY,core,3,10,2026-01-19,2026-01-18,delivered,CarrierY,east",
                "4004,2026-02-10,CUST-B,SKU-BASE,core,1,15,2026-02-16,2026-02-15,delivered,CarrierY,east",
                "4005,2026-02-12,CUST-C,SKU-STEADY,core,4,10,2026-02-17,2026-02-18,delivered,CarrierY,east",
                "4006,2026-03-01,CUST-D,SKU-SPIKE,promo,20,25,2026-03-05,2026-03-09,delivered,CarrierZ,west",
                "4007,2026-03-01,CUST-E,SKU-SPIKE,promo,18,25,2026-03-05,2026-03-08,delivered,CarrierZ,west",
                "4008,2026-03-05,CUST-C,SKU-STEADY,core,2,10,2026-03-10,,in_transit,CarrierY,east",
                "4009,2026-03-10,CUST-B,SKU-BASE,core,1,15,2026-03-14,2026-03-14,delivered,CarrierY,east",
                "4010,2026-03-20,CUST-C,SKU-STEADY,core,3,10,2026-03-25,,processing,CarrierY,east",
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


def test_risk_and_retention_modules_return_expected_payloads(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_risk_retention_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    routes = [
        (
            "/api/v1/customer-churn/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["high_risk_customer_count"] == 1,
        ),
        (
            "/api/v1/sales-anomalies/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["spike_count"] == 1,
        ),
        (
            "/api/v1/seasonality/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["strong_seasonal_sku_count"] == 2,
        ),
        (
            "/api/v1/fulfillment-sla/summary",
            {"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
            lambda payload: payload["summary"]["delayed_order_count"] == 4,
        ),
    ]

    for endpoint, params, check in routes:
        response = client.get(endpoint, params=params)
        assert response.status_code == 200, response.text
        assert check(response.json())


def test_risk_retention_detail_routes_work(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_risk_retention_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    customer_churn = client.get(
        "/api/v1/customer-churn/customers/CUST-A",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert customer_churn.status_code == 200
    assert customer_churn.json()["churn_risk_band"] == "high"

    sales_anomaly = client.get(
        "/api/v1/sales-anomalies/days/2026-03-01",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert sales_anomaly.status_code == 200
    assert sales_anomaly.json()["anomaly_type"] == "spike"

    seasonality = client.get(
        "/api/v1/seasonality/skus/SKU-SEASON",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert seasonality.status_code == 200
    assert seasonality.json()["seasonality_band"] == "strong_seasonal"

    fulfillment = client.get(
        "/api/v1/fulfillment-sla/orders/4010",
        params={"upload_id": upload_id, "uploads_dir": str(uploads_dir), "refresh": "true"},
    )
    assert fulfillment.status_code == 200
    assert fulfillment.json()["sla_band"] == "breach_risk"
