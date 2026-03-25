from pathlib import Path

from modules.forecasting.service import run_first_forecast


def test_run_first_forecast_builds_expected_horizons(tmp_path: Path) -> None:
    transform_summary = {
        "total_orders": 2,
        "total_quantity": 3,
        "total_revenue": 36.0,
        "daily_sales": [
            {
                "sales_date": "2026-03-20",
                "order_count": 1,
                "total_quantity": 2,
                "total_revenue": 21.0,
            },
            {
                "sales_date": "2026-03-21",
                "order_count": 1,
                "total_quantity": 1,
                "total_revenue": 15.0,
            },
        ],
    }

    artifact = run_first_forecast(
        upload_id="upload_123",
        transform_summary=transform_summary,
        artifact_dir=tmp_path,
    )

    assert artifact.baseline_method == "daily_average_baseline"
    assert [item.horizon_days for item in artifact.horizons] == [7, 14, 30]
    assert artifact.daily_forecast[0].forecast_date == "2026-03-22"
