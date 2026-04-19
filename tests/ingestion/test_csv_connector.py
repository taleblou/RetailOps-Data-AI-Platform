# Project:      RetailOps Data & AI Platform
# Module:       tests.ingestion
# File:         test_csv_connector.py
# Path:         tests/ingestion/test_csv_connector.py
#
# Summary:      Contains automated tests for the ingestion workflows and behaviors.
# Purpose:      Validates ingestion behavior and protects the repository against regressions.
# Scope:        test
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
#   - Main types: None.
#   - Key APIs: build_source, test_csv_connector_discovers_schema_and_extracts_rows
#   - Dependencies: datetime, pathlib, core.ingestion.base.models, core.ingestion.base.raw_loader, core.ingestion.base.repository, core.ingestion.base.state_store, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from datetime import UTC, datetime
from pathlib import Path

from core.ingestion.base.models import SourceRecord, SourceStatus, SourceType
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.repository import MemoryRepository
from core.ingestion.base.state_store import StateStore
from modules.connector_csv.connector import CsvConnector


def build_source(csv_path: Path) -> SourceRecord:
    return SourceRecord(
        source_id=1,
        name="orders-csv",
        type=SourceType.CSV,
        status=SourceStatus.CREATED,
        config={"file_path": str(csv_path)},
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


def test_csv_connector_discovers_schema_and_extracts_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text(
        "order_id,qty,price_each\n1001,2,9.99\n1002,3,14.50\n",
        encoding="utf-8",
    )
    repository = MemoryRepository()
    connector = CsvConnector(
        source=build_source(csv_path),
        state_store=StateStore(repository),
        raw_loader=RawLoader(repository),
    )
    schema = connector.discover_schema()
    rows = connector.extract()
    assert [column.name for column in schema.columns] == [
        "order_id",
        "qty",
        "price_each",
    ]
    assert len(rows) == 2
    assert rows[0]["order_id"] == "1001"
