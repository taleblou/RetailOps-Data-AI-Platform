from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Phase20CdcBlueprintResponse(BaseModel):
    module_name: str
    phase: int
    status: str
    generated_at: str
    artifact_path: str
    connector_name: str
    source_database: str
    kafka_compatible_runtime: str
    raw_event_topic_prefix: str
    snapshot_mode: str
    replication_slot: str
    publication_name: str
    management_actions: list[str] = Field(default_factory=list)
    emitted_topics: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
    connector_properties: dict[str, Any] = Field(default_factory=dict)
