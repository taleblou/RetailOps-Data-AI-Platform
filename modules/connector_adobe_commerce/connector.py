# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_adobe_commerce
# File:         connector.py
# Path:         modules/connector_adobe_commerce/connector.py
#
# Summary:      Implements adapter logic for the connector adobe commerce integration surface.
# Purpose:      Standardizes external-system interaction for the connector adobe commerce workflow.
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
#   - Main types: AdobeCommerceConnector
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, typing, core.ingestion.base.api_connector, core.ingestion.base.models, modules.connector_adobe_commerce.schemas
#   - Constraints: External-system assumptions must remain aligned with connector contracts and mapping rules.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from typing import Any

from core.ingestion.base.api_connector import BaseApiConnector
from core.ingestion.base.models import TestConnectionResult
from modules.connector_adobe_commerce.schemas import AdobeCommerceConnectorConfig

RESOURCE_ENDPOINTS = {
    "orders": "orders",
    "products": "products",
    "customers": "customers/search",
    "inventory": "inventory/source-items",
}


class AdobeCommerceConnector(BaseApiConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = AdobeCommerceConnectorConfig.model_validate(self.source.config)

    def connect(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/rest/{self.config.store_code.strip('/')}/V1"

    def default_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.config.access_token}",
        }

    def _endpoint(self) -> str:
        return RESOURCE_ENDPOINTS.get(self.config.resource, self.config.resource)

    def healthcheck_details(self) -> dict[str, Any]:
        payload = self.request_json("store/storeConfigs")
        store_count = len(payload) if isinstance(payload, list) else 0
        return {
            "base_url": self.config.base_url,
            "resource": self.config.resource,
            "store_count": store_count,
        }

    def test_connection(self) -> TestConnectionResult:
        if not self.config.base_url or not self.config.access_token:
            return TestConnectionResult(
                ok=False, message="Adobe Commerce credentials are incomplete."
            )
        return super().test_connection()

    def extract(self, cursor: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        page = max(int(cursor or 1), 1)
        page_size = min(limit or self.config.page_size, self.config.page_size)
        query: dict[str, Any] = {
            "searchCriteria[currentPage]": page,
            "searchCriteria[pageSize]": page_size,
        }
        for key, value in self.config.search_criteria.items():
            query[f"searchCriteria[{key}]"] = value
        payload = self.request_json(self._endpoint(), query=query)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        items = payload.get("items") if isinstance(payload, dict) else None
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        return []
