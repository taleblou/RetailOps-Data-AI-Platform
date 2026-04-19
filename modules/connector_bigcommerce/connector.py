# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_bigcommerce
# File:         connector.py
# Path:         modules/connector_bigcommerce/connector.py
#
# Summary:      Implements adapter logic for the connector bigcommerce integration surface.
# Purpose:      Standardizes external-system interaction for the connector bigcommerce workflow.
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
#   - Main types: BigCommerceConnector
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, typing, core.ingestion.base.api_connector, core.ingestion.base.models, modules.connector_bigcommerce.schemas
#   - Constraints: External-system assumptions must remain aligned with connector contracts and mapping rules.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from typing import Any

from core.ingestion.base.api_connector import BaseApiConnector
from core.ingestion.base.models import TestConnectionResult
from modules.connector_bigcommerce.schemas import BigCommerceConnectorConfig


class BigCommerceConnector(BaseApiConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = BigCommerceConnectorConfig.model_validate(self.source.config)

    def connect(self) -> str:
        return f"{self.config.api_root.rstrip('/')}/{self.config.store_hash}/v3"

    def default_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "X-Auth-Token": self.config.access_token,
        }

    def healthcheck_details(self) -> dict[str, Any]:
        payload = self.request_json("store")
        data = payload.get("data") if isinstance(payload, dict) else {}
        return {
            "store_hash": self.config.store_hash,
            "resource": self.config.resource,
            "store_name": data.get("name") if isinstance(data, dict) else "",
        }

    def test_connection(self) -> TestConnectionResult:
        if not self.config.store_hash or not self.config.access_token:
            return TestConnectionResult(ok=False, message="BigCommerce credentials are incomplete.")
        return super().test_connection()

    def extract(self, cursor: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        page = max(int(cursor or 1), 1)
        page_size = min(limit or self.config.page_size, self.config.page_size)
        query = {"page": page, "limit": page_size}
        payload = self.request_json(self.config.resource.strip("/"), query=query)
        rows = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
        return []
