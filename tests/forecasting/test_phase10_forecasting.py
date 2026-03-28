from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.forecasting.service import get_product_forecast, run_phase10_batch_forecast


def _write_phase10_upload(tmp_path: Path) -> tuple[str, Path, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "phase10_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,order_date,sku,quantity,unit_price,category,store_code,on_hand_qty",
                "1,2026-03-01,SKU-001,4,10.0,beverages,HEL-01,25",
                "2,2026-03-02,SKU-001,5,10.0,beverages,HEL-01,24",
                "3,2026-03-03,SKU-001,6,10.0,beverages,HEL-01,22",
                "4,2026-03-04,SKU-001,5,10.0,beverages,HEL-01,21",
                "5,2026-03-05,SKU-001,7,10.0,beverages,HEL-01,20",
                "6,2026-03-06,SKU-002,2,20.0,snacks,HEL-02,30",
                "7,2026-03-07,SKU-002,3,20.0,snacks,HEL-02,29",
                "8,2026-03-08,SKU-002,4,20.0,snacks,HEL-02,28",
                "9,2026-03-09,SKU-002,3,20.0,snacks,HEL-02,27",
                "10,2026-03-10,SKU-002,5,20.0,snacks,HEL-02,26",
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
    return upload_id, uploads_dir, artifact_dir


def test_run_phase10_batch_forecast_builds_summary(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_phase10_upload(tmp_path)

    artifact = run_phase10_batch_forecast(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )

    assert artifact.summary.active_products == 2
    assert artifact.summary.nightly_batch_job == "nightly_active_sku_forecast"
    assert set(artifact.summary.model_candidates) == {"seasonal_naive", "moving_average"}
    assert len(artifact.products) == 2
    first_product = artifact.products[0]
    assert first_product.horizons[0].horizon_days == 7
    assert (
        first_product.horizons[0].p10
        <= first_product.horizons[0].p50
        <= first_product.horizons[0].p90
    )
    assert 0.0 <= first_product.horizons[0].stockout_probability <= 1.0
    assert first_product.backtest_metrics.mae >= 0.0
    assert artifact.category_metrics
    assert artifact.product_group_metrics
    assert Path(artifact.artifact_path).exists()


def test_get_product_forecast_reads_product_from_artifact(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_phase10_upload(tmp_path)

    product = get_product_forecast(
        upload_id=upload_id,
        product_id="SKU-001",
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=True,
    )

    assert product["product_id"] == "SKU-001"
    assert product["selected_model"] in {"seasonal_naive", "moving_average"}
    assert len(product["daily_forecast"]) == 30


def test_phase10_forecast_router_returns_summary_and_product(tmp_path: Path) -> None:
    upload_id, uploads_dir, artifact_dir = _write_phase10_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    summary_response = client.get(
        "/api/v1/forecast/summary",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert summary_response.status_code == 200, summary_response.text
    summary_payload = summary_response.json()
    assert summary_payload["active_products"] == 2
    assert summary_payload["model_candidates"] == ["seasonal_naive", "moving_average"]

    product_response = client.get(
        "/api/v1/forecast/products/SKU-002",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
        },
    )
    assert product_response.status_code == 200, product_response.text
    product_payload = product_response.json()
    assert product_payload["product_id"] == "SKU-002"
    assert product_payload["horizons"][1]["horizon_days"] == 14
