# Project:      RetailOps Data & AI Platform
# Module:       modules.lakehouse
# File:         service.py
# Path:         modules/lakehouse/service.py
#
# Summary:      Builds deployment-ready lakehouse bundles for the Pro platform.
# Purpose:      Packages lakehouse layout, Spark jobs, and compose metadata into operator-friendly artifacts.
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
#   - Key APIs: build_lakehouse_artifact
#   - Dependencies: __future__, pathlib, typing, modules.common.platform_extensions
#   - Constraints: Lakehouse layer naming should stay stable because query-layer artifacts depend on it.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

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

LAKEHOUSE_VERSION = "lakehouse-v2"


def build_lakehouse_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "platform_extensions_lakehouse_bundle.json"
    cached = read_cached_payload(artifact_path, refresh)
    if cached is not None:
        return cached

    module_root = Path(__file__).resolve().parent
    repo_root = module_root.parents[1]
    compose_summary = summarize_compose(repo_root / "compose" / "compose.lakehouse.yaml")
    layout = load_yaml_file(module_root / "config" / "lakehouse_layout.yaml")
    bronze_sql = (module_root / "jobs" / "bronze_to_silver.sql").read_text(encoding="utf-8")
    silver_sql_path = module_root / "jobs" / "silver_to_gold_store_kpis.sql"
    silver_sql = silver_sql_path.read_text(encoding="utf-8") if silver_sql_path.exists() else ""
    layers = [
        {"layer_name": layer_name, "purpose": str(spec.get("description", "")), "tables": []}
        for layer_name, spec in layout.get("layers", {}).items()
    ]
    readiness_checks = {
        "compose_overlay_exists": True,
        "layout_has_layers": bool(layers),
        "bronze_job_present": bool(bronze_sql.strip()),
        "silver_job_present": bool(silver_sql.strip()),
    }
    bootstrap_commands = [
        "docker compose -f compose/compose.core.yaml -f compose/compose.lakehouse.yaml up -d",
        "mc mb local/retailops-lakehouse",
        "spark-sql -f modules/lakehouse/jobs/bronze_to_silver.sql",
        "spark-sql -f modules/lakehouse/jobs/silver_to_gold_store_kpis.sql",
    ]
    health_checks = [
        "MinIO bucket retailops-lakehouse should exist",
        "Spark master should accept jobs",
        "Iceberg warehouse path should be writable",
        "gold store KPI tables should be queryable",
    ]
    generated_files = write_bundle_files(
        artifact_dir,
        json_files={
            "generated/layout.json": layout,
            "generated/spark_jobs.json": {
                "jobs": [
                    "modules/lakehouse/jobs/bronze_to_silver.sql",
                    "modules/lakehouse/jobs/silver_to_gold_store_kpis.sql",
                ]
            },
        },
        text_files={
            "generated/bronze_to_silver.sql": bronze_sql,
            "generated/silver_to_gold_store_kpis.sql": silver_sql,
        },
    )
    payload = {
        "module_name": "lakehouse",
        "platform_surface": "extensions",
        "status": bool_to_status(list(readiness_checks.values())),
        "generated_at": utc_now_iso(),
        "artifact_path": str(artifact_path.resolve()),
        "module_version": LAKEHOUSE_VERSION,
        "catalog_type": str(layout.get("catalog", {}).get("type", "iceberg-rest")),
        "table_format": "iceberg",
        "object_storage": str(layout.get("object_storage", {}).get("type", "minio")),
        "layers": layers,
        "spark_jobs": ["bronze_to_silver.sql", "silver_to_gold_store_kpis.sql"],
        "config_templates": {
            "layout": str((module_root / "config" / "lakehouse_layout.yaml").resolve()),
            "bronze_job": str((module_root / "jobs" / "bronze_to_silver.sql").resolve()),
            "silver_job": str(silver_sql_path.resolve()),
        },
        "compose_file": compose_summary["compose_file"],
        "service_inventory": compose_summary["services"],
        "bootstrap_commands": bootstrap_commands,
        "health_checks": health_checks,
        "readiness_checks": readiness_checks,
        "generated_files": generated_files,
    }
    return write_payload(artifact_path, payload)
