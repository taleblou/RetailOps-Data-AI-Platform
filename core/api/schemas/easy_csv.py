from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EasyCsvPreviewResponse(BaseModel):
    upload_id: str
    filename: str
    stored_path: str
    delimiter: str = ","
    encoding: str = "utf-8"
    columns: list[str] = Field(default_factory=list)
    sample_rows: list[dict[str, str | None]] = Field(default_factory=list)
    preview_row_count: int = 0


class EasyCsvMappingRequest(BaseModel):
    mappings: dict[str, str] = Field(default_factory=dict)


class EasyCsvMappingResponse(BaseModel):
    upload_id: str
    filename: str
    mapped_columns: dict[str, str] = Field(default_factory=dict)
    unmapped_columns: list[str] = Field(default_factory=list)
    required_missing: list[str] = Field(default_factory=list)
    aliases_applied: dict[str, str] = Field(default_factory=dict)


class EasyCsvValidationIssue(BaseModel):
    level: str
    code: str
    message: str
    column: str | None = None
    row_number: int | None = None
    value: Any | None = None


class EasyCsvValidationResponse(BaseModel):
    upload_id: str
    filename: str
    row_count: int
    mapped_columns: dict[str, str] = Field(default_factory=dict)
    warnings: list[EasyCsvValidationIssue] = Field(default_factory=list)
    blocking_errors: list[EasyCsvValidationIssue] = Field(default_factory=list)
    can_import: bool


class EasyCsvImportResponse(BaseModel):
    upload_id: str
    filename: str
    source_id: int
    source_name: str
    import_job_id: int
    sync_run_id: int
    rows_extracted: int
    rows_loaded: int
    source_status: str


class EasyCsvTransformDailyMetric(BaseModel):
    sales_date: str
    order_count: int
    total_quantity: float
    total_revenue: float


class EasyCsvTransformResponse(BaseModel):
    upload_id: str
    filename: str
    transform_run_id: str
    input_row_count: int
    output_row_count: int
    total_orders: int
    total_quantity: float
    total_revenue: float
    daily_sales: list[EasyCsvTransformDailyMetric] = Field(default_factory=list)
    artifact_path: str


class EasyCsvDashboardCard(BaseModel):
    title: str
    value: str
    description: str


class EasyCsvDashboardResponse(BaseModel):
    upload_id: str
    filename: str
    dashboard_id: str
    dashboard_title: str
    dashboard_url: str
    artifact_path: str
    cards: list[EasyCsvDashboardCard] = Field(default_factory=list)


class EasyCsvForecastHorizon(BaseModel):
    horizon_days: int
    projected_orders: float
    projected_units: float
    projected_revenue: float


class EasyCsvForecastDailyPoint(BaseModel):
    forecast_date: str
    projected_units: float
    projected_revenue: float


class EasyCsvForecastResponse(BaseModel):
    upload_id: str
    filename: str
    forecast_run_id: str
    baseline_method: str
    base_daily_orders: float
    base_daily_units: float
    base_daily_revenue: float
    horizons: list[EasyCsvForecastHorizon] = Field(default_factory=list)
    daily_forecast: list[EasyCsvForecastDailyPoint] = Field(default_factory=list)
    artifact_path: str
