# Project:      RetailOps Data & AI Platform
# Module:       core.ingestion.base
# File:         api_connector.py
# Path:         core/ingestion/base/api_connector.py
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
#   - Main types: BaseApiConnector
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, json, abc, typing, urllib.error, urllib.parse, ...
#   - Constraints: External-system assumptions must remain aligned with connector contracts and mapping rules.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import json
from abc import abstractmethod
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import ColumnInfo, SchemaDiscoveryResult, TestConnectionResult


class BaseApiConnector(BaseConnector):
    timeout_seconds = 20

    @abstractmethod
    def default_headers(self) -> dict[str, str]:
        raise NotImplementedError

    def build_url(self, path: str, query: dict[str, Any] | None = None) -> str:
        base = str(self.connect()).rstrip("/")
        normalized_path = path.lstrip("/")
        url = f"{base}/{normalized_path}" if normalized_path else base
        if query:
            url = f"{url}?{urlencode(query, doseq=True)}"
        return url

    def request_json(
        self,
        path: str,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request = Request(
            self.build_url(path, query),
            headers={**self.default_headers(), **(headers or {})},
            method="GET",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)

    def test_connection(self) -> TestConnectionResult:
        try:
            details = self.healthcheck_details()
        except HTTPError as exc:
            return TestConnectionResult(ok=False, message=f"HTTP {exc.code}")
        except URLError as exc:
            return TestConnectionResult(ok=False, message=f"Request failed: {exc.reason}")
        except Exception as exc:
            return TestConnectionResult(ok=False, message=str(exc))
        return TestConnectionResult(
            ok=True, message="Connector source is reachable.", details=details
        )

    @abstractmethod
    def healthcheck_details(self) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def infer_type(value: object) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "float"
        if isinstance(value, dict):
            return "object"
        if isinstance(value, list):
            return "array"
        text = str(value)
        if text.endswith("Z") or "T" in text:
            return "datetime"
        return "string"

    def discover_schema(self) -> SchemaDiscoveryResult:
        rows = self.extract(limit=3)
        if not rows:
            return SchemaDiscoveryResult(columns=[], sample_rows=[])
        sample_row = rows[0]
        columns = [
            ColumnInfo(name=key, dtype=self.infer_type(value), position=index)
            for index, (key, value) in enumerate(sample_row.items(), start=1)
        ]
        return SchemaDiscoveryResult(columns=columns, sample_rows=rows)
