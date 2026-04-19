# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_portfolio_reporting.py
# Path:         tests/business/test_portfolio_reporting.py
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
#   - Key APIs: test_portfolio_reporting_catalog_includes_additional_reports, test_portfolio_reporting_profitability_inventory_and_cross_sell_reports, test_portfolio_reporting_customer_finance_reports, test_portfolio_reporting_seasonality_and_assortment_reports
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_portfolio_reporting_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "portfolio_reporting_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                (
                    "order_id,shipment_id,order_date,customer_id,store_code,region,carrier,sku,product_id,"
                    "category,product_group,quantity,unit_price,list_price,unit_cost,on_hand_units,"
                    "available_qty,promised_date,actual_delivery_date,shipment_status,promo_code,"
                    "returned,supplier_id,supplier_name,ordered_qty,received_qty,lead_time_days,"
                    "supplier_moq,service_level_target,total_amount,paid_amount,refund_amount,"
                    "payment_provider"
                ),
                "1001,SHIP-1001,2026-01-05,C-01,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,1,120,135,75,14,14,2026-01-09,2026-01-09,delivered,VIP,0,SUP-1,Prime Source,2,2,5,8,0.98,165,165,0,stripe",
                "1001,SHIP-1001,2026-01-05,C-01,STORE-A,north,DHL,SKU-D,SKU-D,accessories,attach,1,45,55,20,30,30,2026-01-09,2026-01-09,delivered,VIP,0,SUP-1,Prime Source,2,2,5,8,0.98,165,165,0,stripe",
                "1002,SHIP-1002,2026-01-18,C-02,STORE-B,east,UPS,SKU-B,SKU-B,home,core,2,40,50,26,34,34,2026-01-24,2026-01-28,delivered,none,0,SUP-2,Risky Vendor,3,2,12,12,0.95,80,70,0,paypal",
                "1003,SHIP-1003,2026-01-26,C-03,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,3,22,30,12,120,120,2026-01-31,2026-02-05,delivered,FLASH,1,SUP-2,Risky Vendor,5,3,15,20,0.94,66,66,18,adyen",
                "1004,SHIP-1004,2026-02-02,C-01,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,1,121,135,75,12,12,2026-02-07,2026-02-08,delivered,SPRING,0,SUP-1,Prime Source,2,2,5,8,0.98,171,171,0,stripe",
                "1004,SHIP-1004,2026-02-02,C-01,STORE-A,north,DHL,SKU-E,SKU-E,electronics,attach,1,50,60,30,16,16,2026-02-07,2026-02-08,delivered,SPRING,0,SUP-1,Prime Source,2,2,5,8,0.98,171,171,0,stripe",
                "1005,SHIP-1005,2026-02-12,C-04,STORE-B,east,UPS,SKU-B,SKU-B,home,core,1,42,50,26,28,28,2026-02-17,2026-02-22,delivered,none,1,SUP-2,Risky Vendor,2,1,12,12,0.95,42,42,6,paypal",
                "1005,SHIP-1005,2026-02-12,C-04,STORE-B,east,UPS,SKU-F,SKU-F,home,attach,1,18,25,10,40,40,2026-02-17,2026-02-22,delivered,none,0,SUP-2,Risky Vendor,2,1,12,12,0.95,42,42,0,paypal",
                "1006,SHIP-1006,2026-02-19,C-05,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,4,21,30,12,110,110,2026-02-24,2026-03-02,delivered,FLASH,1,SUP-2,Risky Vendor,6,3,15,20,0.94,84,84,20,adyen",
                "1007,SHIP-1007,2026-03-01,C-01,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,2,123,135,75,10,10,2026-03-06,2026-03-07,delivered,SPRING,0,SUP-1,Prime Source,3,2,5,8,0.98,296,296,0,stripe",
                "1007,SHIP-1007,2026-03-01,C-01,STORE-A,north,DHL,SKU-D,SKU-D,accessories,attach,1,50,55,20,24,24,2026-03-06,2026-03-07,delivered,SPRING,0,SUP-1,Prime Source,3,2,5,8,0.98,296,296,0,stripe",
                "1008,SHIP-1008,2026-03-05,C-06,STORE-A,north,DHL,SKU-G,SKU-G,electronics,core,1,260,300,250,5,5,2026-03-10,,processing,VIP,0,SUP-1,Prime Source,2,1,6,5,0.98,260,260,0,stripe",
                "1009,SHIP-1009,2026-03-10,C-07,STORE-B,east,UPS,SKU-B,SKU-B,home,core,1,41,50,26,18,18,2026-03-15,,processing,none,0,SUP-2,Risky Vendor,2,0,12,12,0.95,61,61,0,paypal",
                "1009,SHIP-1009,2026-03-10,C-07,STORE-B,east,UPS,SKU-F,SKU-F,home,attach,1,20,25,10,35,35,2026-03-15,,processing,none,0,SUP-2,Risky Vendor,2,0,12,12,0.95,61,61,0,paypal",
                "1010,SHIP-1010,2026-03-14,C-08,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,5,20,30,12,95,95,2026-03-19,,processing,FLASH,0,SUP-2,Risky Vendor,6,2,15,20,0.94,100,0,0,adyen",
                "1011,SHIP-1011,2026-03-20,C-09,STORE-A,north,DHL,SKU-H,SKU-H,electronics,core,1,85,95,88,48,48,2026-03-24,2026-03-25,delivered,VIP,0,SUP-1,Prime Source,2,2,6,5,0.98,85,90,0,stripe",
                "1012,SHIP-1012,2026-03-24,C-10,STORE-B,east,UPS,SKU-I,SKU-I,home,tail,1,14,20,12,80,80,2026-03-28,,processing,none,0,SUP-2,Risky Vendor,2,0,12,12,0.95,14,14,0,paypal",
                "1013,SHIP-1013,2026-03-26,C-04,STORE-B,east,UPS,SKU-B,SKU-B,home,core,1,43,50,26,16,16,2026-03-31,,processing,none,0,SUP-2,Risky Vendor,2,0,12,12,0.95,43,43,0,paypal",
                "1014,SHIP-1014,2026-03-27,C-11,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,1,124,135,75,8,8,2026-03-31,,processing,SPRING,0,SUP-1,Prime Source,2,0,5,8,0.98,174,174,0,stripe",
                "1014,SHIP-1014,2026-03-27,C-11,STORE-A,north,DHL,SKU-E,SKU-E,electronics,attach,1,50,60,30,14,14,2026-03-31,,processing,SPRING,0,SUP-1,Prime Source,2,0,5,8,0.98,174,174,0,stripe",
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


