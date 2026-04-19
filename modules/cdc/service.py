# Project:      RetailOps Data & AI Platform
# Module:       modules.cdc
# File:         service.py
# Path:         modules/cdc/service.py
#
# Summary:      Builds deployment-ready CDC bundles for the Pro platform.
# Purpose:      Turns Debezium, routing, and compose templates into reusable CDC artifacts and runbooks.
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
    load_json_file,
    load_yaml_file,
    read_cached_payload,
    summarize_compose,
    utc_now_iso,
    write_bundle_files,
    write_payload,
)

CDC_VERSION = "cdc-v2"


def build_cdc_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "platform_extensions_cdc_bundle.json"
    cached = read_cached_payload(artifact_path, refresh)
    if cached is not None:
        return cached

    module_root = Path(__file__).resolve().parent
    repo_root = module_root.parents[1]
    compose_summary = summarize_compose(repo_root / "compose" / "compose.cdc.yaml")
    connector_template = load_json_file(module_root / "config" / "debezium-postgres.json")
    cdc_profile = load_yaml_file(module_root / "config" / "cdc_profile.yaml")
    routing_profile = load_yaml_file(module_root / "config" / "table_routing.yaml")

    readiness_checks = {
        "compose_overlay_exists": True,
        "connector_template_has_name": bool(connector_template.get("name")),
        "profile_has_tables": bool(cdc_profile.get("tables")),
        "routing_has_routes": bool(routing_profile.get("routes")),
    }
    bootstrap_commands = [
        "docker compose -f compose/compose.core.yaml -f compose/compose.cdc.yaml up -d",
        "curl -X POST http://localhost:${DEBEZIUM_PORT:-8083}/connectors -H 'Content-Type: application/json' --data @generated/debezium_connector.json",
        "python scripts/health.sh",
    ]
    health_checks = [
        "redpanda cluster health should report healthy brokers",
        "Debezium connector status should be RUNNING",
        "replication slot retailops_cdc_slot should exist in PostgreSQL",
        "raw CDC topics should receive snapshot and change events",
    ]
    generated_files = write_bundle_files(
        artifact_dir,
        json_files={
            "generated/debezium_connector.json": connector_template,
            "generated/cdc_profile.json": cdc_profile,
            "generated/table_routing.json": routing_profile,
        },
        text_files={
            "generated/runbook.md": "# CDC Runbook\n\n"
            "1. Start compose core and CDC overlays.\n"
            "2. Register the Debezium connector.\n"
            "3. Watch snapshot completion in Debezium logs.\n"
            "4. Confirm events land in raw topics.\n"
            "5. Hand off bronze topics to streaming and lakehouse layers.\n"
        },
    )

    payload = {
        "module_name": "cdc",
        "platform_surface": "extensions",
        "status": bool_to_status(list(readiness_checks.values())),
        "generated_at": utc_now_iso(),
        "artifact_path": str(artifact_path.resolve()),
        "module_version": CDC_VERSION,
        "connector_name": connector_template.get("name", "retailops-postgres-cdc"),
        "source_database": connector_template.get("config", {}).get("database.dbname", "retailops"),
        "kafka_compatible_runtime": "redpanda",
        "raw_event_topic_prefix": cdc_profile.get("routing", {}).get(
            "raw_topic_prefix", "retailops.raw_cdc"
        ),
        "snapshot_mode": cdc_profile.get("snapshot_mode", "initial"),
        "replication_slot": connector_template.get("config", {}).get(
            "slot.name", "retailops_cdc_slot"
        ),
        "publication_name": connector_template.get("config", {}).get(
            "publication.name", "retailops_cdc_publication"
        ),
        "tables": cdc_profile.get("tables", []),
        "routes": routing_profile.get("routes", []),
        "connector_properties": connector_template.get("config", {}),
        "config_templates": {
            "debezium_connector": str(
                (module_root / "config" / "debezium-postgres.json").resolve()
            ),
            "cdc_profile": str((module_root / "config" / "cdc_profile.yaml").resolve()),
            "table_routing": str((module_root / "config" / "table_routing.yaml").resolve()),
        },
        "compose_file": compose_summary["compose_file"],
        "service_inventory": compose_summary["services"],
        "bootstrap_commands": bootstrap_commands,
        "health_checks": health_checks,
        "readiness_checks": readiness_checks,
        "generated_files": generated_files,
    }
    return write_payload(artifact_path, payload)
