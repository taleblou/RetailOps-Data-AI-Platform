from __future__ import annotations

from pydantic import BaseModel, Field


class StockoutRiskSkuResponse(BaseModel):
    sku: str
    store_code: str
    as_of_date: str
    available_qty: float
    inbound_qty: float
    avg_daily_demand_7d: float
    avg_daily_demand_28d: float
    demand_trend_ratio: float
    days_to_stockout: float
    lead_time_days: float
    stockout_probability: float
    reorder_urgency_score: float
    expected_lost_sales_estimate: float
    risk_band: str
    recommended_action: str
    feature_timestamp: str
    model_version: str
    explanation_summary: str


class StockoutRiskSummaryResponse(BaseModel):
    total_skus: int
    at_risk_skus: int
    critical_skus: int
    average_days_to_stockout: float
    average_stockout_probability: float
    predictions_table: str


class StockoutRiskSkuListResponse(BaseModel):
    stockout_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: StockoutRiskSummaryResponse
    skus: list[StockoutRiskSkuResponse] = Field(default_factory=list)
    artifact_path: str
