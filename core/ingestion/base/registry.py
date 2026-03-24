from __future__ import annotations

from collections.abc import Callable

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import SourceRecord, SourceType
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.state_store import StateStore

ConnectorFactory = Callable[[SourceRecord, StateStore, RawLoader], BaseConnector]


class ConnectorRegistry:
    def __init__(self) -> None:
        self._registry: dict[SourceType, ConnectorFactory] = {}

    def register(self, source_type: SourceType, factory: ConnectorFactory) -> None:
        self._registry[source_type] = factory

    def create(
        self,
        source: SourceRecord,
        state_store: StateStore,
        raw_loader: RawLoader,
    ) -> BaseConnector:
        if source.type not in self._registry:
            raise KeyError(f"No connector registered for source type: {source.type}")
        return self._registry[source.type](source, state_store, raw_loader)


def build_default_registry() -> ConnectorRegistry:
    from modules.connector_csv.connector import CsvConnector
    from modules.connector_db.connector import DatabaseConnector
    from modules.connector_shopify.connector import ShopifyConnector

    registry = ConnectorRegistry()
    registry.register(
        SourceType.CSV,
        lambda source, state_store, raw_loader: CsvConnector(
            source,
            state_store,
            raw_loader,
        ),
    )
    registry.register(
        SourceType.DATABASE,
        lambda source, state_store, raw_loader: DatabaseConnector(
            source,
            state_store,
            raw_loader,
        ),
    )
    registry.register(
        SourceType.SHOPIFY,
        lambda source, state_store, raw_loader: ShopifyConnector(
            source,
            state_store,
            raw_loader,
        ),
    )
    return registry
