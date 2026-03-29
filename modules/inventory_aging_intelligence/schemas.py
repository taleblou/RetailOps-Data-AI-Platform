from __future__ import annotations

from pydantic import BaseModel, Field


class InventoryAgingSummaryResponse(BaseModel):
    sku_count: int
    stale_sku_count: int
    critical_aging_count: int
    inventory_coverage_rate: float
    average_days_since_last_sale: float


class InventoryAgingSkuResponse(BaseModel):
    sku: str
    category: str
    order_count: int
    quantity_sold: float
    revenue: float
    on_hand_units: float
    days_since_last_sale: int
    average_daily_units: float
    days_of_cover: float | None = None
    aging_band: str


class InventoryAgingArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: InventoryAgingSummaryResponse
    skus: list[InventoryAgingSkuResponse] = Field(default_factory=list)
