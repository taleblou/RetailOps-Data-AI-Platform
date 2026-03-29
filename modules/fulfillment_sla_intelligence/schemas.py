from __future__ import annotations

from pydantic import BaseModel, Field


class FulfillmentSlaSummaryResponse(BaseModel):
    order_count: int
    delivered_order_count: int
    delayed_order_count: int
    open_breach_risk_count: int
    on_time_rate: float
    average_delay_days: float


class FulfillmentSlaOrderResponse(BaseModel):
    order_id: str
    carrier: str
    region: str
    shipment_status: str
    promised_date: str
    actual_delivery_date: str
    delay_days: float
    sla_band: str
    recommended_action: str


class FulfillmentSlaArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: FulfillmentSlaSummaryResponse
    orders: list[FulfillmentSlaOrderResponse] = Field(default_factory=list)
