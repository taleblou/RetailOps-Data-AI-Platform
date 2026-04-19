# Project:      RetailOps Data & AI Platform
# Module:       modules.forecasting
# File:         service.py
# Path:         modules/forecasting/service.py
#
# Summary:      Implements the forecasting service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for forecasting workflows.
# Scope:        internal
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
#   - Main types: ForecastHorizonArtifact, ForecastDailyPointArtifact, ForecastArtifact, ForecastMetricArtifact, ForecastModelScoreArtifact, ForecastIntervalArtifact, ...
#   - Key APIs: run_first_forecast, run_batch_forecast, load_batch_forecast_artifact, get_or_create_batch_forecast_artifact, get_product_forecast
#   - Dependencies: __future__, csv, json, math, uuid, collections, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import json
import math
import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
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


@dataclass(slots=True)
class ForecastMetricArtifact:
    mae: float
    rmse: float
    mape: float
    bias: float


@dataclass(slots=True)
class ForecastModelScoreArtifact:
    model_name: str
    metrics: ForecastMetricArtifact


@dataclass(slots=True)
class ForecastIntervalArtifact:
    horizon_days: int
    point_forecast: float
    p10: float
    p50: float
    p90: float
    stockout_probability: float


@dataclass(slots=True)
class ForecastDailyIntervalArtifact:
    forecast_date: str
    p10: float
    p50: float
    p90: float


@dataclass(slots=True)
class ForecastGroupedMetricArtifact:
    group_name: str
    product_count: int
    metrics: ForecastMetricArtifact


@dataclass(slots=True)
class ForecastProductArtifact:
    product_id: str
    category: str
    product_group: str
    selected_model: str
    baseline_models: list[ForecastModelScoreArtifact]
    model_version: str
    feature_timestamp: str
    training_window_start: str
    training_window_end: str
    history_points: int
    latest_inventory_units: float
    inventory_source: str
    horizons: list[ForecastIntervalArtifact]
    daily_forecast: list[ForecastDailyIntervalArtifact]
    backtest_metrics: ForecastMetricArtifact
    explanation_summary: str


@dataclass(slots=True)
class ForecastBatchSummaryArtifact:
    active_products: int
    categories: list[str]
    product_groups: list[str]
    nightly_batch_job: str
    model_candidates: list[str]
    champion_model_counts: dict[str, int]
    average_metrics: ForecastMetricArtifact


@dataclass(slots=True)
class ForecastBatchArtifact:
    forecast_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: ForecastBatchSummaryArtifact
    category_metrics: list[ForecastGroupedMetricArtifact]
    product_group_metrics: list[ForecastGroupedMetricArtifact]
    products: list[ForecastProductArtifact]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


MODEL_CANDIDATES: tuple[str, str] = ("seasonal_naive", "moving_average")
FORECAST_MODEL_VERSION = "forecasting-baseline-v1"
FORECAST_BATCH_JOB = "nightly_active_sku_forecast"
FORECAST_ARTIFACT_SUFFIX = "forecasting"


class ForecastArtifactNotFoundError(FileNotFoundError):
    """Raised when a requested forecast artifact does not exist."""


@dataclass(slots=True)
class _ProductSeries:
    product_id: str
    category: str
    product_group: str
    dates: list[date]
    quantities: list[float]
    latest_inventory_units: float
    inventory_source: str


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


def _load_upload_metadata(upload_id: str, uploads_dir: Path) -> dict[str, Any]:
    metadata_path = uploads_dir / f"{upload_id}.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Upload metadata was not found for upload_id={upload_id}.")
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Upload metadata is invalid for upload_id={upload_id}.")
    return payload


def _resolve_uploaded_csv_path(metadata: dict[str, Any], uploads_dir: Path) -> Path:
    stored_path = _to_text(metadata.get("stored_path"))
    candidates: list[Path] = []
    if stored_path:
        path = Path(stored_path)
        if path.is_absolute():
            candidates.append(path)
        else:
            candidates.append(path)
            candidates.append(uploads_dir / path.name)
    upload_id = _to_text(metadata.get("upload_id"))
    filename = _to_text(metadata.get("filename"))
    if upload_id and filename:
        candidates.append(uploads_dir / f"{upload_id}_{filename}")
    if upload_id:
        candidates.extend(sorted(uploads_dir.glob(f"{upload_id}_*.csv")))

    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Uploaded CSV file was not found for the forecast batch.")


