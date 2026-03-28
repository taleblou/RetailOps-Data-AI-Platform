from __future__ import annotations

from pydantic import BaseModel, Field


class LakehouseLayerResponse(BaseModel):
    layer_name: str
    purpose: str
    tables: list[str] = Field(default_factory=list)


class Phase20LakehouseBlueprintResponse(BaseModel):
    module_name: str
    phase: int
    status: str
    generated_at: str
    artifact_path: str
    catalog_type: str
    table_format: str
    object_storage: str
    layers: list[LakehouseLayerResponse] = Field(default_factory=list)
    spark_jobs: list[str] = Field(default_factory=list)
    config_templates: dict[str, str] = Field(default_factory=dict)
