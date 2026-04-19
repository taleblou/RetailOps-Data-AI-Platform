# Project:      RetailOps Data & AI Platform
# Module:       tests.ingestion
# File:         test_platform_connectors.py
# Path:         tests/ingestion/test_platform_connectors.py
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
#   - Key APIs: test_woocommerce_connector_extracts_rows_with_mocked_request, test_adobe_connector_extracts_items_payload, test_bigcommerce_connector_extracts_data_payload
#   - Dependencies: __future__, datetime, core.ingestion.base.models, core.ingestion.base.raw_loader, core.ingestion.base.repository, core.ingestion.base.state_store, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

from datetime import UTC, datetime

from core.ingestion.base.models import SourceRecord, SourceStatus, SourceType
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.repository import MemoryRepository
from core.ingestion.base.state_store import StateStore
from modules.connector_adobe_commerce.connector import AdobeCommerceConnector
from modules.connector_bigcommerce.connector import BigCommerceConnector
from modules.connector_woocommerce.connector import WooCommerceConnector


def _source(source_type: SourceType, config: dict[str, object]) -> SourceRecord:
    return SourceRecord(
        source_id=1,
        name="platform-source",
        type=source_type,
        status=SourceStatus.CREATED,
        config=config,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


def test_woocommerce_connector_extracts_rows_with_mocked_request(monkeypatch) -> None:
    connector = WooCommerceConnector(
        source=_source(
            SourceType.WOOCOMMERCE,
            {
                "store_url": "https://example.test",
                "consumer_key": "ck",
                "consumer_secret": "cs",
                "resource": "orders",
            },
        ),
        state_store=StateStore(MemoryRepository()),
        raw_loader=RawLoader(MemoryRepository()),
    )

    monkeypatch.setattr(
        connector,
        "request_json",
        lambda path, query=None, headers=None: [
            {"id": 1001, "status": "processing", "total": "19.99"}
        ],
    )
    rows = connector.extract(limit=5)
    schema = connector.discover_schema()
    assert rows[0]["id"] == 1001
    assert schema.columns[0].name == "id"


def test_adobe_connector_extracts_items_payload(monkeypatch) -> None:
    connector = AdobeCommerceConnector(
        source=_source(
            SourceType.ADOBE_COMMERCE,
            {
                "base_url": "https://commerce.example.test",
                "access_token": "token",
                "resource": "orders",
            },
        ),
        state_store=StateStore(MemoryRepository()),
        raw_loader=RawLoader(MemoryRepository()),
    )
    monkeypatch.setattr(
        connector,
        "request_json",
        lambda path, query=None, headers=None: {"items": [{"entity_id": 10, "status": "complete"}]},
    )
    rows = connector.extract(limit=5)
    assert rows[0]["entity_id"] == 10


def test_bigcommerce_connector_extracts_data_payload(monkeypatch) -> None:
    connector = BigCommerceConnector(
        source=_source(
            SourceType.BIGCOMMERCE,
            {
                "store_hash": "abc123",
                "access_token": "token",
                "resource": "orders",
            },
        ),
        state_store=StateStore(MemoryRepository()),
        raw_loader=RawLoader(MemoryRepository()),
    )
    monkeypatch.setattr(
        connector,
        "request_json",
        lambda path, query=None, headers=None: {
            "data": [{"id": 11, "status": "awaiting_fulfillment"}]
        },
    )
    rows = connector.extract(limit=5)
    assert rows[0]["id"] == 11
