# Project:      RetailOps Data & AI Platform
# Module:       modules.feature_store
# File:         service.py
# Path:         modules/feature_store/service.py
#
# Summary:      Builds deployment-ready feature-store bundles for the Pro platform.
# Purpose:      Packages Feast templates, materialization schedules, and service metadata into reusable artifacts.
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
#   - Key APIs: build_feature_store_artifact
#   - Dependencies: __future__, pathlib, re, typing, modules.common.platform_extensions
#   - Constraints: Feature-view names and materialization jobs should stay aligned with online-serving expectations.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import re
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

FEATURE_STORE_VERSION = "feature-store-v2"


def _extract_feature_view_names(content: str) -> list[str]:
    return re.findall(r"^(\w+_features_view)\s*=\s*FeatureView\(", content, flags=re.MULTILINE)


def build_feature_store_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "platform_extensions_feature_store_bundle.json"
    cached = read_cached_payload(artifact_path, refresh)
    if cached is not None:
        return cached

    module_root = Path(__file__).resolve().parent
    repo_root = module_root.parents[1]
    compose_summary = summarize_compose(repo_root / "compose" / "compose.feature_store.yaml")
    feature_store_yaml = load_yaml_file(module_root / "repo" / "feature_store.yaml")
    schedule = load_yaml_file(module_root / "repo" / "materialization_schedule.yaml")
    feature_view_source = (module_root / "repo" / "feature_views.py").read_text(encoding="utf-8")
    feature_view_names = _extract_feature_view_names(feature_view_source)
    feature_views = [
        {
            "name": name,
            "entity": "shipment_id" if "shipment" in name else "sku",
            "ttl_days": 7 if "shipment" in name else 14,
            "owner": "logistics-ai" if "shipment" in name else "inventory-ai",
        }
        for name in feature_view_names
    ]
    readiness_checks = {
        "compose_overlay_exists": True,
        "feature_store_repo_exists": bool(feature_store_yaml),
        "feature_views_defined": bool(feature_views),
        "materialization_jobs_defined": bool(schedule.get("jobs", [])),
    }
    bootstrap_commands = [
        "docker compose -f compose/compose.core.yaml -f compose/compose.feature_store.yaml up -d",
        "feast apply",
        "feast materialize-incremental $(date -u +%Y-%m-%dT%H:%M:%SZ)",
    ]
    health_checks = [
        "Redis online store should be reachable",
        "Feast registry should be created or updated",
        "materialization jobs should publish fresh feature values",
    ]
    generated_files = write_bundle_files(
        artifact_dir,
        json_files={
            "generated/feature_store.json": feature_store_yaml,
            "generated/materialization_schedule.json": schedule,
            "generated/feature_views.json": {"feature_views": feature_views},
        },
        text_files={"generated/feature_views.py": feature_view_source},
    )
    payload = {
        "module_name": "feature_store",
        "platform_surface": "extensions",
        "status": bool_to_status(list(readiness_checks.values())),
        "generated_at": utc_now_iso(),
        "artifact_path": str(artifact_path.resolve()),
        "module_version": FEATURE_STORE_VERSION,
        "engine": "feast",
        "offline_store": str(feature_store_yaml.get("offline_store", {}).get("type", "postgres")),
        "online_store": str(feature_store_yaml.get("online_store", {}).get("type", "redis")),
        "feature_views": feature_views,
        "materialization_jobs": [job.get("name", "") for job in schedule.get("jobs", [])],
        "config_templates": {
            "feature_store": str((module_root / "repo" / "feature_store.yaml").resolve()),
            "feature_views": str((module_root / "repo" / "feature_views.py").resolve()),
            "materialization_schedule": str(
                (module_root / "repo" / "materialization_schedule.yaml").resolve()
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
