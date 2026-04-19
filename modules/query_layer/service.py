# Project:      RetailOps Data & AI Platform
# Module:       modules.query_layer
# File:         service.py
# Path:         modules/query_layer/service.py
#
# Summary:      Builds deployment-ready query-layer bundles for the Pro platform.
# Purpose:      Packages Trino catalogs, federation SQL, and compose metadata into reusable query-layer artifacts.
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
#   - Main types: None.
#   - Key APIs: build_query_layer_artifact
#   - Dependencies: __future__, pathlib, typing, modules.common.platform_extensions
#   - Constraints: Catalog names should remain stable because dashboards and metadata workflows depend on them.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from pathlib import Path
from typing import Any

from modules.common.platform_extensions import (
    bool_to_status,
    read_cached_payload,
    summarize_compose,
    utc_now_iso,
    write_bundle_files,
    write_payload,
)

QUERY_LAYER_VERSION = "query-layer-v2"


def _read_properties(path: Path) -> dict[str, str]:
    properties: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        properties[key.strip()] = value.strip()
    return properties


def build_query_layer_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "platform_extensions_query_layer_bundle.json"
    cached = read_cached_payload(artifact_path, refresh)
    if cached is not None:
        return cached

    module_root = Path(__file__).resolve().parent
    repo_root = module_root.parents[1]
    compose_summary = summarize_compose(repo_root / "compose" / "compose.query.yaml")
    postgres_catalog_path = module_root / "config" / "catalogs" / "postgres.properties"
    iceberg_catalog_path = module_root / "config" / "catalogs" / "iceberg.properties"
    postgres_catalog = _read_properties(postgres_catalog_path)
    iceberg_catalog = _read_properties(iceberg_catalog_path)
    query_examples = (module_root / "sql" / "federation_queries.sql").read_text(encoding="utf-8")
    readiness_checks = {
        "compose_overlay_exists": True,
        "postgres_catalog_defined": bool(postgres_catalog),
        "iceberg_catalog_defined": bool(iceberg_catalog),
        "query_examples_present": bool(query_examples.strip()),
    }
    bootstrap_commands = [
        "docker compose -f compose/compose.core.yaml -f compose/compose.query.yaml up -d",
        'trino --execute "SHOW CATALOGS"',
        "trino --file modules/query_layer/sql/federation_queries.sql",
    ]
    health_checks = [
        "Trino should list postgres and iceberg catalogs",
        "federated queries should return joined retail facts",
        "query-layer service health endpoint should report healthy",
    ]
    catalogs = [
        {
            "name": "postgres",
            "connector_name": postgres_catalog.get("connector.name", "postgresql"),
            "target": "operational retail database",
        },
        {
            "name": "iceberg",
            "connector_name": iceberg_catalog.get("connector.name", "iceberg"),
            "target": "lakehouse analytics tables",
        },
    ]
    generated_files = write_bundle_files(
        artifact_dir,
        json_files={
            "generated/postgres_catalog.json": postgres_catalog,
            "generated/iceberg_catalog.json": iceberg_catalog,
        },
        text_files={"generated/federation_queries.sql": query_examples},
    )
    payload = {
        "module_name": "query_layer",
        "platform_surface": "extensions",
        "status": bool_to_status(list(readiness_checks.values())),
        "generated_at": utc_now_iso(),
        "artifact_path": str(artifact_path.resolve()),
        "module_version": QUERY_LAYER_VERSION,
        "engine": "trino",
        "catalogs": catalogs,
        "federation_queries": [
            statement.strip() for statement in query_examples.split(";") if statement.strip()
        ],
        "config_templates": {
            "postgres_catalog": str(postgres_catalog_path.resolve()),
            "iceberg_catalog": str(iceberg_catalog_path.resolve()),
            "query_examples": str((module_root / "sql" / "federation_queries.sql").resolve()),
        },
        "compose_file": compose_summary["compose_file"],
        "service_inventory": compose_summary["services"],
        "bootstrap_commands": bootstrap_commands,
        "health_checks": health_checks,
        "readiness_checks": readiness_checks,
        "generated_files": generated_files,
    }
    return write_payload(artifact_path, payload)
