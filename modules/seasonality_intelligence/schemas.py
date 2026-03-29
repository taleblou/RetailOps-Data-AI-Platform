from __future__ import annotations

from pydantic import BaseModel, Field


class SeasonalitySummaryResponse(BaseModel):
    sku_count: int
    strong_seasonal_sku_count: int
    moderate_seasonal_sku_count: int
    steady_sku_count: int
    most_common_peak_month: str


class SeasonalitySkuResponse(BaseModel):
    sku: str
    category: str
    total_revenue: float
    active_month_count: int
    peak_month: str
    peak_month_revenue_share: float
    trough_month: str
    seasonality_band: str


class SeasonalityArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: SeasonalitySummaryResponse
    skus: list[SeasonalitySkuResponse] = Field(default_factory=list)
