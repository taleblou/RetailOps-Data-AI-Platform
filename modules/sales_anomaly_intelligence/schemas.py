from __future__ import annotations

from pydantic import BaseModel, Field


class SalesAnomalySummaryResponse(BaseModel):
    day_count: int
    anomaly_count: int
    spike_count: int
    drop_count: int
    largest_positive_delta_ratio: float
    largest_negative_delta_ratio: float


class SalesAnomalyDetailResponse(BaseModel):
    order_date: str
    revenue: float
    order_count: int
    quantity: float
    dominant_category: str
    baseline_revenue: float
    delta_ratio: float
    anomaly_type: str


class SalesAnomalyArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: SalesAnomalySummaryResponse
    days: list[SalesAnomalyDetailResponse] = Field(default_factory=list)
