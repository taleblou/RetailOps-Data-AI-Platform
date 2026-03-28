from __future__ import annotations

from pydantic import BaseModel, Field


class StreamingTopicResponse(BaseModel):
    name: str
    partitions: int
    retention_hours: int
    cleanup_policy: str


class StreamingProcessorResponse(BaseModel):
    name: str
    input_topic: str
    output_topic: str
    responsibility: str


class Phase20StreamingBlueprintResponse(BaseModel):
    module_name: str
    phase: int
    status: str
    generated_at: str
    artifact_path: str
    runtime: str
    consumer_groups: list[str] = Field(default_factory=list)
    topics: list[StreamingTopicResponse] = Field(default_factory=list)
    processors: list[StreamingProcessorResponse] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
