from __future__ import annotations

from pydantic import BaseModel, Field


class ForecastMetricResponse(BaseModel):
    mae: float
    rmse: float
    mape: float
    bias: float


class ForecastModelScoreResponse(BaseModel):
    model_name: str
    metrics: ForecastMetricResponse


class ForecastIntervalResponse(BaseModel):
    horizon_days: int
    point_forecast: float
    p10: float
    p50: float
    p90: float
    stockout_probability: float


class ForecastDailyIntervalResponse(BaseModel):
    forecast_date: str
    p10: float
    p50: float
    p90: float


class ForecastGroupedMetricResponse(BaseModel):
    group_name: str
    product_count: int
    metrics: ForecastMetricResponse


class ForecastProductResponse(BaseModel):
    product_id: str
    category: str
    product_group: str
    selected_model: str
    baseline_models: list[ForecastModelScoreResponse] = Field(default_factory=list)
    model_version: str
    feature_timestamp: str
    training_window_start: str
    training_window_end: str
    history_points: int
    latest_inventory_units: float
    inventory_source: str
    horizons: list[ForecastIntervalResponse] = Field(default_factory=list)
    daily_forecast: list[ForecastDailyIntervalResponse] = Field(default_factory=list)
    backtest_metrics: ForecastMetricResponse
    explanation_summary: str


class ForecastSummaryResponse(BaseModel):
    forecast_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    active_products: int
    categories: list[str] = Field(default_factory=list)
    product_groups: list[str] = Field(default_factory=list)
    nightly_batch_job: str
    model_candidates: list[str] = Field(default_factory=list)
    champion_model_counts: dict[str, int] = Field(default_factory=dict)
    average_metrics: ForecastMetricResponse
    category_metrics: list[ForecastGroupedMetricResponse] = Field(default_factory=list)
    product_group_metrics: list[ForecastGroupedMetricResponse] = Field(default_factory=list)
    artifact_path: str
