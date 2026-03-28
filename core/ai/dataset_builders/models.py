from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FreshnessPolicy:
    warn_after_hours: int
    error_after_hours: int


@dataclass(slots=True)
class FeatureContract:
    name: str
    description: str
    entity: list[str]
    relation: str
    sql_file: str
    timestamp_column: str
    feature_columns: list[str]
    transformation: str
    materialization: str
    freshness: FreshnessPolicy
    null_handling: dict[str, Any]
    owner: str
    training_serving_parity: bool
    serving_join_keys: list[str]
    leakage_prevention: list[str]
    labels_relation: str | None = None
    labels_timestamp_column: str | None = None
    source_path: Path | None = None
