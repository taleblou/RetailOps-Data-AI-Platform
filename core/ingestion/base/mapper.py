# Project:      RetailOps Data & AI Platform
# Module:       core.ingestion.base
# File:         mapper.py
# Path:         core/ingestion/base/mapper.py
#
# Summary:      Maps source structures used by the ingestion base workflow.
# Purpose:      Normalizes source fields and structures for ingestion base processing.
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
#   - Main types: ColumnMapper
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, typing, core.ingestion.base.models
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from typing import Any

from core.ingestion.base.models import ColumnMapping, MappingResult

CANONICAL_ALIASES: dict[str, list[str]] = {
    "order_id": ["order_id", "orderid", "id", "order number", "order_no"],
    "order_date": ["order_date", "orderdate", "created_at", "date", "ordered_at"],
    "customer_id": ["customer_id", "customerid", "client_id", "buyer_id"],
    "product_id": ["product_id", "productid", "item_id"],
    "sku": ["sku", "product_code", "productcode", "item_sku"],
    "quantity": ["quantity", "qty", "units"],
    "unit_price": ["unit_price", "price", "price_each", "unitprice"],
    "shipment_status": [
        "shipment_status",
        "shipping_status",
        "delivery_status",
    ],
    "store_code": ["store_code", "store", "branch_code"],
}


class ColumnMapper:
    def __init__(self, aliases: dict[str, list[str]] | None = None) -> None:
        self.aliases = aliases or CANONICAL_ALIASES

    @staticmethod
    def normalize_name(name: str) -> str:
        cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        return cleaned.strip("_")

    def build_mapping(
        self,
        source_columns: list[str],
        explicit_mapping: dict[str, str] | None = None,
        required_columns: list[str] | None = None,
    ) -> MappingResult:
        explicit_mapping = explicit_mapping or {}
        required_columns = required_columns or []
        normalized_columns = {self.normalize_name(column): column for column in source_columns}
        mappings: list[ColumnMapping] = []
        aliases_applied: dict[str, str] = {}
        used_sources: set[str] = set()

        for target, source in explicit_mapping.items():
            if source in source_columns:
                used_sources.add(source)
                mappings.append(
                    ColumnMapping(
                        source=source,
                        target=target,
                        required=target in required_columns,
                    )
                )

        for canonical, aliases in self.aliases.items():
            if any(item.target == canonical for item in mappings):
                continue
            for alias in aliases:
                normalized_alias = self.normalize_name(alias)
                if normalized_alias not in normalized_columns:
                    continue
                original_name = normalized_columns[normalized_alias]
                if original_name in used_sources:
                    continue
                used_sources.add(original_name)
                aliases_applied[original_name] = canonical
                mappings.append(
                    ColumnMapping(
                        source=original_name,
                        target=canonical,
                        required=canonical in required_columns,
                    )
                )
                break

        mapped_targets = {item.target for item in mappings}
        missing_required = [column for column in required_columns if column not in mapped_targets]
        unmapped_source_columns = [
            column for column in source_columns if column not in used_sources
        ]
        return MappingResult(
            mappings=mappings,
            missing_required=missing_required,
            unmapped_source_columns=unmapped_source_columns,
            aliases_applied=aliases_applied,
        )

    def apply_mapping(
        self,
        rows: list[dict[str, Any]],
        mapping_result: MappingResult,
    ) -> list[dict[str, Any]]:
        if not rows:
            return []
        mapping_dict = {item.source: item.target for item in mapping_result.mappings}
        return [
            {target: row.get(source) for source, target in mapping_dict.items()} for row in rows
        ]
