from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from core.serving.service import get_or_create_phase16_batch_artifact


def _write_phase16_upload(tmp_path: Path) -> dict[str, Path | str]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    forecast_artifact_dir = tmp_path / "forecast_artifacts"
    forecast_artifact_dir.mkdir(parents=True, exist_ok=True)
    shipment_artifact_dir = tmp_path / "shipment_artifacts"
    shipment_artifact_dir.mkdir(parents=True, exist_ok=True)
    stockout_artifact_dir = tmp_path / "stockout_artifacts"
    stockout_artifact_dir.mkdir(parents=True, exist_ok=True)
    reorder_artifact_dir = tmp_path / "reorder_artifacts"
    reorder_artifact_dir.mkdir(parents=True, exist_ok=True)
    serving_artifact_dir = tmp_path / "serving_artifacts"
    serving_artifact_dir.mkdir(parents=True, exist_ok=True)

    upload_id = "phase16_upload"
    orders_csv = uploads_dir / f"{upload_id}_orders.csv"
    orders_csv.write_text(
        "\n".join(
            [
                (
                    "order_date,sku,quantity,unit_price,category,store_code,"
                    "available_qty,in_transit_qty,lead_time_days,supplier_moq,"
                    "service_level_target"
                ),
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
                "2026-03-01,SKU-003,9,20.0,household,HEL-03,8,0,7,16,0.98",
                "2026-03-02,SKU-003,10,20.0,household,HEL-03,7,0,7,16,0.98",
                "2026-03-03,SKU-003,11,20.0,household,HEL-03,6,0,7,16,0.98",
                "2026-03-04,SKU-003,12,20.0,household,HEL-03,5,0,7,16,0.98",
                "2026-03-05,SKU-003,12,20.0,household,HEL-03,4,0,7,16,0.98",
                "2026-03-06,SKU-003,13,20.0,household,HEL-03,3,0,7,16,0.98",
                "2026-03-07,SKU-003,14,20.0,household,HEL-03,2,0,7,16,0.98",
            ]
        ),
        encoding="utf-8",
    )
    shipments_csv = uploads_dir / f"{upload_id}_shipments.csv"
    shipments_csv.write_text(
        "\n".join(
            [
                (
                    "Shipment ID,Order ID,Store Code,Carrier,Shipment Status,"
                    "Promised Date,Actual Delivery Date,Order Date,Inventory Lag Days"
                ),
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
                "filename": "orders.csv",
                "stored_path": str(orders_csv),
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
    return {
        "upload_id": upload_id,
        "uploads_dir": uploads_dir,
        "forecast_artifact_dir": forecast_artifact_dir,
        "shipment_artifact_dir": shipment_artifact_dir,
        "stockout_artifact_dir": stockout_artifact_dir,
        "reorder_artifact_dir": reorder_artifact_dir,
        "serving_artifact_dir": serving_artifact_dir,
    }


def test_run_phase16_batch_serving_builds_summary_artifact(tmp_path: Path) -> None:
    paths = _write_phase16_upload(tmp_path)

    artifact = get_or_create_phase16_batch_artifact(
        upload_id=str(paths["upload_id"]),
        uploads_dir=Path(paths["uploads_dir"]),
        forecast_artifact_dir=Path(paths["forecast_artifact_dir"]),
        shipment_artifact_dir=Path(paths["shipment_artifact_dir"]),
        stockout_artifact_dir=Path(paths["stockout_artifact_dir"]),
        artifact_dir=Path(paths["serving_artifact_dir"]),
        refresh=True,
    )

    assert artifact["status"] == "completed"
    assert len(artifact["jobs"]) == 3
    assert {job["job_name"] for job in artifact["jobs"]} == {
        "nightly_forecast",
        "stockout_daily_scoring",
        "shipment_open_order_scoring",
    }
    assert Path(artifact["artifact_path"]).exists()


def test_phase16_serving_router_returns_standardized_payloads(tmp_path: Path) -> None:
    paths = _write_phase16_upload(tmp_path)
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    batch_response = client.post(
        "/api/v1/serving/batch/run",
        json={
            "upload_id": paths["upload_id"],
            "uploads_dir": str(paths["uploads_dir"]),
            "forecast_artifact_dir": str(paths["forecast_artifact_dir"]),
            "shipment_artifact_dir": str(paths["shipment_artifact_dir"]),
            "stockout_artifact_dir": str(paths["stockout_artifact_dir"]),
            "artifact_dir": str(paths["serving_artifact_dir"]),
            "refresh": True,
        },
    )
    assert batch_response.status_code == 200, batch_response.text
    batch_payload = batch_response.json()
    assert len(batch_payload["jobs"]) == 3
    assert "prediction" in batch_payload["standard_response_fields"]

    forecast_response = client.get(
        "/api/v1/serving/forecast/products/SKU-001",
        params={
            "upload_id": paths["upload_id"],
            "uploads_dir": str(paths["uploads_dir"]),
            "artifact_dir": str(paths["forecast_artifact_dir"]),
        },
    )
    assert forecast_response.status_code == 200, forecast_response.text
    forecast_payload = forecast_response.json()
    assert forecast_payload["serving_type"] == "forecast"
    assert forecast_payload["interval"]["horizon_days"] == 7
    assert forecast_payload["prediction"]["point_forecast_14d"] >= 0.0

    forecast_explain_response = client.get(
        "/api/v1/serving/forecast/products/SKU-001/explain",
        params={
            "upload_id": paths["upload_id"],
            "uploads_dir": str(paths["uploads_dir"]),
            "artifact_dir": str(paths["forecast_artifact_dir"]),
        },
    )
    assert forecast_explain_response.status_code == 200, forecast_explain_response.text
    forecast_explain_payload = forecast_explain_response.json()
    assert forecast_explain_payload["top_factors"]

    shipment_response = client.get(
        "/api/v1/serving/shipment-risk/open-orders/SHP-004",
        params={
            "upload_id": paths["upload_id"],
            "uploads_dir": str(paths["uploads_dir"]),
            "artifact_dir": str(paths["shipment_artifact_dir"]),
        },
    )
    assert shipment_response.status_code == 200, shipment_response.text
    shipment_payload = shipment_response.json()
    assert shipment_payload["serving_type"] == "shipment_delay"
    assert 0.0 <= shipment_payload["confidence"] <= 1.0

    manual_shipment_response = client.post(
        "/api/v1/serving/predict/shipment-delay",
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
    assert manual_shipment_response.status_code == 200, manual_shipment_response.text
    manual_shipment_payload = manual_shipment_response.json()
    assert manual_shipment_payload["source_artifact"] == "inline-request"
    assert manual_shipment_payload["prediction"]["recommended_action"]

    stockout_response = client.get(
        "/api/v1/serving/stockout-risk/SKU-003",
        params={
            "upload_id": paths["upload_id"],
            "uploads_dir": str(paths["uploads_dir"]),
            "artifact_dir": str(paths["stockout_artifact_dir"]),
        },
    )
    assert stockout_response.status_code == 200, stockout_response.text
    stockout_payload = stockout_response.json()
    assert stockout_payload["prediction"]["stockout_probability"] >= 0.0

    reorder_response = client.get(
        "/api/v1/serving/reorder/SKU-003",
        params={
            "upload_id": paths["upload_id"],
            "uploads_dir": str(paths["uploads_dir"]),
            "forecast_artifact_dir": str(paths["forecast_artifact_dir"]),
            "stockout_artifact_dir": str(paths["stockout_artifact_dir"]),
            "artifact_dir": str(paths["reorder_artifact_dir"]),
        },
    )
    assert reorder_response.status_code == 200, reorder_response.text
    reorder_payload = reorder_response.json()
    assert reorder_payload["serving_type"] == "reorder"
    assert reorder_payload["prediction"]["reorder_quantity"] >= 0.0

    reorder_explain_response = client.get(
        "/api/v1/serving/reorder/SKU-003/explain",
        params={
            "upload_id": paths["upload_id"],
            "uploads_dir": str(paths["uploads_dir"]),
            "forecast_artifact_dir": str(paths["forecast_artifact_dir"]),
            "stockout_artifact_dir": str(paths["stockout_artifact_dir"]),
            "artifact_dir": str(paths["reorder_artifact_dir"]),
        },
    )
    assert reorder_explain_response.status_code == 200, reorder_explain_response.text
    reorder_explain_payload = reorder_explain_response.json()
    assert reorder_explain_payload["recommended_action"]
