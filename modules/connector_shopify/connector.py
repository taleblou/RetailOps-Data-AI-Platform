# Project:      RetailOps Data & AI Platform
# Module:       modules.connector_shopify
# File:         connector.py
# Path:         modules/connector_shopify/connector.py
#
# Summary:      Implements adapter logic for the connector shopify integration surface.
# Purpose:      Standardizes external-system interaction for the connector shopify workflow.
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
#   - Main types: ShopifyConnector
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, json, typing, urllib.error, urllib.parse, urllib.request, ...
#   - Constraints: External-system assumptions must remain aligned with connector contracts and mapping rules.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import ColumnInfo, SchemaDiscoveryResult, TestConnectionResult
from modules.connector_shopify.schemas import ShopifyConnectorConfig


class ShopifyConnector(BaseConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = ShopifyConnectorConfig.model_validate(self.source.config)

    def connect(self) -> dict[str, str]:
        return {
            "store_url": self.config.store_url.rstrip("/"),
            "api_version": self.config.api_version,
            "resource": self.config.resource.strip("/"),
        }

    def _build_url(self, path: str, query: dict[str, Any] | None = None) -> str:
        base = self.connect()["store_url"]
        normalized_path = path.lstrip("/")
        url = f"{base}/admin/api/{self.config.api_version}/{normalized_path}"
        if query:
            url = f"{url}?{urlencode(query, doseq=True)}"
        return url

    def _request_json(self, path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
        request = Request(
            self._build_url(path, query),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.config.access_token,
            },
            method="GET",
        )
        with urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)

    def test_connection(self) -> TestConnectionResult:
        if not self.config.store_url or not self.config.access_token:
            return TestConnectionResult(
                ok=False,
                message="Shopify credentials are incomplete.",
            )
        try:
            payload = self._request_json("shop.json")
        except HTTPError as exc:
            return TestConnectionResult(
                ok=False,
                message=f"Shopify API returned HTTP {exc.code}.",
                details={"store_url": self.config.store_url, "resource": self.config.resource},
            )
        except URLError as exc:
            return TestConnectionResult(
                ok=False,
                message=f"Shopify API request failed: {exc.reason}",
                details={"store_url": self.config.store_url, "resource": self.config.resource},
            )
        except Exception as exc:
            return TestConnectionResult(
                ok=False,
                message=str(exc),
                details={"store_url": self.config.store_url, "resource": self.config.resource},
            )

        shop = payload.get("shop") if isinstance(payload, dict) else None
        shop_name = shop.get("name", "Unknown shop") if isinstance(shop, dict) else "Unknown shop"
        return TestConnectionResult(
            ok=True,
            message="Shopify source is reachable.",
            details={
                "store_url": self.config.store_url,
                "resource": self.config.resource,
                "shop_name": shop_name,
            },
        )

    def discover_schema(self) -> SchemaDiscoveryResult:
        rows = self.extract(limit=3)
        if not rows:
            return SchemaDiscoveryResult(columns=[], sample_rows=[])

        sample_row = rows[0]
        columns = [
            ColumnInfo(
                name=key,
                dtype=self._infer_type(value),
                position=index,
            )
            for index, (key, value) in enumerate(sample_row.items(), start=1)
        ]
        return SchemaDiscoveryResult(columns=columns, sample_rows=rows)

    def extract(
        self,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        _ = cursor
        query: dict[str, Any] = {"limit": min(limit or 50, 250)}
        payload = self._request_json(f"{self.config.resource}.json", query)
        resource_name = self.config.resource.split("/")[-1]
        rows = payload.get(resource_name)
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
        return []

    @staticmethod
    def _infer_type(value: object) -> str:
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
