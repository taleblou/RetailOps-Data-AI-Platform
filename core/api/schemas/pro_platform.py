from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProPlatformSummaryResponse(BaseModel):
    phase: int
    platform_name: str
    module_count: int
    artifact_root: str
    modules: dict[str, dict[str, Any]] = Field(default_factory=dict)
