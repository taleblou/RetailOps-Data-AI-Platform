from __future__ import annotations

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import ColumnInfo, SchemaDiscoveryResult, TestConnectionResult
from modules.connector_shopify.schemas import ShopifyConnectorConfig


class ShopifyConnector(BaseConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = ShopifyConnectorConfig.model_validate(self.source.config)

    def connect(self) -> dict[str, str]:
        return {
            "store_url": self.config.store_url,
            "api_version": self.config.api_version,
            "resource": self.config.resource,
        }

    def test_connection(self) -> TestConnectionResult:
        if not self.config.store_url or not self.config.access_token:
            return TestConnectionResult(
                ok=False,
                message="Shopify credentials are incomplete.",
            )
        return TestConnectionResult(
            ok=False,
            message=(
                "Shopify HTTP sync is intentionally left as a phase 5 skeleton. "
                "The contract and configuration are ready."
            ),
            details=self.connect(),
        )

    def discover_schema(self) -> SchemaDiscoveryResult:
        columns = [
            ColumnInfo(name="id", dtype="integer", position=1),
            ColumnInfo(name="created_at", dtype="datetime", position=2),
            ColumnInfo(name="email", dtype="string", position=3),
            ColumnInfo(name="financial_status", dtype="string", position=4),
            ColumnInfo(name="fulfillment_status", dtype="string", position=5),
            ColumnInfo(name="total_price", dtype="float", position=6),
        ]
        return SchemaDiscoveryResult(columns=columns, sample_rows=[])

    def extract(
        self,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        _ = cursor
        _ = limit
        return []
