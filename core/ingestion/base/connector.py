# Project:      RetailOps Data & AI Platform
# Module:       core.ingestion.base
# File:         connector.py
# Path:         core/ingestion/base/connector.py
#
# Summary:      Implements adapter logic for the ingestion base integration surface.
# Purpose:      Standardizes external-system interaction for the ingestion base workflow.
# Scope:        adapter
# Status:       stable
#
# Author(s):    Morteza Taleblou
# Website:      https://taleblou.ir/
# Repository:   https://github.com/taleblou/RetailOps-Data-AI-Platform
#
# License:      Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
# Copyright:    (c) 2025 Morteza Taleblou
#
# Notes:
#   - Main types: BaseConnector
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, abc, typing, core.ingestion.base.mapper, core.ingestion.base.models, core.ingestion.base.raw_loader, ...
#   - Constraints: External-system assumptions must remain aligned with connector contracts and mapping rules.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.ingestion.base.mapper import ColumnMapper
from core.ingestion.base.models import (
    ImportResult,
    MappingResult,
    SchemaDiscoveryResult,
    SourceRecord,
    TestConnectionResult,
    ValidationResult,
)
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.state_store import StateStore
from core.ingestion.base.validator import DataValidator


class BaseConnector(ABC):
    def __init__(
        self,
        source: SourceRecord,
        state_store: StateStore,
        raw_loader: RawLoader,
        mapper: ColumnMapper | None = None,
        validator: DataValidator | None = None,
    ) -> None:
        self.source = source
        self.state_store = state_store
        self.raw_loader = raw_loader
        self.mapper = mapper or ColumnMapper()
        self.validator = validator or DataValidator()

    @abstractmethod
    def connect(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def test_connection(self) -> TestConnectionResult:
        raise NotImplementedError

    @abstractmethod
    def discover_schema(self) -> SchemaDiscoveryResult:
        raise NotImplementedError

    @abstractmethod
    def extract(
        self,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def map_columns(
        self,
        rows: list[dict[str, Any]],
        explicit_mapping: dict[str, str] | None = None,
        required_columns: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], MappingResult]:
        source_columns = list(rows[0].keys()) if rows else []
        mapping = self.mapper.build_mapping(
            source_columns,
            explicit_mapping=explicit_mapping,
            required_columns=required_columns,
        )
        return self.mapper.apply_mapping(rows, mapping), mapping

    def validate(
        self,
        rows: list[dict[str, Any]],
        required_columns: list[str] | None = None,
        type_hints: dict[str, str] | None = None,
        unique_key_columns: list[str] | None = None,
    ) -> ValidationResult:
        return self.validator.validate(
            rows,
            required_columns=required_columns,
            type_hints=type_hints,
            unique_key_columns=unique_key_columns,
        )

    def load_raw(self, import_job_id: int, rows: list[dict[str, Any]]) -> int:
        return self.raw_loader.load(self.source.source_id, import_job_id, rows)

    def run_import(
        self,
        import_job_id: int,
        sync_run_id: int,
        explicit_mapping: dict[str, str] | None = None,
        required_columns: list[str] | None = None,
        type_hints: dict[str, str] | None = None,
        unique_key_columns: list[str] | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> ImportResult:
        self.connect()
        self.discover_schema()
        extracted_rows = self.extract(cursor=cursor, limit=limit)
        mapped_rows, mapping = self.map_columns(
            extracted_rows,
            explicit_mapping=explicit_mapping,
            required_columns=required_columns,
        )

        if mapping.missing_required:
            message = f"Missing required mapped columns: {mapping.missing_required}"
            self.state_store.save_failure(self.source.source_id, cursor, message)
            raise ValueError(message)

        validation = self.validate(
            mapped_rows,
            required_columns=required_columns,
            type_hints=type_hints,
            unique_key_columns=unique_key_columns,
        )
        if not validation.valid:
            message = validation.errors[0].message
            self.state_store.save_failure(self.source.source_id, cursor, message)
            raise ValueError(message)

        rows_loaded = self.load_raw(import_job_id, mapped_rows)
        state = self.state_store.save_success(
            self.source.source_id,
            str(rows_loaded),
            rows_loaded,
        )
        return ImportResult(
            source_id=self.source.source_id,
            import_job_id=import_job_id,
            sync_run_id=sync_run_id,
            rows_extracted=len(extracted_rows),
            rows_loaded=rows_loaded,
            mapping=mapping,
            validation=validation,
            state=state,
        )
