# Project:      RetailOps Data & AI Platform
# Module:       core.ingestion.base
# File:         registry.py
# Path:         core/ingestion/base/registry.py
#
# Summary:      Registers and resolves components for the ingestion base workflow.
# Purpose:      Provides lookup and lifecycle helpers for ingestion base implementations.
# Scope:        internal
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
#   - Main types: ConnectorRegistry, ConnectorSpec, ConnectorField
#   - Key APIs: build_default_registry, get_connector_specs,
#     resolve_enabled_connector_types
#   - Dependencies: __future__, collections.abc, dataclasses, importlib,
#     core.ingestion.base.connector, core.ingestion.base.models,
#     core.ingestion.base.raw_loader, core.ingestion.base.state_store
#   - Constraints: Internal interfaces should remain aligned with adjacent
#     modules and repository conventions.
#   - Compatibility: Python 3.12+ and repository-supported runtime dependencies.

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import SourceRecord, SourceType
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.state_store import StateStore

ConnectorFactory = Callable[[SourceRecord, StateStore, RawLoader], BaseConnector]


@dataclass(frozen=True, slots=True)
class ConnectorField:
    name: str
    label: str
    default: str = ""


@dataclass(frozen=True, slots=True)
class ConnectorSpec:
    source_type: SourceType
    label: str
    module_path: str
    class_name: str
    wizard_fields: tuple[ConnectorField, ...]

    @property
    def source_value(self) -> str:
        return self.source_type.value


def _field(name: str, label: str, default: str = "") -> ConnectorField:
    return ConnectorField(name=name, label=label, default=default)


CONNECTOR_SPECS: tuple[ConnectorSpec, ...] = (
    ConnectorSpec(
        source_type=SourceType.CSV,
        label="CSV",
        module_path="modules.connector_csv.connector",
        class_name="CsvConnector",
        wizard_fields=(
            _field("file_path", "CSV file path"),
            _field("delimiter", "Delimiter", ","),
            _field("encoding", "Encoding", "utf-8"),
        ),
    ),
    ConnectorSpec(
        source_type=SourceType.DATABASE,
        label="Database",
        module_path="modules.connector_db.connector",
        class_name="DatabaseConnector",
        wizard_fields=(
            _field("database_url", "Database URL"),
            _field("query", "SQL query", "select 1 as id"),
        ),
    ),
    ConnectorSpec(
        source_type=SourceType.SHOPIFY,
        label="Shopify",
        module_path="modules.connector_shopify.connector",
        class_name="ShopifyConnector",
        wizard_fields=(
            _field("store_url", "Shopify store URL"),
            _field("access_token", "Shopify access token"),
            _field("api_version", "API version", "2024-01"),
            _field("resource", "Resource", "orders"),
        ),
    ),
    ConnectorSpec(
        source_type=SourceType.WOOCOMMERCE,
        label="WooCommerce",
        module_path="modules.connector_woocommerce.connector",
        class_name="WooCommerceConnector",
        wizard_fields=(
            _field("store_url", "WooCommerce store URL"),
            _field("consumer_key", "Consumer key"),
            _field("consumer_secret", "Consumer secret"),
            _field("api_version", "API version", "wc/v3"),
            _field("resource", "Resource", "orders"),
        ),
    ),
    ConnectorSpec(
        source_type=SourceType.ADOBE_COMMERCE,
        label="Adobe Commerce",
        module_path="modules.connector_adobe_commerce.connector",
        class_name="AdobeCommerceConnector",
        wizard_fields=(
            _field("base_url", "Adobe Commerce base URL"),
            _field("store_code", "Store code", "default"),
            _field("access_token", "Access token"),
            _field("resource", "Resource", "orders"),
        ),
    ),
    ConnectorSpec(
        source_type=SourceType.BIGCOMMERCE,
        label="BigCommerce",
        module_path="modules.connector_bigcommerce.connector",
        class_name="BigCommerceConnector",
        wizard_fields=(
            _field("api_root", "API root", "https://api.bigcommerce.com/stores"),
            _field("store_hash", "Store hash"),
            _field("access_token", "Access token"),
            _field("api_version", "API version", "v3"),
            _field("resource", "Resource", "orders"),
        ),
    ),
    ConnectorSpec(
        source_type=SourceType.PRESTASHOP,
        label="PrestaShop",
        module_path="modules.connector_prestashop.connector",
        class_name="PrestaShopConnector",
        wizard_fields=(
            _field("base_url", "PrestaShop base URL"),
            _field("api_key", "API key"),
            _field("resource", "Resource", "orders"),
        ),
    ),
)

CONNECTOR_SPEC_MAP: dict[SourceType, ConnectorSpec] = {
    item.source_type: item for item in CONNECTOR_SPECS
}


class ConnectorRegistry:
    def __init__(self) -> None:
        self._registry: dict[SourceType, ConnectorFactory] = {}

    def register(self, source_type: SourceType, factory: ConnectorFactory) -> None:
        self._registry[source_type] = factory

    def registered_source_types(self) -> list[SourceType]:
        return list(self._registry.keys())

    def has_source_type(self, source_type: SourceType) -> bool:
        return source_type in self._registry

    def create(
        self,
        source: SourceRecord,
        state_store: StateStore,
        raw_loader: RawLoader,
    ) -> BaseConnector:
        if source.type not in self._registry:
            raise KeyError(
                "No connector is enabled for source type: "
                f"{source.type}. Update ENABLED_CONNECTORS or the install profile."
            )
        return self._registry[source.type](source, state_store, raw_loader)


def _normalize_source_type(value: Any) -> SourceType | None:
    if isinstance(value, SourceType):
        return value
    try:
        return SourceType(str(value).strip().lower())
    except ValueError:
        return None


def resolve_enabled_connector_types(
    enabled_connectors: Iterable[SourceType | str] | None = None,
) -> list[SourceType]:
    if enabled_connectors is None:
        return [SourceType.CSV]

    seen: set[SourceType] = set()
    resolved: list[SourceType] = []
    for item in enabled_connectors:
        source_type = _normalize_source_type(item)
        if source_type is None or source_type in seen:
            continue
        seen.add(source_type)
        resolved.append(source_type)
    if not resolved:
        return [SourceType.CSV]
    return resolved


def get_connector_specs(
    enabled_connectors: Iterable[SourceType | str] | None = None,
) -> list[ConnectorSpec]:
    enabled_types = resolve_enabled_connector_types(enabled_connectors)
    return [CONNECTOR_SPEC_MAP[item] for item in enabled_types if item in CONNECTOR_SPEC_MAP]


def _load_connector_class(spec: ConnectorSpec) -> type[BaseConnector]:
    module = import_module(spec.module_path)
    candidate = getattr(module, spec.class_name, None)
    if candidate is None:
        raise RuntimeError(f"Expected connector class '{spec.class_name}' in '{spec.module_path}'.")
    return candidate


def build_default_registry(
    enabled_connectors: Iterable[SourceType | str] | None = None,
) -> ConnectorRegistry:
    registry = ConnectorRegistry()
    for spec in get_connector_specs(enabled_connectors):
        connector_class = _load_connector_class(spec)
        registry.register(
            spec.source_type,
            lambda source, state_store, raw_loader, cls=connector_class: cls(
                source,
                state_store,
                raw_loader,
            ),
        )
    return registry
