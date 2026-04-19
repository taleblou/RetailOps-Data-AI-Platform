# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_csv
# File:         connector.py
# Path:         modules/connector_csv/connector.py
#
# Summary:      Implements adapter logic for the connector csv integration surface.
# Purpose:      Standardizes external-system interaction for the connector csv workflow.
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
#   - Main types: CsvConnector
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, csv, pathlib, typing, core.ingestion.base.connector, core.ingestion.base.models, ...
#   - Constraints: External-system assumptions must remain aligned with connector contracts and mapping rules.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import ColumnInfo, SchemaDiscoveryResult, TestConnectionResult
from modules.connector_csv.schemas import CsvConnectorConfig


class CsvConnector(BaseConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = CsvConnectorConfig.model_validate(self.source.config)

    def connect(self) -> Path:
        path = Path(self.config.file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file does not exist: {path}")
        return path

    def test_connection(self) -> TestConnectionResult:
        try:
            path = self.connect()
            with path.open("r", encoding=self.config.encoding, newline="") as handle:
                preview = handle.readline().strip()
            return TestConnectionResult(
                ok=True,
                message="CSV source is reachable.",
                details={"path": str(path), "preview": preview},
            )
        except Exception as exc:
            return TestConnectionResult(ok=False, message=str(exc), details={})

    def discover_schema(self) -> SchemaDiscoveryResult:
        path = self.connect()
        with path.open("r", encoding=self.config.encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self.config.delimiter)
            sample_rows: list[dict[str, Any]] = []
            for index, row in enumerate(reader, start=1):
                sample_rows.append(row)
                if index >= 3:
                    break
            fieldnames = reader.fieldnames or []

        columns = [
            ColumnInfo(
                name=column,
                dtype=self._infer_column_type(sample_rows, column),
                position=index,
            )
            for index, column in enumerate(fieldnames, start=1)
        ]
        return SchemaDiscoveryResult(columns=columns, sample_rows=sample_rows)

    def extract(
        self,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        _ = cursor
        path = self.connect()
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding=self.config.encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self.config.delimiter)
            for index, row in enumerate(reader, start=1):
                rows.append(dict(row))
                if limit is not None and index >= limit:
                    break
        return rows

    @staticmethod
    def _infer_column_type(rows: list[dict[str, Any]], column_name: str) -> str:
        values = [row.get(column_name) for row in rows if row.get(column_name) not in (None, "")]
        if not values:
            return "string"
        if all(str(value).isdigit() for value in values):
            return "integer"
        try:
            for value in values:
                float(str(value))
        except ValueError:
            return "string"
        return "float"
