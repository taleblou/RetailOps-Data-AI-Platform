from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    CSV = "csv"
    SHOPIFY = "shopify"
    DATABASE = "database"
    WOOCOMMERCE = "woocommerce"
    ADOBE_COMMERCE = "adobe_commerce"
    BIGCOMMERCE = "bigcommerce"
    PRESTASHOP = "prestashop"


class SourceStatus(StrEnum):
    CREATED = "created"
    TESTED = "tested"
    READY = "ready"
    RUNNING = "running"
    FAILED = "failed"


class ColumnInfo(BaseModel):
    name: str
    dtype: str
    nullable: bool = True
    position: int | None = None


class SourceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: SourceType
    config: dict[str, Any] = Field(default_factory=dict)


class SourceRecord(BaseModel):
    source_id: int
    name: str
    type: SourceType
    status: SourceStatus
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TestConnectionResult(BaseModel):
    ok: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SchemaDiscoveryResult(BaseModel):
    columns: list[ColumnInfo]
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count_estimate: int | None = None


class ColumnMapping(BaseModel):
    source: str
    target: str
    required: bool = False


class MappingResult(BaseModel):
    mappings: list[ColumnMapping]
    missing_required: list[str] = Field(default_factory=list)
    unmapped_source_columns: list[str] = Field(default_factory=list)
    aliases_applied: dict[str, str] = Field(default_factory=dict)


class ValidationIssue(BaseModel):
    level: Literal["error", "warning"]
    code: str
    message: str
    column: str | None = None
    row_number: int | None = None
    value: Any | None = None


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)


class ConnectorState(BaseModel):
    source_id: int
    last_sync_at: datetime | None = None
    cursor_value: str | None = None
    error_count: int = 0
    retry_count: int = 0
    last_error: str | None = None
    last_run_status: str | None = None


class ImportRequest(BaseModel):
    mapping: dict[str, str] = Field(default_factory=dict)
    required_columns: list[str] = Field(default_factory=list)
    type_hints: dict[str, str] = Field(default_factory=dict)
    unique_key_columns: list[str] = Field(default_factory=list)
    cursor: str | None = None
    limit: int | None = None
    sync_mode: str = "full"


class ImportResult(BaseModel):
    source_id: int
    import_job_id: int
    sync_run_id: int
    rows_extracted: int
    rows_loaded: int
    mapping: MappingResult
    validation: ValidationResult
    state: ConnectorState


class SourceErrorRecord(BaseModel):
    source_id: int
    error_type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SourceStatusResponse(BaseModel):
    source: SourceRecord
    state: ConnectorState | None = None
