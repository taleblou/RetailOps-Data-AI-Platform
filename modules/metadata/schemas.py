from __future__ import annotations

from pydantic import BaseModel, Field


class MetadataWorkflowResponse(BaseModel):
    name: str
    source_type: str
    output: str


class Phase20MetadataBlueprintResponse(BaseModel):
    module_name: str
    phase: int
    status: str
    generated_at: str
    artifact_path: str
    platform: str
    lineage_enabled: bool
    workflows: list[MetadataWorkflowResponse] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
