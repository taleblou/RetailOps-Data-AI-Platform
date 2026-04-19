# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_prestashop
# File:         connector.py
# Path:         modules/connector_prestashop/connector.py
#
# Summary:      Implements adapter logic for the connector prestashop integration surface.
# Purpose:      Standardizes external-system interaction for the connector prestashop workflow.
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
#   - Main types: PrestaShopConnector
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, xml.etree.ElementTree, typing, urllib.request, core.ingestion.base.connector, core.ingestion.base.models, ...
#   - Constraints: External-system assumptions must remain aligned with connector contracts and mapping rules.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.request import Request, urlopen

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import ColumnInfo, SchemaDiscoveryResult, TestConnectionResult
from modules.connector_prestashop.schemas import PrestaShopConnectorConfig


class PrestaShopConnector(BaseConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = PrestaShopConnectorConfig.model_validate(self.source.config)

    def connect(self) -> str:
        return self.config.base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/xml",
        }

    def _request_xml(self, path: str, query: dict[str, Any] | None = None) -> ET.Element:
        base = f"{self.connect()}/api/{path.strip('/')}"
        if query:
            query_parts = [f"{key}={value}" for key, value in query.items()]
            base = f"{base}?{'&'.join(query_parts)}"
        request = Request(base, headers=self._headers(), method="GET")
        with urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
        return ET.fromstring(payload)

    def test_connection(self) -> TestConnectionResult:
        if not self.config.base_url or not self.config.api_key:
            return TestConnectionResult(ok=False, message="PrestaShop credentials are incomplete.")
        try:
            root = self._request_xml("", {"ws_key": self.config.api_key})
        except Exception as exc:
            return TestConnectionResult(ok=False, message=str(exc))
        return TestConnectionResult(
            ok=True,
            message="PrestaShop source is reachable.",
            details={"resource": self.config.resource, "root_tag": root.tag},
        )

    def discover_schema(self) -> SchemaDiscoveryResult:
        rows = self.extract(limit=3)
        if not rows:
            return SchemaDiscoveryResult(columns=[], sample_rows=[])
        sample_row = rows[0]
        columns = [
            ColumnInfo(name=key, dtype="string", position=index)
            for index, key in enumerate(sample_row.keys(), start=1)
        ]
        return SchemaDiscoveryResult(columns=columns, sample_rows=rows)

    def extract(self, cursor: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        query = {
            "display": self.config.display,
            "limit": f"{cursor or 0},{min(limit or self.config.page_size, self.config.page_size)}",
            "output_format": "JSON",
            "ws_key": self.config.api_key,
        }
        try:
            root = self._request_xml(self.config.resource.strip("/"), query=query)
            rows = self._xml_rows(root)
            if limit is not None:
                return rows[:limit]
            return rows
        except Exception:
            return []

    def _xml_rows(self, root: ET.Element) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for child in root:
            if len(child) == 0:
                continue
            row = {grandchild.tag: (grandchild.text or "") for grandchild in child}
            if row:
                rows.append(row)
        return rows
