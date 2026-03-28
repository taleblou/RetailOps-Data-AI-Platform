from __future__ import annotations

from pydantic import BaseModel, Field


class ThresholdGateResponse(BaseModel):
    name: str
    description: str
    passed: bool
    actual_value: float
    baseline_value: float | None = None
    threshold_value: float
    direction: str


class ModelVersionResponse(BaseModel):
    model_version: str
    run_id: str
    created_at: str
    source_module: str
    source_artifact: str
    stage: str
    metrics: dict[str, float] = Field(default_factory=dict)
    baseline_metrics: dict[str, float] = Field(default_factory=dict)
    calibration_error: float
    drift_score: float
    evaluation_passed: bool
    promotion_eligible: bool
    explanation_summary: str
    tags: list[str] = Field(default_factory=list)


class ModelRegistryDetailsResponse(BaseModel):
    registry_name: str
    display_name: str
    experiment_name: str
    problem_type: str
    experiment_tracking_enabled: bool
    aliases: dict[str, str] = Field(default_factory=dict)
    evaluation_contract: dict[str, object] = Field(default_factory=dict)
    threshold_gates: list[ThresholdGateResponse] = Field(default_factory=list)
    versions: list[ModelVersionResponse] = Field(default_factory=list)
    promotion_history: list[dict[str, object]] = Field(default_factory=list)
    rollback_history: list[dict[str, object]] = Field(default_factory=list)
    rollback_flow: list[str] = Field(default_factory=list)
    artifact_path: str


class ModelRegistrySummaryItemResponse(BaseModel):
    registry_name: str
    display_name: str
    champion_version: str
    challenger_version: str
    shadow_version: str
    primary_metric: str
    optimization_direction: str
    challenger_primary_metric_value: float
    challenger_primary_metric_baseline: float
    challenger_passed: bool
    challenger_promotion_eligible: bool
    last_promotion_at: str | None = None


class Phase15ModelRegistrySummaryResponse(BaseModel):
    registry_run_id: str
    generated_at: str
    experiment_tracking_enabled: bool
    alias_policy: dict[str, str] = Field(default_factory=dict)
    rollback_flow: list[str] = Field(default_factory=list)
    registries: list[ModelRegistrySummaryItemResponse] = Field(default_factory=list)
    artifact_path: str


class ModelRegistryPromotionRequest(BaseModel):
    candidate_alias: str = Field(default="challenger")


class ModelRegistryRollbackRequest(BaseModel):
    target_version: str | None = Field(default=None)
