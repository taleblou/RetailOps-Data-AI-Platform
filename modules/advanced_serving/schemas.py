from __future__ import annotations

from pydantic import BaseModel, Field


class AdvancedServingServiceResponse(BaseModel):
    name: str
    model_alias: str
    deployment_mode: str


class Phase20AdvancedServingBlueprintResponse(BaseModel):
    module_name: str
    phase: int
    status: str
    generated_at: str
    artifact_path: str
    platform: str
    services: list[AdvancedServingServiceResponse] = Field(default_factory=list)
    shadow_deployments: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
