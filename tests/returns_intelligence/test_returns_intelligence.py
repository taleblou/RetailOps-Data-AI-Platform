# Project:      RetailOps Data & AI Platform
# Module:       tests.returns_intelligence
# File:         test_returns_intelligence.py
# Path:         tests/returns_intelligence/test_returns_intelligence.py
#
# Summary:      Contains automated tests for the returns intelligence workflows and behaviors.
# Purpose:      Validates returns intelligence behavior and protects the repository against regressions.
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
#   - Key APIs: test_run_returns_returns_builds_scores_and_risky_products, test_get_return_risk_order_reads_saved_artifact, test_returns_router_returns_orders_products_and_detail
#   - Dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.returns_intelligence.service import (
    get_return_risk_order,
    run_returns_intelligence,
)


def _write_returns_upload(tmp_path: Path) -> tuple[str, Path, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "returns_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,order_date,customer_id,sku,quantity,unit_price,store_code,category,discount_rate,shipment_delay_days,returned",
                "ORD-001,2026-01-10,C-001,SKU-RTN-1,1,120,HEL-01,fashion,0.35,4,true",
                "ORD-002,2026-01-18,C-001,SKU-RTN-1,1,118,HEL-01,fashion,0.30,3,true",
                "ORD-003,2026-01-24,C-002,SKU-STABLE-1,1,40,HEL-01,home,0.00,0,false",
                "ORD-004,2026-02-02,C-003,SKU-RTN-2,2,95,HEL-02,beauty,0.20,2,true",
                "ORD-005,2026-02-15,C-001,SKU-RTN-1,1,125,HEL-01,fashion,0.25,5,false",
                "ORD-006,2026-02-16,C-002,SKU-STABLE-1,1,42,HEL-01,home,0.00,0,false",
                "ORD-007,2026-02-20,C-004,SKU-RTN-3,3,70,HEL-02,fashion,0.15,1,true",
                "ORD-008,2026-03-01,C-001,SKU-RTN-1,1,130,HEL-01,fashion,0.28,6,false",
                "ORD-009,2026-03-03,C-004,SKU-RTN-3,2,72,HEL-02,fashion,0.12,2,false",
                "ORD-010,2026-03-05,C-005,SKU-STABLE-2,1,25,HEL-03,electronics,0.00,0,false",
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


def test_run_returns_returns_builds_scores_and_risky_products(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_returns_upload(tmp_path)

    artifact = run_returns_intelligence(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    assert artifact.summary.total_orders == 10
    assert artifact.summary.high_risk_orders >= 2
    assert artifact.summary.risky_products_count >= 1
    assert artifact.scores[0].return_probability >= artifact.scores[-1].return_probability
    assert (
        artifact.risky_products[0].total_expected_return_cost
        >= artifact.risky_products[-1].total_expected_return_cost
    )
    assert Path(artifact.artifact_path).exists()


def test_get_return_risk_order_reads_saved_artifact(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_returns_upload(tmp_path)
    run_returns_intelligence(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    prediction = get_return_risk_order(
        upload_id=upload_id,
        order_id="ORD-008",
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    assert prediction["order_id"] == "ORD-008"
    assert prediction["risk_band"] in {"medium", "high", "critical"}
    assert prediction["expected_return_cost"] > 0.0


def test_returns_router_returns_orders_products_and_detail(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_returns_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    orders_response = client.get(
        "/api/v1/returns-risk/orders",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert orders_response.status_code == 200, orders_response.text
    orders_payload = orders_response.json()
    assert orders_payload["summary"]["total_orders"] == 10
    assert len(orders_payload["scores"]) == 10

    products_response = client.get(
        "/api/v1/returns-risk/products",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "min_probability": 0.2,
        },
    )
    assert products_response.status_code == 200, products_response.text
    products_payload = products_response.json()
    assert len(products_payload["risky_products"]) >= 1

    detail_response = client.get(
        "/api/v1/returns-risk/orders/ORD-008",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
        },
    )
    assert detail_response.status_code == 200, detail_response.text
    detail_payload = detail_response.json()
    assert detail_payload["order_id"] == "ORD-008"
    assert detail_payload["sku"] == "SKU-RTN-1"
