# Project:      RetailOps Data & AI Platform
# Module:       tests.setup
# File:         test_connector_source_types.py
# Path:         tests/setup/test_connector_source_types.py
#
# Summary:      Tests dynamic connector source type exposure.
# Purpose:      Ensures setup and sources endpoints reflect enabled connectors only.
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
#   - Key APIs: test_dynamic_setup_source_types, test_dynamic_sources_types
#   - Dependencies: __future__, fastapi.testclient, core.api.main, core.config.settings
#   - Constraints: Uses isolated environment overrides and clears settings cache between cases.
#   - Compatibility: Python 3.12+ with pytest and repository test dependencies.

from __future__ import annotations

from fastapi.testclient import TestClient

from config.settings import get_settings
from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def _build_client(monkeypatch, enabled_connectors: str) -> TestClient:
    monkeypatch.setenv("ENABLED_CONNECTORS", enabled_connectors)
    get_settings.cache_clear()
    app = create_app(repository=MemoryRepository())
    return TestClient(app)


def test_dynamic_setup_source_types(monkeypatch) -> None:
    client = _build_client(monkeypatch, "csv,shopify")

    response = client.get("/api/v1/setup/source-types")
    assert response.status_code == 200, response.text

    payload = response.json()
    assert [item["source_type"] for item in payload] == ["csv", "shopify"]
    assert payload[0]["fields"]
    assert payload[1]["fields"]


def test_dynamic_sources_types(monkeypatch) -> None:
    client = _build_client(monkeypatch, "database,prestashop")

    response = client.get("/sources/types")
    assert response.status_code == 200, response.text

    payload = response.json()
    assert [item["source_type"] for item in payload] == ["database", "prestashop"]
    assert len(payload) == 2
