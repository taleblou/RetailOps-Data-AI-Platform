from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MonitoringCheckResponse(BaseModel):
    check_name: str
    category: str
    status: str
    metric_name: str
    metric_value: float
    threshold_value: float
    message: str
    recommended_action: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MonitoringAlertResponse(BaseModel):
    alert_id: str
    severity: str
    category: str
    check_name: str
    message: str
    recommended_action: str
    retrain_recommended: bool
    disable_prediction_recommended: bool


class MonitoringDashboardMetricResponse(BaseModel):
    metric_name: str
    value: float
    unit: str
    status: str
    description: str


class MonitoringOverrideEntryResponse(BaseModel):
    override_id: str
    upload_id: str
    prediction_type: str
    entity_id: str
    original_decision: dict[str, Any]
    override_decision: dict[str, Any]
    reason: str
    feedback_label: str | None = None
    user_id: str | None = None
    retraining_feedback_kept: bool = True
    created_at: str


class MonitoringOverrideRequest(BaseModel):
    upload_id: str
    prediction_type: str
    entity_id: str
    original_decision: dict[str, Any]
    override_decision: dict[str, Any]
    reason: str
    feedback_label: str | None = None
    user_id: str | None = None
    override_dir: str = "data/artifacts/monitoring/overrides"


class MonitoringOverrideSummaryResponse(BaseModel):
    upload_id: str
    total_overrides: int
    by_prediction_type: dict[str, int]
    last_override_at: str | None = None
    entries: list[MonitoringOverrideEntryResponse] = Field(default_factory=list)


class MonitoringSummaryResponse(BaseModel):
    source_row_count: int
    source_file_count: int
    total_alerts: int
    warning_alerts: int
    critical_alerts: int
    retrain_recommended: bool
    disable_prediction_recommended: bool
    model_usage_total: int
    model_coverage: float
    abstention_rate: float
    api_latency_ms: float


class MonitoringArtifactResponse(BaseModel):
    monitoring_run_id: str
    upload_id: str
    generated_at: str
    summary: MonitoringSummaryResponse
    data_checks: list[MonitoringCheckResponse]
    ml_checks: list[MonitoringCheckResponse]
    alerts: list[MonitoringAlertResponse]
    dashboard_metrics: list[MonitoringDashboardMetricResponse]
    override_summary: MonitoringOverrideSummaryResponse
    artifact_path: str
