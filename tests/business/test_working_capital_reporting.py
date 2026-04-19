# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_working_capital_reporting.py
# Path:         tests/business/test_working_capital_reporting.py
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
#   - Key APIs: test_working_capital_catalog_includes_new_reports, test_working_capital_inventory_and_root_cause_reports, test_working_capital_forecast_quality_and_replenishment_reports
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_working_capital_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "working_capital_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                (
                    "order_id,order_date,customer_id,store_code,region,sku,category,product_group,quantity,"
                    "unit_price,list_price,unit_cost,on_hand_units,available_qty,inbound_qty,promised_date,"
                    "actual_delivery_date,shipment_status,promo_code,returned,lead_time_days,supplier_moq,"
                    "service_level_target"
                ),
                "6001,2026-01-05,C1,STORE-A,north,SKU-ALPHA,electronics,premium,5,100,120,60,8,8,0,2026-01-10,2026-01-10,delivered,WINTER,0,10,10,0.95",
                "6002,2026-01-12,C2,STORE-A,north,SKU-ALPHA,electronics,premium,4,102,120,60,8,8,0,2026-01-17,2026-01-18,delivered,WINTER,0,10,10,0.95",
                "6003,2026-01-20,C3,STORE-B,east,SKU-BETA,home,core,3,45,50,28,35,35,0,2026-01-25,2026-01-30,delivered,none,1,7,12,0.96",
                "6004,2026-01-27,C4,STORE-B,east,SKU-GAMMA,apparel,seasonal,6,24,30,12,90,90,0,2026-02-02,2026-02-02,delivered,FLASH,0,14,20,0.97",
                "6005,2026-02-03,C5,STORE-A,north,SKU-ALPHA,electronics,premium,5,99,120,60,7,7,0,2026-02-08,2026-02-08,delivered,SPRING,0,10,10,0.95",
                "6006,2026-02-07,C6,STORE-B,east,SKU-BETA,home,core,2,44,50,28,34,34,0,2026-02-13,2026-02-17,delivered,none,0,7,12,0.96",
                "6007,2026-02-12,C7,STORE-C,west,SKU-DELTA,electronics,core,2,290,320,250,3,3,0,2026-02-18,2026-02-25,delivered,none,0,8,5,0.98",
                "6008,2026-02-18,C8,STORE-C,west,SKU-DELTA,electronics,core,1,288,320,250,2,2,0,2026-02-22,2026-02-24,delivered,none,0,8,5,0.98",
                "6009,2026-02-20,C9,STORE-A,north,SKU-OMEGA,accessories,long_tail,1,16,20,14,220,220,0,2026-02-25,2026-02-28,delivered,none,1,5,25,0.93",
                "6010,2026-02-24,C10,STORE-B,east,SKU-GAMMA,apparel,seasonal,7,22,30,12,95,95,0,2026-03-01,2026-03-01,delivered,FLASH,0,14,20,0.97",
                "6011,2026-03-01,C11,STORE-A,north,SKU-ALPHA,electronics,premium,6,105,120,60,4,4,0,2026-03-06,2026-03-06,delivered,SPRING,0,10,10,0.95",
                "6012,2026-03-04,C12,STORE-B,east,SKU-BETA,home,core,2,40,50,28,28,28,0,2026-03-09,2026-03-14,delivered,none,1,7,12,0.96",
                "6013,2026-03-07,C13,STORE-C,west,SKU-DELTA,electronics,core,2,300,320,250,1,1,0,2026-03-12,,processing,none,0,8,5,0.98",
                "6014,2026-03-10,C14,STORE-A,north,SKU-OMEGA,accessories,long_tail,1,15,20,14,240,240,0,2026-03-14,2026-03-18,delivered,none,1,5,25,0.93",
                "6015,2026-03-15,C15,STORE-B,east,SKU-GAMMA,apparel,seasonal,5,21,30,12,100,100,0,2026-03-20,,processing,FLASH,0,14,20,0.97",
                "6016,2026-03-18,C16,STORE-C,west,SKU-DELTA,electronics,core,1,305,320,250,1,1,3,2026-03-23,,processing,none,0,8,5,0.98",
                "6017,2026-03-22,C17,STORE-A,north,SKU-ALPHA,electronics,premium,4,108,120,60,3,3,0,2026-03-27,,processing,SPRING,0,10,10,0.95",
                "6018,2026-03-26,C18,STORE-B,east,SKU-BETA,home,core,2,39,50,28,25,25,0,2026-03-30,,processing,none,0,7,12,0.96",
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


def test_working_capital_catalog_includes_new_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_working_capital_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    response = client.get(
        "/api/v1/business-reports/catalog",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert response.status_code == 200
    report_names = {item["report_name"] for item in response.json()["report_index"]}
    assert "inventory_investment_and_working_capital_report" in report_names
    assert "revenue_root_cause_analysis_report" in report_names
    assert "forecast_quality_and_reliability_report" in report_names
    assert "replenishment_decision_review_pack" in report_names


def test_working_capital_inventory_and_root_cause_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_working_capital_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    inventory = client.get(
        "/api/v1/business-reports/inventory-investment",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert inventory.status_code == 200
    inventory_payload = inventory.json()
    assert inventory_payload["summary"]["total_inventory_value"] > 0
    assert inventory_payload["summary"]["liquidation_candidate_count"] >= 1
    assert inventory_payload["rows"][0]["recommended_action"]

    root_cause = client.get(
        "/api/v1/business-reports/revenue-root-cause",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "window_days": 30,
        },
    )
    assert root_cause.status_code == 200
    root_payload = root_cause.json()
    assert root_payload["summary"]["window_days"] == 30
    assert len(root_payload["contributions"]) >= 5
    assert any(item["factor"] == "volume_effect" for item in root_payload["contributions"])


def test_working_capital_forecast_quality_and_replenishment_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_working_capital_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    forecast_quality = client.get(
        "/api/v1/business-reports/forecast-quality",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert forecast_quality.status_code == 200
    forecast_payload = forecast_quality.json()
    assert forecast_payload["summary"]["product_count"] >= 4
    assert forecast_payload["summary"]["dominant_model"]
    assert any(
        item["reliability_band"] in {"watch", "low_confidence"}
        for item in forecast_payload["products"]
    )

    replenishment = client.get(
        "/api/v1/business-reports/replenishment-review",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert replenishment.status_code == 200
    replenishment_payload = replenishment.json()
    assert replenishment_payload["summary"]["total_recommendations"] >= 4
    assert replenishment_payload["summary"]["lead_time_pressure_count"] >= 1
    assert any(item["flags"] for item in replenishment_payload["rows"])
