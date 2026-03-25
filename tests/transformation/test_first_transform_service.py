from pathlib import Path

from core.transformations.service import run_first_transform


def test_run_first_transform_accepts_positional_rows(tmp_path: Path) -> None:
    rows = [
        {
            "order_id": "1001",
            "order_date": "2026-03-20T10:00:00",
            "customer_id": "5001",
            "sku": "SKU-001",
            "quantity": "2",
            "unit_price": "10.50",
        },
        {
            "order_id": "1002",
            "order_date": "2026-03-21T11:00:00",
            "customer_id": "5002",
            "sku": "SKU-002",
            "quantity": "1",
            "unit_price": "15.00",
        },
    ]

    artifact = run_first_transform(rows, artifact_dir=tmp_path, upload_id="upload_123")

    assert artifact.input_row_count == 2
    assert artifact.output_row_count == 2
    assert artifact.total_orders == 2
    assert artifact.daily_sales[0].total_revenue == 21.0