_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "product_id": ("product_id", "sku", "sku_code", "product", "item_id"),
    "order_date": ("order_date", "date", "ordered_at", "sales_date", "timestamp"),
    "quantity": ("quantity", "qty", "units", "unit_count"),
    "unit_price": ("unit_price", "price", "amount", "line_price"),
    "revenue": ("revenue", "line_total", "total_amount", "sales_amount"),
    "inventory": (
        "available_qty",
        "available",
        "inventory_on_hand",
        "on_hand",
        "on_hand_qty",
        "stock_on_hand",
    ),
    "category": ("category", "product_category", "department"),
    "product_group": ("product_group", "brand", "collection", "store_code"),
}


def _candidate_columns(
    mapping: dict[str, str], canonical_name: str, field_names: Sequence[str]
) -> list[str]:
    candidates: list[str] = []
    mapped = _to_text(mapping.get(canonical_name))
    if mapped:
        candidates.append(mapped)
    for alias in _ALIAS_MAP.get(canonical_name, ()):
        if alias in field_names:
            candidates.append(alias)
    return list(dict.fromkeys(column for column in candidates if column in field_names))


def _pick_value(row: dict[str, str], candidates: list[str]) -> str:
    for column in candidates:
        value = _to_text(row.get(column))
        if value:
            return value
    return ""


def _parse_order_date(raw_value: str) -> date | None:
    text = raw_value.strip()
    if not text:
        return None
    for parser in (datetime.fromisoformat,):
        try:
            return parser(text).date()
        except ValueError:
            continue
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _build_metric(errors: list[float], actuals: list[float]) -> ForecastMetricArtifact:
    if not errors:
        return ForecastMetricArtifact(mae=0.0, rmse=0.0, mape=0.0, bias=0.0)
    absolute_errors = [abs(item) for item in errors]
    mae = sum(absolute_errors) / len(absolute_errors)
    rmse = math.sqrt(sum(item * item for item in errors) / len(errors))
    non_zero_actuals = [
        abs(error) / abs(actual)
        for error, actual in zip(errors, actuals, strict=False)
        if abs(actual) > 1e-9
    ]
    mape = (sum(non_zero_actuals) / len(non_zero_actuals) * 100.0) if non_zero_actuals else 0.0
    bias = sum(errors) / len(errors)
    return ForecastMetricArtifact(
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        mape=round(mape, 4),
        bias=round(bias, 4),
    )


def _evaluate_models(values: list[float], *, window: int = 7) -> dict[str, ForecastMetricArtifact]:
    if len(values) < 2:
        default_metric = ForecastMetricArtifact(mae=0.0, rmse=0.0, mape=0.0, bias=0.0)
        return {model_name: default_metric for model_name in MODEL_CANDIDATES}

    seasonal_errors: list[float] = []
    seasonal_actuals: list[float] = []
    moving_errors: list[float] = []
    moving_actuals: list[float] = []

    for index in range(1, len(values)):
        actual = values[index]
        seasonal_prediction = values[index - 1]
        moving_window = values[max(0, index - window) : index]
        moving_prediction = (
            sum(moving_window) / len(moving_window) if moving_window else values[index - 1]
        )

        seasonal_errors.append(seasonal_prediction - actual)
        seasonal_actuals.append(actual)
        moving_errors.append(moving_prediction - actual)
        moving_actuals.append(actual)

    return {
        "seasonal_naive": _build_metric(seasonal_errors, seasonal_actuals),
        "moving_average": _build_metric(moving_errors, moving_actuals),
    }


def _select_model(metrics_by_model: dict[str, ForecastMetricArtifact]) -> str:
    return min(
        metrics_by_model,
        key=lambda model_name: (
            metrics_by_model[model_name].mae,
            metrics_by_model[model_name].rmse,
            abs(metrics_by_model[model_name].bias),
        ),
    )


