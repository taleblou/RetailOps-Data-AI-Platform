from __future__ import annotations

from pydantic import BaseModel, Field


class FeatureViewResponse(BaseModel):
    name: str
    entity: str
    ttl_days: int
    owner: str


class Phase20FeatureStoreBlueprintResponse(BaseModel):
    module_name: str
    phase: int
    status: str
    generated_at: str
    artifact_path: str
    engine: str
    offline_store: str
    online_store: str
    feature_views: list[FeatureViewResponse] = Field(default_factory=list)
    materialization_jobs: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
