# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_commercial_reporting.py
# Path:         tests/business/test_commercial_reporting.py
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
#   - Key APIs: test_commercial_reporting_catalog_includes_new_reports, test_commercial_reporting_supplier_and_returns_reports, test_commercial_reporting_promotion_and_cohort_reports
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_commercial_reporting_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "commercial_reporting_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                (
                    "order_id,order_date,customer_id,store_code,region,sku,category,quantity,unit_price,list_price,"
                    "unit_cost,promised_date,actual_delivery_date,shipment_status,promo_code,returned,supplier_id,"
                    "supplier_name,ordered_qty,received_qty,lead_time_days,supplier_moq,service_level_target"
                ),
                "7001,2025-11-20,C-OLD,STORE-A,north,SKU-LEGACY,home,1,40,45,24,2025-11-25,2025-11-24,delivered,none,0,SUP-3,Stable Supply,1,1,4,6,0.96",
                "7002,2026-01-03,C-ALPHA,STORE-A,north,SKU-A1,electronics,2,110,120,70,2026-01-08,2026-01-08,delivered,BUNDLE,0,SUP-1,Prime Source,2,2,6,8,0.97",
                "7003,2026-01-18,C-ALPHA,STORE-A,north,SKU-A1,electronics,1,112,120,70,2026-01-23,2026-01-23,delivered,BUNDLE,0,SUP-1,Prime Source,1,1,5,8,0.97",
                "7004,2026-01-05,C-BETA,STORE-B,east,SKU-H1,home,1,48,50,30,2026-01-10,2026-01-14,delivered,none,1,SUP-2,Risky Vendor,1,1,9,10,0.95",
                "7005,2026-01-27,C-GAMMA,STORE-C,west,SKU-F1,apparel,3,20,30,12,2026-02-01,2026-02-06,delivered,FLASH,1,SUP-2,Risky Vendor,3,2,12,20,0.94",
                "7006,2026-02-02,C-DELTA,STORE-A,north,SKU-A2,electronics,2,108,118,68,2026-02-07,2026-02-07,delivered,BUNDLE,0,SUP-1,Prime Source,2,2,5,8,0.97",
                "7007,2026-02-09,C-EPS,STORE-B,east,SKU-H2,home,2,46,50,30,2026-02-14,2026-02-18,delivered,none,0,SUP-2,Risky Vendor,2,1,11,12,0.95",
                "7008,2026-02-15,C-ZETA,STORE-C,west,SKU-F1,apparel,2,19,30,12,2026-02-20,2026-02-25,delivered,FLASH,1,SUP-2,Risky Vendor,2,1,13,20,0.94",
                "7009,2026-02-21,C-ETA,STORE-A,north,SKU-A3,electronics,3,104,118,68,2026-02-26,2026-02-26,delivered,SPRING,0,SUP-1,Prime Source,3,3,5,8,0.97",
                "7010,2026-02-28,C-THETA,STORE-B,east,SKU-H3,home,1,44,50,30,2026-03-05,2026-03-09,delivered,none,0,SUP-2,Risky Vendor,1,0,12,12,0.95",
                "7011,2026-03-04,C-ALPHA,STORE-A,north,SKU-A1,electronics,2,114,120,70,2026-03-09,2026-03-09,delivered,BUNDLE,0,SUP-1,Prime Source,2,2,5,8,0.97",
                "7012,2026-03-08,C-IOTA,STORE-C,west,SKU-F2,apparel,2,18,30,12,2026-03-13,2026-03-18,delivered,FLASH,1,SUP-2,Risky Vendor,2,1,14,20,0.94",
                "7013,2026-03-12,C-KAPPA,STORE-A,north,SKU-A2,electronics,1,109,118,68,2026-03-17,2026-03-17,delivered,SPRING,0,SUP-1,Prime Source,1,1,5,8,0.97",
                "7014,2026-03-14,C-LAMBDA,STORE-B,east,SKU-H1,home,1,45,50,30,2026-03-19,2026-03-23,delivered,none,1,SUP-2,Risky Vendor,1,1,10,10,0.95",
                "7015,2026-03-18,C-MU,STORE-C,west,SKU-F3,apparel,1,17,28,11,2026-03-23,,processing,FLASH,0,SUP-2,Risky Vendor,1,0,15,20,0.94",
                "7016,2026-03-20,C-NI,STORE-A,north,SKU-A3,electronics,2,105,118,68,2026-03-25,,processing,SPRING,0,SUP-1,Prime Source,2,1,6,8,0.97",
                "7017,2026-03-22,C-OMICRON,STORE-B,east,SKU-H2,home,1,47,50,30,2026-03-27,,processing,none,0,SUP-2,Risky Vendor,1,0,12,12,0.95",
                "7018,2026-03-24,C-PI,STORE-C,west,SKU-F2,apparel,2,18,30,12,2026-03-29,,processing,FLASH,0,SUP-2,Risky Vendor,2,0,15,20,0.94",
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


def test_commercial_reporting_catalog_includes_new_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_commercial_reporting_upload(tmp_path)
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
    assert "supplier_and_procurement_intelligence_pack" in report_names
    assert "returns_profit_leakage_report" in report_names
    assert "promotion_and_pricing_effectiveness_analysis" in report_names
    assert "customer_cohort_and_retention_review" in report_names


def test_commercial_reporting_supplier_and_returns_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_commercial_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    supplier = client.get(
        "/api/v1/business-reports/supplier-procurement-pack",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert supplier.status_code == 200
    supplier_payload = supplier.json()
    assert supplier_payload["summary"]["supplier_count"] >= 2
    assert supplier_payload["summary"]["spend_at_risk"] > 0
    assert any(item["procurement_risk_band"] == "high" for item in supplier_payload["rows"])

    returns_report = client.get(
        "/api/v1/business-reports/returns-profit-leakage",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert returns_report.status_code == 200
    leakage_payload = returns_report.json()
    assert leakage_payload["summary"]["total_actual_return_cost"] > 0
    assert leakage_payload["summary"]["high_loss_category_count"] >= 1
    assert any(
        item["component"] == "delay_linked_return_cost" for item in leakage_payload["waterfall"]
    )


def test_commercial_reporting_promotion_and_cohort_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_commercial_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    promotion = client.get(
        "/api/v1/business-reports/promotion-pricing-effectiveness",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert promotion.status_code == 200
    promotion_payload = promotion.json()
    assert promotion_payload["summary"]["promo_code_count"] >= 2
    assert promotion_payload["summary"]["discount_value"] > 0
    assert any(
        item["effectiveness_band"] in {"efficient", "dilutive"}
        for item in promotion_payload["promotions"]
    )

    cohort = client.get(
        "/api/v1/business-reports/customer-cohort-retention",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert cohort.status_code == 200
    cohort_payload = cohort.json()
    assert cohort_payload["summary"]["cohort_count"] >= 3
    assert cohort_payload["summary"]["high_risk_customer_count"] >= 1
    assert cohort_payload["focus_customers"]
    assert any(
        item["cohort_health_band"] in {"healthy", "watch", "fragile"}
        for item in cohort_payload["cohorts"]
    )
