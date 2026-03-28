from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.reorder_engine.service import (
    get_reorder_recommendation,
    run_phase13_reorder_engine,
)


def _write_phase13_upload(tmp_path: Path) -> tuple[str, Path, Path, Path, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    forecast_artifact_dir = tmp_path / "forecast_artifacts"
    forecast_artifact_dir.mkdir(parents=True, exist_ok=True)
    stockout_artifact_dir = tmp_path / "stockout_artifacts"
    stockout_artifact_dir.mkdir(parents=True, exist_ok=True)
    reorder_artifact_dir = tmp_path / "reorder_artifacts"
    reorder_artifact_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "phase13_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_date,sku,quantity,unit_price,category,store_code,available_qty,in_transit_qty,lead_time_days,supplier_moq,service_level_target",
                "2026-03-01,SKU-001,4,10.0,beverages,HEL-01,44,8,7,12,0.95",
                "2026-03-02,SKU-001,5,10.0,beverages,HEL-01,42,8,7,12,0.95",
                "2026-03-03,SKU-001,6,10.0,beverages,HEL-01,40,8,7,12,0.95",
                "2026-03-04,SKU-001,5,10.0,beverages,HEL-01,38,8,7,12,0.95",
                "2026-03-05,SKU-001,7,10.0,beverages,HEL-01,36,8,7,12,0.95",
                "2026-03-06,SKU-001,6,10.0,beverages,HEL-01,34,8,7,12,0.95",
                "2026-03-07,SKU-001,7,10.0,beverages,HEL-01,32,8,7,12,0.95",
                "2026-03-01,SKU-002,7,12.0,snacks,HEL-02,18,2,6,10,0.97",
                "2026-03-02,SKU-002,8,12.0,snacks,HEL-02,17,2,6,10,0.97",
                "2026-03-03,SKU-002,9,12.0,snacks,HEL-02,15,2,6,10,0.97",
                "2026-03-04,SKU-002,9,12.0,snacks,HEL-02,13,2,6,10,0.97",
                "2026-03-05,SKU-002,10,12.0,snacks,HEL-02,11,2,6,10,0.97",
                "2026-03-06,SKU-002,11,12.0,snacks,HEL-02,9,2,6,10,0.97",
                "2026-03-07,SKU-002,12,12.0,snacks,HEL-02,7,2,6,10,0.97",
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
                "mapping": {
                    "order_date": "order_date",
                    "sku": "sku",
                    "quantity": "quantity",
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return (
        upload_id,
        uploads_dir,
        forecast_artifact_dir,
        stockout_artifact_dir,
        reorder_artifact_dir,
    )


def test_run_phase13_reorder_engine_builds_ranked_recommendations(tmp_path: Path) -> None:
    upload_id, uploads_dir, forecast_artifact_dir, stockout_artifact_dir, reorder_artifact_dir = (
        _write_phase13_upload(tmp_path)
    )

    artifact = run_phase13_reorder_engine(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=reorder_artifact_dir,
        refresh_forecast=True,
        refresh_stockout=True,
    )

    assert artifact.summary.total_skus == 2
    assert artifact.summary.urgent_skus >= 1
    assert artifact.recommendations[0].urgency_score >= artifact.recommendations[-1].urgency_score
    assert artifact.recommendations[0].reorder_quantity >= 0
    assert Path(artifact.artifact_path).exists()


def test_get_reorder_recommendation_reads_saved_artifact(tmp_path: Path) -> None:
    upload_id, uploads_dir, forecast_artifact_dir, stockout_artifact_dir, reorder_artifact_dir = (
        _write_phase13_upload(tmp_path)
    )
    run_phase13_reorder_engine(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=reorder_artifact_dir,
        refresh_forecast=True,
        refresh_stockout=True,
    )

    recommendation = get_reorder_recommendation(
        upload_id=upload_id,
        sku="SKU-002",
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=reorder_artifact_dir,
    )

    assert recommendation["sku"] == "SKU-002"
    assert recommendation["urgency"] in {"medium", "high", "critical"}
    assert recommendation["rationale"]


def test_phase13_router_returns_recommendation_list_and_detail(tmp_path: Path) -> None:
    upload_id, uploads_dir, forecast_artifact_dir, stockout_artifact_dir, reorder_artifact_dir = (
        _write_phase13_upload(tmp_path)
    )
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    list_response = client.get(
        "/api/v1/reorder/recommendations",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "forecast_artifact_dir": str(forecast_artifact_dir),
            "stockout_artifact_dir": str(stockout_artifact_dir),
            "artifact_dir": str(reorder_artifact_dir),
            "refresh": "true",
        },
    )
    assert list_response.status_code == 200, list_response.text
    list_payload = list_response.json()
    assert list_payload["summary"]["total_skus"] == 2
    assert len(list_payload["recommendations"]) == 2

    detail_response = client.get(
        "/api/v1/reorder/SKU-002",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "forecast_artifact_dir": str(forecast_artifact_dir),
            "stockout_artifact_dir": str(stockout_artifact_dir),
            "artifact_dir": str(reorder_artifact_dir),
        },
    )
    assert detail_response.status_code == 200, detail_response.text
    detail_payload = detail_response.json()
    assert detail_payload["sku"] == "SKU-002"
    assert detail_payload["reorder_quantity"] >= 0
