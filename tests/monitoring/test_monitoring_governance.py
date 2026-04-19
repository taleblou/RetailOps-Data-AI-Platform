# Project:      RetailOps Data & AI Platform
# Module:       tests.monitoring
# File:         test_monitoring_governance.py
# Path:         tests/monitoring/test_monitoring_governance.py
#
# Summary:      Contains automated tests for the monitoring workflows and behaviors.
# Purpose:      Validates monitoring behavior and protects the repository against regressions.
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
#   - Key APIs: test_run_monitoring_builds_governance_artifact, test_monitoring_manual_override_logging_keeps_feedback, test_monitoring_router_returns_monitoring_summary_and_override_log
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from core.monitoring.service import (
    get_or_create_monitoring_artifact,
    get_override_summary,
    log_manual_override,
)
from core.serving.service import get_or_create_batch_serving_artifact
from modules.forecasting.service import get_or_create_batch_forecast_artifact
from modules.ml_registry.service import run_model_registry
from modules.shipment_risk.service import get_or_create_shipment_risk_artifact
from modules.stockout_intelligence.service import get_or_create_stockout_artifact


def _write_monitoring_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "monitoring_upload"

    orders_path = uploads_dir / f"{upload_id}_orders.csv"
    orders_path.write_text(
        "\n".join(
            [
                "order_date,sku,product_id,quantity,unit_price,store_code,available_qty,in_transit_qty,lead_time_days",
                "2026-03-01,SKU-001,PROD-001,3,12.0,HEL-01,45,12,7",
                "2026-03-02,SKU-001,PROD-001,3,12.0,HEL-01,44,12,7",
                "2026-03-03,SKU-001,PROD-001,4,12.0,HEL-01,43,12,7",
                "2026-03-04,SKU-001,PROD-001,3,12.0,HEL-01,42,12,7",
                "2026-03-05,SKU-001,PROD-001,4,12.0,HEL-01,41,12,7",
                "2026-03-06,SKU-001,PROD-001,3,12.0,HEL-01,40,12,7",
                "2026-03-07,SKU-001,PROD-001,4,12.0,HEL-01,39,12,7",
                "2026-03-01,SKU-002,PROD-002,6,8.0,HEL-01,18,4,6",
                "2026-03-02,SKU-002,PROD-002,7,8.0,HEL-01,17,4,6",
                "2026-03-03,SKU-002,PROD-002,6,8.0,HEL-01,16,4,6",
                "2026-03-04,SKU-002,PROD-002,8,8.0,HEL-01,15,4,6",
                "2026-03-05,SKU-002,PROD-002,7,8.0,HEL-01,14,4,6",
                "2026-03-06,SKU-002,PROD-002,8,8.0,HEL-01,13,4,6",
                "2026-03-07,SKU-002,PROD-002,9,8.0,HEL-01,12,4,6",
                "2026-03-01,SKU-003,PROD-003,9,20.0,HEL-02,8,0,7",
                "2026-03-02,SKU-003,PROD-003,10,20.0,HEL-02,7,0,7",
                "2026-03-03,SKU-003,PROD-003,11,20.0,HEL-02,6,0,7",
                "2026-03-04,SKU-003,PROD-003,12,20.0,HEL-02,5,0,7",
                "2026-03-05,SKU-003,PROD-003,12,20.0,HEL-02,4,0,7",
                "2026-03-06,SKU-003,PROD-003,13,20.0,HEL-02,3,0,7",
                "2026-03-07,SKU-003,PROD-003,14,20.0,HEL-02,2,0,7",
            ]
        ),
        encoding="utf-8",
    )
    shipments_path = uploads_dir / f"{upload_id}_shipments.csv"
    shipments_path.write_text(
        "\n".join(
            [
                "shipment_id,order_id,store_code,carrier,shipment_status,promised_date,actual_delivery_date,order_date,inventory_lag_days",
                "SHP-001,ORD-001,HEL-01,DHL,processing,2026-03-05,,2026-03-01,1",
                "SHP-002,ORD-002,HEL-01,DHL,processing,2026-03-05,,2026-03-01,2",
                "SHP-003,ORD-003,HEL-02,Posti,in_transit,2026-03-06,,2026-03-02,5",
                "SHP-004,ORD-004,HEL-02,Posti,delayed,2026-03-04,,2026-03-01,8",
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
                "stored_path": str(orders_path),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return upload_id, uploads_dir


def _prepare_monitoring_artifacts(tmp_path: Path) -> dict[str, Path | str]:
    upload_id, uploads_dir = _write_monitoring_upload(tmp_path)
    forecast_artifact_dir = tmp_path / "artifacts" / "forecasts"
    shipment_artifact_dir = tmp_path / "artifacts" / "shipment_risk"
    stockout_artifact_dir = tmp_path / "artifacts" / "stockout_risk"
    serving_artifact_dir = tmp_path / "artifacts" / "serving"
    registry_artifact_dir = tmp_path / "artifacts" / "model_registry"
    monitoring_artifact_dir = tmp_path / "artifacts" / "monitoring"
    override_dir = monitoring_artifact_dir / "overrides"

    get_or_create_batch_forecast_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=forecast_artifact_dir,
        refresh=True,
    )
    get_or_create_shipment_risk_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=shipment_artifact_dir,
        refresh=True,
    )
    get_or_create_stockout_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=stockout_artifact_dir,
        refresh=True,
    )
    get_or_create_batch_serving_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        shipment_artifact_dir=shipment_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=serving_artifact_dir,
        refresh=True,
    )
    run_model_registry(
        artifact_dir=registry_artifact_dir,
        refresh=True,
    )
    return {
        "upload_id": upload_id,
        "uploads_dir": uploads_dir,
        "forecast_artifact_dir": forecast_artifact_dir,
        "shipment_artifact_dir": shipment_artifact_dir,
        "stockout_artifact_dir": stockout_artifact_dir,
        "serving_artifact_dir": serving_artifact_dir,
        "registry_artifact_dir": registry_artifact_dir,
        "monitoring_artifact_dir": monitoring_artifact_dir,
        "override_dir": override_dir,
    }


