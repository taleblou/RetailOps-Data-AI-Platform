# Project:      RetailOps Data & AI Platform
# Module:       tests.shipment_risk
# File:         test_shipment_risk.py
# Path:         tests/shipment_risk/test_shipment_risk.py
#
# Summary:      Contains automated tests for the shipment risk workflows and behaviors.
# Purpose:      Validates shipment risk behavior and protects the repository against regressions.
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
#   - Key APIs: test_run_shipment_risk_analysis_builds_open_order_artifact, test_get_open_order_prediction_reads_saved_artifact, test_shipment_risk_router_returns_open_orders_and_prediction
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.shipment_risk.service import get_open_order_prediction, run_shipment_risk_analysis


def _write_shipment_risk_upload(tmp_path: Path) -> tuple[str, Path, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "shipment_risk_upload"
    csv_path = uploads_dir / f"{upload_id}_shipments.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Shipment ID,Order ID,Store Code,Carrier,Shipment Status,Promised Date,"
                "Actual Delivery Date,Order Date,Inventory Lag Days",
                "SHP-001,ORD-001,HEL-01,DHL,delivered,2026-03-01,2026-03-01,2026-02-26,0",
                "SHP-002,ORD-002,HEL-01,DHL,delayed,2026-03-02,2026-03-04,2026-02-27,1",
                "SHP-003,ORD-003,HEL-01,UPS,delivered,2026-03-03,2026-03-03,2026-02-28,0",
                "SHP-004,ORD-004,HEL-02,DHL,processing,2026-03-05,,2026-03-01,2",
                "SHP-005,ORD-005,HEL-02,UPS,in_transit,2026-03-04,,2026-03-02,0",
                "SHP-006,ORD-006,HEL-02,DHL,delayed,2026-03-04,2026-03-07,2026-03-01,3",
                "SHP-007,ORD-007,HEL-03,FedEx,processing,2026-03-06,,2026-03-03,4",
            ]
        ),
        encoding="utf-8",
    )
    metadata_path = uploads_dir / f"{upload_id}.json"
    metadata_path.write_text(
        json.dumps(
            {
                "upload_id": upload_id,
                "filename": "shipments.csv",
                "stored_path": str(csv_path),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return upload_id, uploads_dir, artifact_dir


def test_run_shipment_risk_analysis_builds_open_order_artifact(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_shipment_risk_upload(tmp_path)

    artifact = run_shipment_risk_analysis(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    assert artifact.summary.open_orders == 3
    assert artifact.summary.high_risk_orders >= 1
    assert artifact.evaluation_metrics.roc_auc >= 0.0
    assert artifact.evaluation_metrics.pr_auc >= 0.0
    assert artifact.open_orders[0].probability >= artifact.open_orders[-1].probability
    assert Path(artifact.artifact_path).exists()


def test_get_open_order_prediction_reads_saved_artifact(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_shipment_risk_upload(tmp_path)
    run_shipment_risk_analysis(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    prediction = get_open_order_prediction(
        upload_id=upload_id,
        shipment_id="SHP-004",
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    assert prediction["shipment_id"] == "SHP-004"
    assert prediction["risk_band"] in {"medium", "high", "critical", "low"}
    assert prediction["recommended_action"]


def test_shipment_risk_router_returns_open_orders_and_prediction(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_shipment_risk_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    open_orders_response = client.get(
        "/api/v1/shipment-risk/open-orders",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert open_orders_response.status_code == 200, open_orders_response.text
    open_orders_payload = open_orders_response.json()
    assert open_orders_payload["summary"]["open_orders"] == 3
    assert len(open_orders_payload["open_orders"]) == 3

    detail_response = client.get(
        "/api/v1/shipment-risk/open-orders/SHP-005",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
        },
    )
    assert detail_response.status_code == 200, detail_response.text
    detail_payload = detail_response.json()
    assert detail_payload["shipment_id"] == "SHP-005"

    predict_response = client.post(
        "/api/v1/predict/shipment-delay",
        json={
            "shipment_id": "manual-1",
            "order_id": "manual-order-1",
            "store_code": "HEL-01",
            "carrier": "DHL",
            "shipment_status": "processing",
            "promised_date": "2026-03-06",
            "order_date": "2026-03-01",
            "inventory_lag_days": 2,
            "warehouse_backlog_7d": 5,
            "carrier_delay_rate_30d": 0.4,
            "region_delay_trend_30d": 0.3,
            "reference_date": "2026-03-07",
        },
    )
    assert predict_response.status_code == 200, predict_response.text
    predict_payload = predict_response.json()
    assert predict_payload["probability"] > 0.0
    assert predict_payload["manual_review_required"] is True
