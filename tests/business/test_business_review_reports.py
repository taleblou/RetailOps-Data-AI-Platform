# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_business_review_reports.py
# Path:         tests/business/test_business_review_reports.py
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
#   - Key APIs: test_business_review_report_endpoints_return_expected_payloads, test_business_review_sku_deep_dive_surfaces_risk_flags
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_business_review_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "business_review_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                (
                    "order_id,order_date,customer_id,store_code,region,sku,category,quantity,unit_price,list_price,"
                    "unit_cost,on_hand_units,promised_date,actual_delivery_date,shipment_status,promo_code,returned"
                ),
                "5001,2026-01-02,C1,STORE-A,north,SKU-ALPHA,electronics,3,110,120,70,22,2026-01-07,2026-01-07,delivered,WINTER,0",
                "5002,2026-01-10,C2,STORE-B,east,SKU-BETA,home,2,44,50,28,35,2026-01-15,2026-01-18,delivered,none,1",
                "5003,2026-01-18,C3,STORE-C,west,SKU-GAMMA,apparel,4,22,30,12,95,2026-01-23,2026-01-29,delivered,FLASH,0",
                "5004,2026-02-01,C1,STORE-A,north,SKU-ALPHA,electronics,2,112,120,70,18,2026-02-06,2026-02-06,delivered,WINTER,0",
                "5005,2026-02-08,C4,STORE-B,east,SKU-BETA,home,2,43,50,28,34,2026-02-13,2026-02-17,delivered,none,0",
                "5006,2026-02-16,C5,STORE-C,west,SKU-OMEGA,accessories,1,16,20,14,220,2026-02-21,2026-02-26,delivered,none,1",
                "5007,2026-02-24,C6,STORE-C,west,SKU-DELTA,electronics,1,300,320,250,5,2026-03-01,2026-03-01,delivered,none,0",
                "5008,2026-03-03,C7,STORE-A,north,SKU-ALPHA,electronics,2,114,120,70,14,2026-03-08,2026-03-08,delivered,SPRING,0",
                "5009,2026-03-10,C8,STORE-B,east,SKU-BETA,home,1,42,50,28,30,2026-03-15,2026-03-20,delivered,none,1",
                "5010,2026-03-14,C9,STORE-C,west,SKU-OMEGA,accessories,1,15,20,14,230,2026-03-19,2026-03-24,delivered,none,1",
                "5011,2026-03-18,C10,STORE-C,west,SKU-GAMMA,apparel,3,21,30,12,100,2026-03-23,,processing,FLASH,0",
                "5012,2026-03-22,C11,STORE-A,north,SKU-ALPHA,electronics,3,116,120,70,10,2026-03-27,,processing,SPRING,0",
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


def test_business_review_report_endpoints_return_expected_payloads(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_business_review_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    catalog = client.get(
        "/api/v1/business-reports/catalog",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert catalog.status_code == 200
    assert len(catalog.json()["report_index"]) >= 5

    executive = client.get(
        "/api/v1/business-reports/executive-review",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert executive.status_code == 200
    assert executive.json()["inventory_summary"]["slow_mover_count"] >= 1
    assert executive.json()["customer_summary"]["repeat_customer_count"] >= 1

    store_pack = client.get(
        "/api/v1/business-reports/store-performance",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "group_by": "store",
        },
    )
    assert store_pack.status_code == 200
    assert store_pack.json()["summary"]["grouping_dimension"] == "store_code"
    assert any(item["store_code"] == "STORE-C" for item in store_pack.json()["rows"])

    category_review = client.get(
        "/api/v1/business-reports/category-merchandising",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert category_review.status_code == 200
    assert category_review.json()["summary"]["category_count"] == 4
    assert any(
        item["movement_signal"] == "promo_led" for item in category_review.json()["categories"]
    )


def test_business_review_sku_deep_dive_surfaces_risk_flags(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_business_review_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    response = client.get(
        "/api/v1/business-reports/skus/SKU-OMEGA/deep-dive",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["priority"] in {"high", "critical"}
    assert any(
        flag in {"late_delivery_history", "high_return_exposure", "promo_dependency"}
        for flag in payload["risk_flags"]
    )
    assert payload["inventory_metrics"]["movement_class"] in {"slow_mover", "long_tail"}