def test_portfolio_reporting_catalog_includes_additional_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_portfolio_reporting_upload(tmp_path)
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
    assert response.status_code == 200, response.text
    report_names = {item["report_name"] for item in response.json()["report_index"]}
    assert "profitability_margin_waterfall_report" in report_names
    assert "abc_xyz_inventory_policy_report" in report_names
    assert "basket_cross_sell_opportunity_report" in report_names
    assert "customer_churn_recovery_report" in report_names
    assert "payment_revenue_assurance_report" in report_names
    assert "seasonality_calendar_readiness_report" in report_names
    assert "assortment_rationalization_report" in report_names
    assert "customer_value_segmentation_report" in report_names


def test_portfolio_reporting_profitability_inventory_and_cross_sell_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_portfolio_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    waterfall = client.get(
        "/api/v1/business-reports/profitability-margin-waterfall",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert waterfall.status_code == 200, waterfall.text
    waterfall_payload = waterfall.json()
    assert waterfall_payload["summary"]["margin_leakage_value"] > 0
    assert len(waterfall_payload["waterfall"]) >= 4
    assert waterfall_payload["category_leakage"]

    inventory_policy = client.get(
        "/api/v1/business-reports/abc-xyz-inventory-policy",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert inventory_policy.status_code == 200, inventory_policy.text
    inventory_payload = inventory_policy.json()
    assert inventory_payload["summary"]["class_count"] >= 2
    assert inventory_payload["policy_grid"]
    assert inventory_payload["focus_skus"]

    cross_sell = client.get(
        "/api/v1/business-reports/basket-cross-sell-opportunities",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert cross_sell.status_code == 200, cross_sell.text
    cross_sell_payload = cross_sell.json()
    assert cross_sell_payload["summary"]["pair_count"] >= 2
    assert cross_sell_payload["summary"]["top_bundle"]
    assert cross_sell_payload["opportunities"]


def test_portfolio_reporting_customer_finance_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_portfolio_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    churn = client.get(
        "/api/v1/business-reports/customer-churn-recovery",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert churn.status_code == 200, churn.text
    churn_payload = churn.json()
    assert churn_payload["summary"]["recovery_value_at_risk"] > 0
    assert churn_payload["risk_bands"]
    assert churn_payload["customers"]

    payment = client.get(
        "/api/v1/business-reports/payment-revenue-assurance",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert payment.status_code == 200, payment.text
    payment_payload = payment.json()
    assert payment_payload["summary"]["mismatch_order_count"] >= 2
    assert payment_payload["provider_scorecards"]
    assert payment_payload["exceptions"]

    value_segmentation = client.get(
        "/api/v1/business-reports/customer-value-segmentation",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert value_segmentation.status_code == 200, value_segmentation.text
    value_payload = value_segmentation.json()
    assert value_payload["summary"]["customer_count"] >= 6
    assert value_payload["segment_mix"]
    assert value_payload["prioritized_customers"]


def test_portfolio_reporting_seasonality_and_assortment_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_portfolio_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    seasonality = client.get(
        "/api/v1/business-reports/seasonality-calendar-readiness",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert seasonality.status_code == 200, seasonality.text
    seasonality_payload = seasonality.json()
    assert seasonality_payload["summary"]["strong_seasonal_sku_count"] >= 1
    assert seasonality_payload["peak_months"]
    assert seasonality_payload["focus_skus"]

    assortment = client.get(
        "/api/v1/business-reports/assortment-rationalization",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert assortment.status_code == 200, assortment.text
    assortment_payload = assortment.json()
    assert assortment_payload["summary"]["sku_count"] >= 6
    assert assortment_payload["category_actions"]
    assert assortment_payload["sku_actions"]
