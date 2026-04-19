# Project:      RetailOps Data & AI Platform
# Module:       modules.streaming
# File:         service.py
# Path:         modules/streaming/service.py
#
# Summary:      Builds deployment-ready streaming bundles for the Pro platform.
# Purpose:      Converts topic, consumer-group, and processor templates into actionable streaming deployment artifacts.
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

STREAMING_VERSION = "streaming-v2"


def build_streaming_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "platform_extensions_streaming_bundle.json"
    cached = read_cached_payload(artifact_path, refresh)
    if cached is not None:
        return cached

    module_root = Path(__file__).resolve().parent
    repo_root = module_root.parents[1]
    compose_summary = summarize_compose(repo_root / "compose" / "compose.streaming.yaml")
    topics = load_yaml_file(module_root / "config" / "topics.yaml").get("topics", [])
    processors = load_yaml_file(module_root / "config" / "processors.yaml").get("processors", [])
    consumer_groups = load_yaml_file(module_root / "config" / "consumer_groups.yaml").get(
        "consumer_groups", []
    )
    readiness_checks = {
        "compose_overlay_exists": True,
        "topics_defined": bool(topics),
        "processors_defined": bool(processors),
        "consumer_groups_defined": bool(consumer_groups),
    }
    bootstrap_commands = [
        "docker compose -f compose/compose.core.yaml -f compose/compose.cdc.yaml -f compose/compose.streaming.yaml up -d",
        "rpk topic create retailops.raw_cdc.public.orders",
        "rpk topic create retailops.bronze.orders",
        "python scripts/health.sh",
    ]
    health_checks = [
        "Redpanda topics should exist with the expected retention settings",
        "streaming service health endpoint should respond with 200",
        "processor lag should remain below the operational threshold",
    ]
    generated_files = write_bundle_files(
        artifact_dir,
        json_files={
            "generated/topics.json": {"topics": topics},
            "generated/processors.json": {"processors": processors},
            "generated/consumer_groups.json": {"consumer_groups": consumer_groups},
        },
        text_files={"generated/bootstrap_commands.txt": "\n".join(bootstrap_commands) + "\n"},
    )

    payload = {
        "module_name": "streaming",
        "platform_surface": "extensions",
        "status": bool_to_status(list(readiness_checks.values())),
        "generated_at": utc_now_iso(),
        "artifact_path": str(artifact_path.resolve()),
        "module_version": STREAMING_VERSION,
        "runtime": "redpanda",
        "topics": topics,
        "processors": processors,
        "consumer_groups": consumer_groups,
        "config_templates": {
            "topics": str((module_root / "config" / "topics.yaml").resolve()),
            "processors": str((module_root / "config" / "processors.yaml").resolve()),
            "consumer_groups": str((module_root / "config" / "consumer_groups.yaml").resolve()),
        },
        "compose_file": compose_summary["compose_file"],
        "service_inventory": compose_summary["services"],
        "bootstrap_commands": bootstrap_commands,
        "health_checks": health_checks,
        "readiness_checks": readiness_checks,
        "generated_files": generated_files,
    }
    return write_payload(artifact_path, payload)
