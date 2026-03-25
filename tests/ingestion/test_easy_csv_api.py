from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def test_easy_csv_upload_and_preview(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    repository = MemoryRepository()
    app = create_app(repository=repository)
    client = TestClient(app)

    csv_content = (
        "order_id,order_date,customer_id,sku,quantity,unit_price\n"
        "1001,2026-03-20T10:00:00,5001,SKU-001,2,10.50\n"
        "1002,2026-03-21T11:00:00,5002,SKU-002,1,15.00\n"
    )

    upload_response = client.post(
        "/easy-csv/upload",
        files={
            "file": ("orders.csv", csv_content.encode("utf-8"), "text/csv"),
        },
    )

    assert upload_response.status_code == 200, upload_response.text
    payload = upload_response.json()

    assert payload["filename"] == "orders.csv"
    assert payload["columns"] == [
        "order_id",
        "order_date",
        "customer_id",
        "sku",
        "quantity",
        "unit_price",
    ]
    assert payload["preview_row_count"] == 2
    assert len(payload["sample_rows"]) == 2

    upload_id = payload["upload_id"]

    preview_response = client.get(f"/easy-csv/{upload_id}/preview")
    assert preview_response.status_code == 200, preview_response.text
    preview_payload = preview_response.json()

    assert preview_payload["upload_id"] == upload_id
    assert preview_payload["columns"] == payload["columns"]
    assert len(preview_payload["sample_rows"]) == 2
