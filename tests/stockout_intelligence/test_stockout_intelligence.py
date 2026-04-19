# Project:      RetailOps Data & AI Platform
# Module:       tests.stockout_intelligence
# File:         test_stockout_intelligence.py
# Path:         tests/stockout_intelligence/test_stockout_intelligence.py
#
# Summary:      Contains automated tests for the stockout intelligence workflows and behaviors.
# Purpose:      Validates stockout intelligence behavior and protects the repository against regressions.
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
#   - Key APIs: test_run_stockout_stockout_builds_ranked_predictions, test_get_stockout_sku_prediction_reads_saved_artifact, test_stockout_router_returns_stockout_list_and_detail
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.stockout_intelligence.service import (
    get_stockout_sku_prediction,
    run_stockout_risk_analysis,
)


def _write_stockout_upload(tmp_path: Path) -> tuple[str, Path, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "stockout_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_date,sku,quantity,unit_price,store_code,available_qty,in_transit_qty,lead_time_days",
                "2026-03-01,SKU-001,3,12.0,HEL-01,45,12,7",
                "2026-03-02,SKU-001,3,12.0,HEL-01,44,12,7",
                "2026-03-03,SKU-001,4,12.0,HEL-01,43,12,7",
                "2026-03-04,SKU-001,3,12.0,HEL-01,42,12,7",
                "2026-03-05,SKU-001,4,12.0,HEL-01,41,12,7",
                "2026-03-06,SKU-001,3,12.0,HEL-01,40,12,7",
                "2026-03-07,SKU-001,4,12.0,HEL-01,39,12,7",
                "2026-03-01,SKU-002,6,8.0,HEL-01,18,4,6",
                "2026-03-02,SKU-002,7,8.0,HEL-01,17,4,6",
                "2026-03-03,SKU-002,6,8.0,HEL-01,16,4,6",
                "2026-03-04,SKU-002,8,8.0,HEL-01,15,4,6",
                "2026-03-05,SKU-002,7,8.0,HEL-01,14,4,6",
                "2026-03-06,SKU-002,8,8.0,HEL-01,13,4,6",
                "2026-03-07,SKU-002,9,8.0,HEL-01,12,4,6",
                "2026-03-01,SKU-003,9,20.0,HEL-02,8,0,7",
                "2026-03-02,SKU-003,10,20.0,HEL-02,7,0,7",
                "2026-03-03,SKU-003,11,20.0,HEL-02,6,0,7",
                "2026-03-04,SKU-003,12,20.0,HEL-02,5,0,7",
                "2026-03-05,SKU-003,12,20.0,HEL-02,4,0,7",
                "2026-03-06,SKU-003,13,20.0,HEL-02,3,0,7",
                "2026-03-07,SKU-003,14,20.0,HEL-02,2,0,7",
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
    return upload_id, uploads_dir, artifact_dir


def test_run_stockout_stockout_builds_ranked_predictions(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_stockout_upload(tmp_path)

    artifact = run_stockout_risk_analysis(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    assert artifact.summary.total_skus == 3
    assert artifact.summary.at_risk_skus >= 2
    assert artifact.skus[0].reorder_urgency_score >= artifact.skus[-1].reorder_urgency_score
    assert artifact.skus[0].risk_band in {"critical", "high"}
    assert Path(artifact.artifact_path).exists()


def test_get_stockout_sku_prediction_reads_saved_artifact(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_stockout_upload(tmp_path)
    run_stockout_risk_analysis(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    prediction = get_stockout_sku_prediction(
        upload_id=upload_id,
        sku="SKU-003",
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    assert prediction["sku"] == "SKU-003"
    assert prediction["stockout_probability"] >= 0.6
    assert prediction["recommended_action"]


def test_stockout_router_returns_stockout_list_and_detail(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_stockout_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    list_response = client.get(
        "/api/v1/stockout-risk/skus",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert list_response.status_code == 200, list_response.text
    list_payload = list_response.json()
    assert list_payload["summary"]["total_skus"] == 3
    assert len(list_payload["skus"]) == 3

    detail_response = client.get(
        "/api/v1/stockout-risk/SKU-003",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
        },
    )
    assert detail_response.status_code == 200, detail_response.text
    detail_payload = detail_response.json()
    assert detail_payload["sku"] == "SKU-003"
    assert detail_payload["risk_band"] in {"medium", "high", "critical"}