def test_run_monitoring_builds_governance_artifact(tmp_path: Path) -> None:
    paths = _prepare_monitoring_artifacts(tmp_path)
    artifact = get_or_create_monitoring_artifact(
        upload_id=str(paths["upload_id"]),
        uploads_dir=Path(paths["uploads_dir"]),
        forecast_artifact_dir=Path(paths["forecast_artifact_dir"]),
        shipment_artifact_dir=Path(paths["shipment_artifact_dir"]),
        stockout_artifact_dir=Path(paths["stockout_artifact_dir"]),
        serving_artifact_dir=Path(paths["serving_artifact_dir"]),
        registry_artifact_dir=Path(paths["registry_artifact_dir"]),
        artifact_dir=Path(paths["monitoring_artifact_dir"]),
        override_dir=Path(paths["override_dir"]),
        refresh=True,
    )

    assert artifact["summary"]["source_row_count"] == 25
    assert len(artifact["data_checks"]) == 4
    assert len(artifact["ml_checks"]) == 4
    assert Path(artifact["artifact_path"]).exists()


def test_monitoring_manual_override_logging_keeps_feedback(tmp_path: Path) -> None:
    paths = _prepare_monitoring_artifacts(tmp_path)
    entry = log_manual_override(
        upload_id=str(paths["upload_id"]),
        prediction_type="reorder",
        entity_id="SKU-003",
        original_decision={"recommendation": "reorder_now", "quantity": 30},
        override_decision={"recommendation": "hold", "quantity": 0},
        reason="Buyer wants to wait for a supplier campaign.",
        feedback_label="approved_hold",
        override_dir=Path(paths["override_dir"]),
        user_id="planner-1",
    )
    summary = get_override_summary(
        upload_id=str(paths["upload_id"]),
        override_dir=Path(paths["override_dir"]),
    )

    assert entry["retraining_feedback_kept"] is True
    assert summary["total_overrides"] == 1
    assert summary["by_prediction_type"]["reorder"] == 1


def test_monitoring_router_returns_monitoring_summary_and_override_log(tmp_path: Path) -> None:
    paths = _prepare_monitoring_artifacts(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    monitoring_response = client.get(
        "/api/v1/monitoring/summary",
        params={
            "upload_id": str(paths["upload_id"]),
            "uploads_dir": str(paths["uploads_dir"]),
            "forecast_artifact_dir": str(paths["forecast_artifact_dir"]),
            "shipment_artifact_dir": str(paths["shipment_artifact_dir"]),
            "stockout_artifact_dir": str(paths["stockout_artifact_dir"]),
            "serving_artifact_dir": str(paths["serving_artifact_dir"]),
            "registry_artifact_dir": str(paths["registry_artifact_dir"]),
            "artifact_dir": str(paths["monitoring_artifact_dir"]),
            "override_dir": str(paths["override_dir"]),
            "refresh": "true",
        },
    )
    assert monitoring_response.status_code == 200, monitoring_response.text
    monitoring_payload = monitoring_response.json()
    assert monitoring_payload["summary"]["model_usage_total"] > 0
    assert len(monitoring_payload["dashboard_metrics"]) == 4

    override_response = client.post(
        "/api/v1/monitoring/overrides",
        json={
            "upload_id": str(paths["upload_id"]),
            "prediction_type": "shipment_delay",
            "entity_id": "SHP-004",
            "original_decision": {"recommended_action": "expedite_carrier"},
            "override_decision": {"recommended_action": "manual_call"},
            "reason": "Operations team prefers direct escalation for this carrier.",
            "feedback_label": "manual_escalation",
            "user_id": "ops-lead",
            "override_dir": str(paths["override_dir"]),
        },
    )
    assert override_response.status_code == 200, override_response.text
    override_payload = override_response.json()
    assert override_payload["prediction_type"] == "shipment_delay"

    override_summary_response = client.get(
        "/api/v1/monitoring/overrides",
        params={
            "upload_id": str(paths["upload_id"]),
            "override_dir": str(paths["override_dir"]),
        },
    )
    assert override_summary_response.status_code == 200, override_summary_response.text
    override_summary_payload = override_summary_response.json()
    assert override_summary_payload["total_overrides"] == 1
