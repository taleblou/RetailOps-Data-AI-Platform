# Project:      RetailOps Data & AI Platform
# Module:       modules.advanced_serving
# File:         service.py
# Path:         modules/advanced_serving/service.py
#
# Summary:      Builds deployment-ready advanced-serving bundles for the Pro platform.
# Purpose:      Packages BentoML runtime plans, rollout policies, and shadow-deployment metadata into reusable artifacts.
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

ADVANCED_SERVING_VERSION = "advanced-serving-v2"


def route_runtime_request(payload: dict[str, Any]) -> dict[str, Any]:
    task = str(payload.get("task", "forecast")).strip().lower()
    task_to_runtime = {
        "forecast": {"primary": "forecasting-runtime", "shadow": []},
        "shipment-delay": {
            "primary": "forecasting-runtime",
            "shadow": ["shipment-risk-runtime"],
        },
        "return-risk": {
            "primary": "forecasting-runtime",
            "shadow": ["return-risk-runtime"],
        },
    }
    routing = task_to_runtime.get(task, task_to_runtime["forecast"])
    return {
        "task": task,
        "primary_runtime": routing["primary"],
        "shadow_runtimes": routing["shadow"],
        "request_mode": "shadow" if routing["shadow"] else "primary_only",
    }


def build_advanced_serving_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "platform_extensions_advanced_serving_bundle.json"
    cached = read_cached_payload(artifact_path, refresh)
    if cached is not None:
        return cached

    module_root = Path(__file__).resolve().parent
    repo_root = module_root.parents[1]
    compose_summary = summarize_compose(repo_root / "compose" / "compose.advanced_serving.yaml")
    runtime_deployments = load_yaml_file(module_root / "config" / "runtime_deployments.yaml")
    bentofile = (module_root / "bentofile.yaml").read_text(encoding="utf-8")
    service_source = (module_root / "bentoml" / "service.py").read_text(encoding="utf-8")
    services = runtime_deployments.get("services", [])
    readiness_checks = {
        "compose_overlay_exists": True,
        "runtime_deployments_defined": bool(services),
        "bentofile_present": bool(bentofile.strip()),
        "service_source_present": bool(service_source.strip()),
    }
    bootstrap_commands = [
        "docker compose -f compose/compose.core.yaml -f compose/compose.advanced_serving.yaml up -d",
        "bentoml serve modules.advanced_serving.bentoml.service:svc",
        'curl -X POST http://localhost:${BENTOML_PORT:-3010}/predict --json \'{"task": "forecast"}\'',
    ]
    health_checks = [
        "BentoML service should accept prediction requests",
        "primary and shadow runtime routes should be visible in deployment metadata",
        "model alias mapping should align with registry champion and challenger aliases",
    ]
    shadow_deployments = [
        item.get("name", "") for item in services if item.get("deployment_mode") == "shadow"
    ]
    generated_files = write_bundle_files(
        artifact_dir,
        json_files={
            "generated/runtime_deployments.json": runtime_deployments,
            "generated/routing_examples.json": {
                "forecast": route_runtime_request({"task": "forecast"}),
                "shipment-delay": route_runtime_request({"task": "shipment-delay"}),
                "return-risk": route_runtime_request({"task": "return-risk"}),
            },
        },
        text_files={
            "generated/bentofile.yaml": bentofile,
            "generated/service.py": service_source,
        },
    )
    payload = {
        "module_name": "advanced_serving",
        "platform_surface": "extensions",
        "status": bool_to_status(list(readiness_checks.values())),
        "generated_at": utc_now_iso(),
        "artifact_path": str(artifact_path.resolve()),
        "module_version": ADVANCED_SERVING_VERSION,
        "platform": "bentoml",
        "services": services,
        "shadow_deployments": shadow_deployments,
        "config_templates": {
            "bentofile": str((module_root / "bentofile.yaml").resolve()),
            "service": str((module_root / "bentoml" / "service.py").resolve()),
            "runtime_deployments": str(
                (module_root / "config" / "runtime_deployments.yaml").resolve()
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
