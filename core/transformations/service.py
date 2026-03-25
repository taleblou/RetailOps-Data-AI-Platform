from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ForecastHorizonArtifact:
    horizon_days: int
    projected_orders: float
    projected_units: float
    projected_revenue: float


@dataclass(slots=True)
class ForecastDailyPointArtifact:
    forecast_date: str
    projected_units: float
    projected_revenue: float


@dataclass(slots=True)
class ForecastArtifact:
    forecast_run_id: str
    baseline_method: str
    base_daily_orders: float
    base_daily_units: float
    base_daily_revenue: float
    horizons: list[ForecastHorizonArtifact]
    daily_forecast: list[ForecastDailyPointArtifact]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _to_float(value: object, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return float(text)
        except ValueError:
            return default
    return default


def _as_daily_sales_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            rows.append(dict(item))
    return rows


def run_first_forecast(
    *,
    upload_id: str,
    transform_summary: dict[str, object],
    artifact_dir: Path,
) -> ForecastArtifact:
    artifact_dir.mkdir(parents=True, exist_ok=True)

    forecast_run_id = f"fc_{uuid.uuid4().hex[:12]}"
    daily_sales = _as_daily_sales_rows(transform_summary.get("daily_sales"))
    sales_day_count = max(len(daily_sales), 1)

    total_orders = _to_float(
        transform_summary.get("total_orders"),
        default=float(len(daily_sales)),
    )
    total_quantity = _to_float(transform_summary.get("total_quantity"))
    total_revenue = _to_float(transform_summary.get("total_revenue"))

    base_daily_orders = round(total_orders / sales_day_count, 2)
    base_daily_units = round(total_quantity / sales_day_count, 2)
    base_daily_revenue = round(total_revenue / sales_day_count, 2)

    horizons = [
        ForecastHorizonArtifact(
            horizon_days=days,
            projected_orders=round(base_daily_orders * days, 2),
            projected_units=round(base_daily_units * days, 2),
            projected_revenue=round(base_daily_revenue * days, 2),
        )
        for days in (7, 14, 30)
    ]

    start_day = date.today() + timedelta(days=1)
    daily_forecast = [
        ForecastDailyPointArtifact(
            forecast_date=(start_day + timedelta(days=offset)).isoformat(),
            projected_units=base_daily_units,
            projected_revenue=base_daily_revenue,
        )
        for offset in range(7)
    ]

    artifact_path = artifact_dir / f"{upload_id}_{forecast_run_id}.json"
    artifact = ForecastArtifact(
        forecast_run_id=forecast_run_id,
        baseline_method="simple_daily_average",
        base_daily_orders=base_daily_orders,
        base_daily_units=base_daily_units,
        base_daily_revenue=base_daily_revenue,
        horizons=horizons,
        daily_forecast=daily_forecast,
        artifact_path=str(artifact_path),
    )
    artifact_path.write_text(
        json.dumps(
            artifact.to_dict(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact
