from __future__ import annotations

from typing import Any

from core.ingestion.base.api_connector import BaseApiConnector
from core.ingestion.base.models import TestConnectionResult
from modules.connector_woocommerce.schemas import WooCommerceConnectorConfig


class WooCommerceConnector(BaseApiConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = WooCommerceConnectorConfig.model_validate(self.source.config)

    def connect(self) -> str:
        return f"{self.config.store_url.rstrip('/')}/wp-json/{self.config.api_version.strip('/')}"

    def default_headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}

    def _auth_query(self) -> dict[str, Any]:
        return {
            "consumer_key": self.config.consumer_key,
            "consumer_secret": self.config.consumer_secret,
        }

    def healthcheck_details(self) -> dict[str, Any]:
        payload = self.request_json("system_status", query=self._auth_query())
        environment = payload.get("environment") if isinstance(payload, dict) else {}
        return {
            "store_url": self.config.store_url,
            "resource": self.config.resource,
            "wordpress_version": environment.get("version")
            if isinstance(environment, dict)
            else "",
        }

    def test_connection(self) -> TestConnectionResult:
        if (
            not self.config.store_url
            or not self.config.consumer_key
            or not self.config.consumer_secret
        ):
            return TestConnectionResult(ok=False, message="WooCommerce credentials are incomplete.")
        return super().test_connection()

    def extract(self, cursor: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        page = int(cursor or 1)
        per_page = min(limit or self.config.page_size, self.config.page_size)
        query: dict[str, Any] = {**self._auth_query(), "page": page, "per_page": per_page}
        if self.config.default_status:
            query["status"] = self.config.default_status
        payload = self.request_json(self.config.resource.strip("/"), query=query)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []
