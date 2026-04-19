# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_governance_reporting.py
# Path:         tests/business/test_governance_reporting.py
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
#   - Key APIs: test_governance_reporting_catalog_includes_new_reports, test_governance_reporting_anomaly_and_fulfillment_reports, test_governance_reporting_governance_and_pipeline_reports
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_governance_reporting_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "governance_reporting_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                (
                    "order_id,shipment_id,order_date,customer_id,store_code,region,carrier,sku,product_id,"
                    "category,product_group,quantity,unit_price,list_price,unit_cost,on_hand_units,"
                    "available_qty,promised_date,actual_delivery_date,shipment_status,promo_code,"
                    "returned,supplier_id,supplier_name,ordered_qty,received_qty,lead_time_days,"
                    "supplier_moq,service_level_target"
                ),
                "8001,SHIP-8001,2026-03-01,C-A,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,2,120,130,75,8,8,2026-03-06,2026-03-06,delivered,none,0,SUP-1,Prime Source,2,2,5,8,0.97",
                "8002,SHIP-8002,2026-03-05,C-B,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,1,122,130,75,7,7,2026-03-10,2026-03-12,delivered,SPRING,0,SUP-1,Prime Source,1,1,5,8,0.97",
                "8003,SHIP-8003,2026-03-08,C-C,STORE-B,east,UPS,SKU-B,SKU-B,home,core,1,45,50,28,25,25,2026-03-13,2026-03-18,delivered,none,1,SUP-2,Risky Vendor,1,1,10,12,0.95",
                "8004,SHIP-8004,2026-03-10,C-D,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,4,22,30,12,90,90,2026-03-15,2026-03-20,delivered,FLASH,1,SUP-2,Risky Vendor,4,3,14,20,0.94",
                "8005,SHIP-8005,2026-03-12,C-E,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,2,121,130,75,6,6,2026-03-17,2026-03-17,delivered,SPRING,0,SUP-1,Prime Source,2,2,5,8,0.97",
                "8006,SHIP-8006,2026-03-18,C-F,STORE-B,east,UPS,SKU-B,SKU-B,home,core,1,44,50,28,22,22,2026-03-23,2026-03-27,delivered,none,0,SUP-2,Risky Vendor,1,0,11,12,0.95",
                "8007,SHIP-8007,2026-03-20,C-G,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,5,21,30,12,95,95,2026-03-25,2026-03-30,delivered,FLASH,1,SUP-2,Risky Vendor,5,3,15,20,0.94",
                "8008,SHIP-8008,2026-03-24,C-H,STORE-A,north,DHL,SKU-D,SKU-D,electronics,core,6,300,320,250,3,3,2026-03-28,,processing,VIP,0,SUP-1,Prime Source,6,4,6,5,0.98",
                "8009,SHIP-8009,2026-03-24,C-I,STORE-A,north,DHL,SKU-E,SKU-E,electronics,core,5,290,320,250,2,2,2026-03-28,,processing,VIP,0,SUP-1,Prime Source,5,2,6,5,0.98",
                "8010,SHIP-8010,2026-03-24,C-J,STORE-B,east,UPS,SKU-F,SKU-F,home,core,4,48,50,30,10,10,2026-03-27,,processing,none,0,SUP-2,Risky Vendor,4,1,12,12,0.95",
                "8011,SHIP-8011,2026-03-25,C-K,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,1,20,30,12,94,94,2026-03-29,,processing,FLASH,0,SUP-2,Risky Vendor,1,0,15,20,0.94",
                "8012,SHIP-8012,2026-03-27,C-L,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,1,123,130,75,5,5,2026-03-31,,processing,SPRING,0,SUP-1,Prime Source,1,0,5,8,0.97",
                "8013,SHIP-8013,2026-03-28,C-M,STORE-B,east,UPS,SKU-B,SKU-B,home,core,1,43,50,28,20,20,2026-03-30,,processing,none,0,SUP-2,Risky Vendor,1,0,11,12,0.95",
                "8014,SHIP-8014,2026-03-28,C-N,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,1,19,30,12,92,92,2026-04-01,,processing,FLASH,0,SUP-2,Risky Vendor,1,0,15,20,0.94",
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


def test_governance_reporting_catalog_includes_new_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_governance_reporting_upload(tmp_path)
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
    assert "anomaly_investigation_pack" in report_names
    assert "fulfillment_control_tower_report" in report_names
    assert "ai_governance_and_trust_report" in report_names
    assert "data_quality_and_pipeline_reliability_report" in report_names


def test_governance_reporting_anomaly_and_fulfillment_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_governance_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    anomaly = client.get(
        "/api/v1/business-reports/anomaly-investigation",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert anomaly.status_code == 200
    anomaly_payload = anomaly.json()
    assert anomaly_payload["summary"]["anomaly_count"] >= 1
    assert anomaly_payload["findings"]
    assert any(
        item["severity"] in {"critical", "high", "watch"} for item in anomaly_payload["findings"]
    )

    tower = client.get(
        "/api/v1/business-reports/fulfillment-control-tower",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert tower.status_code == 200
    tower_payload = tower.json()
    assert tower_payload["summary"]["open_order_count"] >= 1
    assert tower_payload["summary"]["revenue_at_risk"] > 0
    assert tower_payload["carrier_scores"]
    assert any(
        item["priority_band"] in {"critical", "high"} for item in tower_payload["open_orders"]
    )


def test_governance_reporting_governance_and_pipeline_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_governance_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    governance = client.get(
        "/api/v1/business-reports/ai-governance-trust",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert governance.status_code == 200
    governance_payload = governance.json()
    assert governance_payload["summary"]["registry_count"] >= 3
    assert governance_payload["registries"]
    assert governance_payload["dashboard_metrics"]
    assert governance_payload["summary"]["governance_band"] in {"trusted", "watch", "restricted"}

    pipeline = client.get(
        "/api/v1/business-reports/data-quality-pipeline-reliability",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert pipeline.status_code == 200
    pipeline_payload = pipeline.json()
    assert pipeline_payload["summary"]["source_file_count"] >= 1
    assert pipeline_payload["data_checks"]
    assert pipeline_payload["pipeline_stages"]
    assert pipeline_payload["summary"]["pipeline_reliability_band"] in {
        "healthy",
        "watch",
        "fragile",
    }
