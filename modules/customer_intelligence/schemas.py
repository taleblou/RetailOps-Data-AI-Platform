from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerSummaryResponse(BaseModel):
    customer_count: int
    repeat_customer_count: int
    repeat_customer_rate: float
    average_order_value: float
    average_orders_per_customer: float


class CustomerSegmentResponse(BaseModel):
    customer_id: str
    order_count: int
    total_revenue: float
    average_order_value: float
    total_quantity: float
    recency_days: int
    segment: str
    expected_ltv: float


class CustomerIntelligenceArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: CustomerSummaryResponse
    customers: list[CustomerSegmentResponse] = Field(default_factory=list)