def _aggregate_metric_rows(metrics: list[ForecastMetricArtifact]) -> ForecastMetricArtifact:
    if not metrics:
        return ForecastMetricArtifact(mae=0.0, rmse=0.0, mape=0.0, bias=0.0)
    return ForecastMetricArtifact(
        mae=round(sum(item.mae for item in metrics) / len(metrics), 4),
        rmse=round(sum(item.rmse for item in metrics) / len(metrics), 4),
        mape=round(sum(item.mape for item in metrics) / len(metrics), 4),
        bias=round(sum(item.bias for item in metrics) / len(metrics), 4),
    )


def _build_group_metrics(
    products: list[ForecastProductArtifact],
    *,
    group_getter: str,
) -> list[ForecastGroupedMetricArtifact]:
    grouped_metrics: dict[str, list[ForecastMetricArtifact]] = defaultdict(list)
    for product in products:
        group_name = getattr(product, group_getter)
        grouped_metrics[group_name].append(product.backtest_metrics)

    artifacts: list[ForecastGroupedMetricArtifact] = []
    for group_name, metrics in sorted(grouped_metrics.items()):
        artifacts.append(
            ForecastGroupedMetricArtifact(
                group_name=group_name,
                product_count=len(metrics),
                metrics=_aggregate_metric_rows(metrics),
            )
        )
    return artifacts


def _date_range(start_date: date, end_date: date) -> list[date]:
    total_days = (end_date - start_date).days + 1
    return [start_date + timedelta(days=offset) for offset in range(max(total_days, 1))]


def _estimated_inventory_units(values: list[float]) -> float:
    if not values:
        return 0.0
    tail = values[-14:] if len(values) >= 14 else values
    return max(sum(tail) * 1.2, max(tail, default=0.0) * 7.0, 1.0)


