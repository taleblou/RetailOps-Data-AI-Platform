from __future__ import annotations

from pydantic import BaseModel, Field


class SupplierSummaryResponse(BaseModel):
    supplier_count: int
    total_ordered_qty: float
    total_received_qty: float
    average_fill_rate: float
    average_lead_time_days: float
    high_risk_suppliers: int


class SupplierProcurementResponse(BaseModel):
    supplier_id: str
    supplier_name: str
    rows: int
    total_ordered_qty: float
    total_received_qty: float
    fill_rate: float
    average_lead_time_days: float
    lead_time_variability_days: float
    average_moq: float
    procurement_risk_band: str
    recommended_action: str


class SupplierProcurementArtifactResponse(BaseModel):
    upload_id: str
    generated_at: str
    model_version: str
    artifact_path: str
    summary: SupplierSummaryResponse
    suppliers: list[SupplierProcurementResponse] = Field(default_factory=list)
