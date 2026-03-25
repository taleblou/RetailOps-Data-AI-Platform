from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
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
    upload_id: str
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


def _to_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _resolve_upload_id(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    value = kwargs.get("upload_id")
    if value is None:
        for candidate in args:
            if isinstance(candidate, str) and candidate:
                value = candidate
                break
    text = _to_text(value)
    if not text:
        raise ValueError("upload_id is required for the starter forecast run.")
    return text


def _resolve_artifact_dir(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Path:
    value = kwargs.get("artifact_dir")
    if value is None:
        for candidate in args:
            if isinstance(candidate, Path):
                value = candidate
                break
            if isinstance(candidate, str) and ("/" in candidate or candidate.endswith(".json")):
                value = candidate
                break
    if value is None:
        raise ValueError("artifact_dir is required for the starter forecast run.")
    return Path(str(value))


def _resolve_transform_summary(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    value = kwargs.get("transform_summary")
    if isinstance(value, dict):
        return value
    for candidate in args:
        if isinstance(candidate, dict):
            return candidate
    raise ValueError("transform_summary is required for the starter forecast run.")


def _safe_positive_days(transform_summary: dict[str, Any]) -> int:
    daily_sales = transform_summary.get("daily_sales")
    if isinstance(daily_sales, list):
        populated_days = sum(1 for item in daily_sales if isinstance(item, dict))
        if populated_days > 0:
            return populated_days
    total_orders = _to_float(transform_summary.get("total_orders"))
    if total_orders > 0:
        return 1
    return 1


def _extract_last_sales_date(transform_summary: dict[str, Any]) -> date:
    daily_sales = transform_summary.get("daily_sales")
    if not isinstance(daily_sales, list):
        return date.today()

    dates: list[date] = []
    for item in daily_sales:
        if not isinstance(item, dict):
            continue
        raw_value = _to_text(item.get("sales_date"))
        if not raw_value or raw_value == "unknown":
            continue
        try:
            dates.append(datetime.fromisoformat(raw_value).date())
        except ValueError:
            continue
    return max(dates) if dates else date.today()


def run_first_forecast(*args: Any, **kwargs: Any) -> ForecastArtifact:
    upload_id = _resolve_upload_id(args, kwargs)
    artifact_dir = _resolve_artifact_dir(args, kwargs)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    transform_summary = _resolve_transform_summary(args, kwargs)

    day_count = _safe_positive_days(transform_summary)
    total_orders = _to_float(transform_summary.get("total_orders"))
    total_quantity = _to_float(transform_summary.get("total_quantity"))
    total_revenue = _to_float(transform_summary.get("total_revenue"))

    base_daily_orders = round(total_orders / day_count, 2)
    base_daily_units = round(total_quantity / day_count, 2)
    base_daily_revenue = round(total_revenue / day_count, 2)

    horizons: list[ForecastHorizonArtifact] = []
    for horizon_days in (7, 14, 30):
        horizons.append(
            ForecastHorizonArtifact(
                horizon_days=horizon_days,
                projected_orders=round(base_daily_orders * horizon_days, 2),
                projected_units=round(base_daily_units * horizon_days, 2),
                projected_revenue=round(base_daily_revenue * horizon_days, 2),
            )
        )

    last_sales_date = _extract_last_sales_date(transform_summary)
    daily_forecast = [
        ForecastDailyPointArtifact(
            forecast_date=(last_sales_date + timedelta(days=offset)).isoformat(),
            projected_units=base_daily_units,
            projected_revenue=base_daily_revenue,
        )
        for offset in range(1, 8)
    ]

    forecast_run_id = f"fc_{uuid.uuid4().hex[:12]}"
    artifact_path = artifact_dir / f"{upload_id}_{forecast_run_id}.json"
    artifact = ForecastArtifact(
        forecast_run_id=forecast_run_id,
        upload_id=upload_id,
        baseline_method="daily_average_baseline",
        base_daily_orders=base_daily_orders,
        base_daily_units=base_daily_units,
        base_daily_revenue=base_daily_revenue,
        horizons=horizons,
        daily_forecast=daily_forecast,
        artifact_path=str(artifact_path),
    )
    artifact_path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return artifact