def _build_product_series(upload_id: str, uploads_dir: Path) -> list[_ProductSeries]:
    metadata = _load_upload_metadata(upload_id, uploads_dir)
    csv_path = _resolve_uploaded_csv_path(metadata, uploads_dir)
    mapping = metadata.get("mapping")
    if not isinstance(mapping, dict):
        mapping = {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        field_names = reader.fieldnames or []
        if not field_names:
            raise ValueError("Uploaded CSV file has no header row.")

        product_columns = _candidate_columns(mapping, "product_id", field_names)
        order_date_columns = _candidate_columns(mapping, "order_date", field_names)
        quantity_columns = _candidate_columns(mapping, "quantity", field_names)
        inventory_columns = _candidate_columns(mapping, "inventory", field_names)
        category_columns = _candidate_columns(mapping, "category", field_names)
        product_group_columns = _candidate_columns(mapping, "product_group", field_names)

        if not product_columns:
            raise ValueError("The uploaded CSV does not expose a product identifier column.")
        if not order_date_columns:
            raise ValueError("The uploaded CSV does not expose an order date column.")
        if not quantity_columns:
            raise ValueError("The uploaded CSV does not expose a quantity column.")

        quantity_by_product: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
        category_by_product: dict[str, str] = {}
        group_by_product: dict[str, str] = {}
        inventory_by_product: dict[str, float] = {}

        for row in reader:
            product_id = _pick_value(row, product_columns)
            raw_order_date = _pick_value(row, order_date_columns)
            order_day = _parse_order_date(raw_order_date)
            quantity = _to_float(_pick_value(row, quantity_columns))
            if not product_id or order_day is None:
                continue
            quantity_by_product[product_id][order_day] += quantity

            category = _pick_value(row, category_columns) or "uncategorized"
            category_by_product.setdefault(product_id, category)

            product_group = (
                _pick_value(row, product_group_columns) or category_by_product[product_id]
            )
            group_by_product.setdefault(product_id, product_group)

            inventory_text = _pick_value(row, inventory_columns)
            if inventory_text:
                inventory_by_product[product_id] = _to_float(inventory_text)

    series_list: list[_ProductSeries] = []
    for product_id, daily_map in sorted(quantity_by_product.items()):
        dates = sorted(daily_map)
        if not dates:
            continue
        full_dates = _date_range(dates[0], dates[-1])
        values = [round(daily_map.get(item, 0.0), 4) for item in full_dates]
        inventory_source = (
            "uploaded_inventory"
            if product_id in inventory_by_product
            else "estimated_from_recent_demand"
        )
        latest_inventory_units = inventory_by_product.get(
            product_id, _estimated_inventory_units(values)
        )
        series_list.append(
            _ProductSeries(
                product_id=product_id,
                category=category_by_product.get(product_id, "uncategorized"),
                product_group=group_by_product.get(
                    product_id, category_by_product.get(product_id, "uncategorized")
                ),
                dates=full_dates,
                quantities=values,
                latest_inventory_units=round(latest_inventory_units, 2),
                inventory_source=inventory_source,
            )
        )

    if not series_list:
        raise ValueError("No usable product demand history was found in the uploaded CSV.")
    return series_list


def _build_daily_forecast_points(
    *,
    anchor_date: date,
    selected_model: str,
    values: list[float],
    residual_rmse: float,
    days: int = 30,
    moving_average_window: int = 7,
) -> list[ForecastDailyIntervalArtifact]:
    if not values:
        return []

    if selected_model == "seasonal_naive":
        baseline_value = values[-1]
    else:
        window = values[-moving_average_window:] if len(values) >= moving_average_window else values
        baseline_value = sum(window) / len(window)

    daily_sigma = max(residual_rmse, max(baseline_value * 0.1, 0.25))
    spread_multiplier = 1.28155
    points: list[ForecastDailyIntervalArtifact] = []
    for offset in range(1, days + 1):
        p50 = round(baseline_value, 2)
        spread = spread_multiplier * daily_sigma
        p10 = round(max(0.0, p50 - spread), 2)
        p90 = round(max(p50, p50 + spread), 2)
        points.append(
            ForecastDailyIntervalArtifact(
                forecast_date=(anchor_date + timedelta(days=offset)).isoformat(),
                p10=p10,
                p50=p50,
                p90=p90,
            )
        )
    return points


def _build_horizon_forecasts(
    daily_points: list[ForecastDailyIntervalArtifact],
    *,
    latest_inventory_units: float,
    residual_rmse: float,
) -> list[ForecastIntervalArtifact]:
    horizons: list[ForecastIntervalArtifact] = []
    for horizon_days in (7, 14, 30):
        selected_points = daily_points[:horizon_days]
        point_forecast = round(sum(item.p50 for item in selected_points), 2)
        p10 = round(sum(item.p10 for item in selected_points), 2)
        p50 = point_forecast
        p90 = round(sum(item.p90 for item in selected_points), 2)
        sigma = max(residual_rmse * math.sqrt(max(horizon_days, 1)), 0.25)
        z_score = (latest_inventory_units - p50) / sigma
        stockout_probability = round(max(0.0, min(1.0, 1.0 - _normal_cdf(z_score))), 4)
        horizons.append(
            ForecastIntervalArtifact(
                horizon_days=horizon_days,
                point_forecast=point_forecast,
                p10=p10,
                p50=p50,
                p90=p90,
                stockout_probability=stockout_probability,
            )
        )
    return horizons


def _build_product_artifact(series: _ProductSeries) -> ForecastProductArtifact:
    metrics_by_model = _evaluate_models(series.quantities)
    selected_model = _select_model(metrics_by_model)
    selected_metrics = metrics_by_model[selected_model]
    daily_points = _build_daily_forecast_points(
        anchor_date=series.dates[-1],
        selected_model=selected_model,
        values=series.quantities,
        residual_rmse=selected_metrics.rmse,
    )
    horizons = _build_horizon_forecasts(
        daily_points,
        latest_inventory_units=series.latest_inventory_units,
        residual_rmse=selected_metrics.rmse,
    )
    baseline_models = [
        ForecastModelScoreArtifact(model_name=model_name, metrics=metrics_by_model[model_name])
        for model_name in MODEL_CANDIDATES
    ]
    explanation_summary = (
        f"Selected {selected_model} because it produced the lowest MAE on the rolling backtest. "
        f"Inventory source is {series.inventory_source}."
    )
    feature_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    return ForecastProductArtifact(
        product_id=series.product_id,
        category=series.category,
        product_group=series.product_group,
        selected_model=selected_model,
        baseline_models=baseline_models,
        model_version=FORECAST_MODEL_VERSION,
        feature_timestamp=feature_timestamp,
        training_window_start=series.dates[0].isoformat(),
        training_window_end=series.dates[-1].isoformat(),
        history_points=len(series.quantities),
        latest_inventory_units=series.latest_inventory_units,
        inventory_source=series.inventory_source,
        horizons=horizons,
        daily_forecast=daily_points,
        backtest_metrics=selected_metrics,
        explanation_summary=explanation_summary,
    )


def _build_batch_summary(products: list[ForecastProductArtifact]) -> ForecastBatchSummaryArtifact:
    champion_model_counts = {
        model_name: sum(1 for product in products if product.selected_model == model_name)
        for model_name in MODEL_CANDIDATES
    }
    average_metrics = _aggregate_metric_rows([product.backtest_metrics for product in products])
    return ForecastBatchSummaryArtifact(
        active_products=len(products),
        categories=sorted({product.category for product in products}),
        product_groups=sorted({product.product_group for product in products}),
        nightly_batch_job=FORECAST_BATCH_JOB,
        model_candidates=list(MODEL_CANDIDATES),
        champion_model_counts=champion_model_counts,
        average_metrics=average_metrics,
    )


def run_batch_forecast(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
) -> ForecastBatchArtifact:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    product_series = _build_product_series(upload_id=upload_id, uploads_dir=uploads_dir)
    products = [_build_product_artifact(series) for series in product_series]
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    forecast_run_id = f"fc10_{uuid.uuid4().hex[:12]}"
    artifact_path = artifact_dir / f"{upload_id}_{FORECAST_ARTIFACT_SUFFIX}_{forecast_run_id}.json"
    artifact = ForecastBatchArtifact(
        forecast_run_id=forecast_run_id,
        upload_id=upload_id,
        generated_at=generated_at,
        model_version=FORECAST_MODEL_VERSION,
        summary=_build_batch_summary(products),
        category_metrics=_build_group_metrics(products, group_getter="category"),
        product_group_metrics=_build_group_metrics(products, group_getter="product_group"),
        products=products,
        artifact_path=str(artifact_path),
    )
    artifact_path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return artifact


def _load_json_artifact(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Artifact file is invalid: {path}")
    return payload


def load_batch_forecast_artifact(*, upload_id: str, artifact_dir: Path) -> dict[str, Any]:
    pattern = f"{upload_id}_{FORECAST_ARTIFACT_SUFFIX}_*.json"
    matches = sorted(
        artifact_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True
    )
    if not matches:
        raise ForecastArtifactNotFoundError(
            f"No forecasting forecast artifact exists for upload_id={upload_id}."
        )
    return _load_json_artifact(matches[0])


def get_or_create_batch_forecast_artifact(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    if not refresh:
        try:
            return load_batch_forecast_artifact(upload_id=upload_id, artifact_dir=artifact_dir)
        except ForecastArtifactNotFoundError:
            pass
    artifact = run_batch_forecast(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )
    return artifact.to_dict()


def get_product_forecast(
    *,
    upload_id: str,
    product_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact = get_or_create_batch_forecast_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    products = artifact.get("products")
    if not isinstance(products, list):
        raise ValueError("Forecast artifact is missing the product forecast list.")
    normalized_product_id = product_id.strip().lower()
    for product in products:
        if not isinstance(product, dict):
            continue
        candidate = _to_text(product.get("product_id"))
        if candidate.lower() == normalized_product_id:
            return product
    raise ForecastArtifactNotFoundError(
        f"Forecast product was not found for product_id={product_id}."
    )
