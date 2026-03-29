from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerCohortSummaryResponse(BaseModel):
    cohort_count: int
    customer_count: int
    repeat_customer_count: int
    repeat_customer_rate: float
    largest_cohort_month: str
    largest_cohort_size: int


class CustomerCohortDetailResponse(BaseModel):
    cohort_month: str
    customer_count: int
    repeat_customer_count: int
    repeat_customer_rate: float
    order_count: int
    revenue: float
    average_orders_per_customer: float
    average_revenue_per_customer: float


class CustomerCohortArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: CustomerCohortSummaryResponse
    cohorts: list[CustomerCohortDetailResponse] = Field(default_factory=list)
