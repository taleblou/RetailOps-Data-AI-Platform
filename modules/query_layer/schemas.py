from __future__ import annotations

from pydantic import BaseModel, Field


class QueryCatalogResponse(BaseModel):
    name: str
    connector_name: str
    target: str


class Phase20QueryLayerBlueprintResponse(BaseModel):
    module_name: str
    phase: int
    status: str
    generated_at: str
    artifact_path: str
    engine: str
    catalogs: list[QueryCatalogResponse] = Field(default_factory=list)
    federation_queries: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
