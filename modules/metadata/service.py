# Project:      RetailOps Data & AI Platform
# Module:       modules.metadata
# File:         service.py
# Path:         modules/metadata/service.py
#
# Summary:      Builds deployment-ready metadata bundles for the Pro platform.
# Purpose:      Packages OpenMetadata ingestion, service connections, and operator guidance into reusable artifacts.
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

from __future__ import annotations

from pathlib import Path
from typing import Any

from modules.common.platform_extensions import (
    bool_to_status,
    load_yaml_file,
    read_cached_payload,
    summarize_compose,
    utc_now_iso,
    write_bundle_files,
    write_payload,
)

METADATA_VERSION = "metadata-v2"


def build_metadata_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "platform_extensions_metadata_bundle.json"
    cached = read_cached_payload(artifact_path, refresh)
    if cached is not None:
        return cached

    module_root = Path(__file__).resolve().parent
    repo_root = module_root.parents[1]
    compose_summary = summarize_compose(repo_root / "compose" / "compose.metadata.yaml")
    ingestion = load_yaml_file(module_root / "config" / "openmetadata_ingestion.yaml")
    connections = load_yaml_file(module_root / "config" / "service_connections.yaml")
    sources = ingestion.get("sources", [])
    workflows = [
        {
            "name": f"{item.get('name', 'unknown')}_ingestion",
            "source_type": item.get("type", "unknown"),
            "output": "catalog metadata and lineage",
        }
        for item in sources
    ]
    readiness_checks = {
        "compose_overlay_exists": True,
        "sources_defined": bool(sources),
        "service_connections_defined": bool(connections.get("services", [])),
        "lineage_enabled": bool(ingestion.get("lineage", {}).get("enabled", False)),
    }
    bootstrap_commands = [
        "docker compose -f compose/compose.core.yaml -f compose/compose.metadata.yaml up -d",
        "openmetadata-ingestion run -c modules/metadata/config/openmetadata_ingestion.yaml",
        "python scripts/health.sh",
    ]
    health_checks = [
        "OpenMetadata UI should load successfully",
        "metadata service should connect to MySQL and Elasticsearch",
        "catalog should list PostgreSQL, dbt, and Trino services",
        "lineage graph should show dbt to query-layer relationships",
    ]
    generated_files = write_bundle_files(
        artifact_dir,
        json_files={
            "generated/openmetadata_ingestion.json": ingestion,
            "generated/service_connections.json": connections,
        },
        text_files={
            "generated/runbook.md": "# Metadata Runbook\n\n"
            "1. Start the metadata overlay.\n"
            "2. Configure service connections.\n"
            "3. Run ingestion workflows.\n"
            "4. Validate lineage and ownership metadata.\n"
        },
    )
    payload = {
        "module_name": "metadata",
        "platform_surface": "extensions",
        "status": bool_to_status(list(readiness_checks.values())),
        "generated_at": utc_now_iso(),
        "artifact_path": str(artifact_path.resolve()),
        "module_version": METADATA_VERSION,
        "platform": str(ingestion.get("service", {}).get("platform", "openmetadata")),
        "lineage_enabled": bool(ingestion.get("lineage", {}).get("enabled", False)),
        "workflows": workflows,
        "service_connections": connections.get("services", []),
        "config_templates": {
            "openmetadata_ingestion": str(
                (module_root / "config" / "openmetadata_ingestion.yaml").resolve()
            ),
            "service_connections": str(
                (module_root / "config" / "service_connections.yaml").resolve()
            ),
        },
        "compose_file": compose_summary["compose_file"],
        "service_inventory": compose_summary["services"],
        "bootstrap_commands": bootstrap_commands,
        "health_checks": health_checks,
        "readiness_checks": readiness_checks,
        "generated_files": generated_files,
    }
    return write_payload(artifact_path, payload)
