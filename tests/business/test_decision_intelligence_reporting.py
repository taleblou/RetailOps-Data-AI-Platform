# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_decision_intelligence_reporting.py
# Path:         tests/business/test_decision_intelligence_reporting.py
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
#   - Key APIs: test_decision_intelligence_catalog_includes_remaining_and_bonus_reports, test_decision_intelligence_scenario_and_board_pack_reports, test_decision_intelligence_playbook_decision_and_portfolio_reports
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _write_decision_intelligence_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "decision_intelligence_upload"
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
                "9001,SHIP-9001,2026-01-05,C-01,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,2,120,130,75,14,14,2026-01-09,2026-01-09,delivered,none,0,SUP-1,Prime Source,2,2,5,8,0.97",
                "9002,SHIP-9002,2026-01-09,C-02,STORE-B,east,UPS,SKU-B,SKU-B,home,core,3,44,50,28,30,30,2026-01-14,2026-01-18,delivered,none,0,SUP-2,Risky Vendor,3,2,11,12,0.95",
                "9003,SHIP-9003,2026-01-15,C-03,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,4,22,30,12,95,95,2026-01-21,2026-01-26,delivered,FLASH,1,SUP-2,Risky Vendor,4,3,15,20,0.94",
                "9004,SHIP-9004,2026-01-22,C-04,STORE-A,north,DHL,SKU-D,SKU-D,electronics,core,1,298,320,250,8,8,2026-01-27,2026-01-27,delivered,VIP,0,SUP-1,Prime Source,1,1,6,5,0.98",
                "9005,SHIP-9005,2026-02-02,C-05,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,1,121,130,75,12,12,2026-02-07,2026-02-08,delivered,SPRING,0,SUP-1,Prime Source,1,1,5,8,0.97",
                "9006,SHIP-9006,2026-02-05,C-06,STORE-B,east,UPS,SKU-B,SKU-B,home,core,2,45,50,28,27,27,2026-02-10,2026-02-15,delivered,none,1,SUP-2,Risky Vendor,2,1,11,12,0.95",
                "9007,SHIP-9007,2026-02-11,C-07,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,5,21,30,12,100,100,2026-02-17,2026-02-23,delivered,FLASH,1,SUP-2,Risky Vendor,5,3,15,20,0.94",
                "9008,SHIP-9008,2026-02-18,C-08,STORE-A,north,DHL,SKU-D,SKU-D,electronics,core,2,300,320,250,6,6,2026-02-23,2026-02-23,delivered,VIP,0,SUP-1,Prime Source,2,2,6,5,0.98",
                "9009,SHIP-9009,2026-03-01,C-09,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,2,122,130,75,10,10,2026-03-06,2026-03-07,delivered,SPRING,0,SUP-1,Prime Source,2,2,5,8,0.97",
                "9010,SHIP-9010,2026-03-05,C-10,STORE-B,east,UPS,SKU-B,SKU-B,home,core,1,44,50,28,22,22,2026-03-10,2026-03-15,delivered,none,0,SUP-2,Risky Vendor,1,0,11,12,0.95",
                "9011,SHIP-9011,2026-03-10,C-11,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,5,20,30,12,94,94,2026-03-15,2026-03-20,delivered,FLASH,1,SUP-2,Risky Vendor,5,3,15,20,0.94",
                "9012,SHIP-9012,2026-03-14,C-12,STORE-A,north,DHL,SKU-D,SKU-D,electronics,core,4,301,320,250,4,4,2026-03-18,,processing,VIP,0,SUP-1,Prime Source,4,2,6,5,0.98",
                "9013,SHIP-9013,2026-03-17,C-13,STORE-A,north,DHL,SKU-E,SKU-E,electronics,core,5,290,320,250,3,3,2026-03-21,,processing,VIP,0,SUP-1,Prime Source,5,2,6,5,0.98",
                "9014,SHIP-9014,2026-03-20,C-14,STORE-B,east,UPS,SKU-F,SKU-F,home,core,4,48,50,30,9,9,2026-03-24,,processing,none,0,SUP-2,Risky Vendor,4,1,12,12,0.95",
                "9015,SHIP-9015,2026-03-24,C-15,STORE-C,west,FedEx,SKU-C,SKU-C,apparel,seasonal,2,19,30,12,92,92,2026-03-29,,processing,FLASH,0,SUP-2,Risky Vendor,2,0,15,20,0.94",
                "9016,SHIP-9016,2026-03-27,C-16,STORE-A,north,DHL,SKU-A,SKU-A,electronics,premium,1,123,130,75,5,5,2026-03-31,,processing,SPRING,0,SUP-1,Prime Source,1,0,5,8,0.97",
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


def test_decision_intelligence_catalog_includes_remaining_and_bonus_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_decision_intelligence_upload(tmp_path)
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
    assert "scenario_simulation_pack" in report_names
    assert "board_style_pdf_pack" in report_names
    assert "alert_to_action_playbook" in report_names
    assert "cross_module_decision_intelligence_report" in report_names
    assert "portfolio_opportunity_matrix_report" in report_names


def test_decision_intelligence_scenario_and_board_pack_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_decision_intelligence_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    scenario = client.get(
        "/api/v1/business-reports/scenario-simulation",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert scenario.status_code == 200, scenario.text
    scenario_payload = scenario.json()
    assert scenario_payload["summary"]["scenario_count"] == 4
    assert scenario_payload["summary"]["recommended_scenario"]
    assert len(scenario_payload["focus_skus"]) >= 1

    board = client.get(
        "/api/v1/business-reports/board-pack",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert board.status_code == 200, board.text
    board_payload = board.json()
    assert board_payload["summary"]["pdf_generated"] is True
    assert board_payload["summary"]["pdf_page_count"] >= 4
    pdf_path = Path(board_payload["pdf_artifact_path"])
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_decision_intelligence_playbook_decision_and_portfolio_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_decision_intelligence_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    playbook = client.get(
        "/api/v1/business-reports/alert-to-action-playbook",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "limit": 12,
        },
    )
    assert playbook.status_code == 200, playbook.text
    playbook_payload = playbook.json()
    assert playbook_payload["summary"]["total_actions"] >= 4
    assert playbook_payload["playbook_lanes"]
    assert any(item["urgency"] in {"critical", "high"} for item in playbook_payload["actions"])

    decisions = client.get(
        "/api/v1/business-reports/cross-module-decision-intelligence",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "limit": 20,
        },
    )
    assert decisions.status_code == 200, decisions.text
    decisions_payload = decisions.json()
    assert decisions_payload["summary"]["sku_count"] >= 4
    assert decisions_payload["strategy_mix"]
    assert any(
        item["strategy"] in {"invest_to_grow", "protect_service", "fix_or_exit", "harvest_cash"}
        for item in decisions_payload["decisions"]
    )

    portfolio = client.get(
        "/api/v1/business-reports/portfolio-opportunity-matrix",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "limit": 10,
        },
    )
    assert portfolio.status_code == 200, portfolio.text
    portfolio_payload = portfolio.json()
    assert portfolio_payload["summary"]["quadrant_count"] >= 3
    assert portfolio_payload["quadrants"]
    assert portfolio_payload["focus_items"]
