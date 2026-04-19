# Project:      RetailOps Data & AI Platform
# Module:       modules.common
# File:         platform_extensions.py
# Path:         modules/common/platform_extensions.py
#
# Summary:      Provides shared helpers for platform-extension bundle generation and deployment planning.
# Purpose:      Centralizes artifact IO, template loading, compose summarization, and operator-facing deployment-plan assembly for Pro modules.
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
#   - Key APIs: read_cached_payload, write_payload, write_bundle_files, summarize_compose, load_env_sample, build_platform_deployment_plan.
#   - Dependencies: __future__, json, pathlib, typing, yaml.
#   - Constraints: Artifact filenames and JSON structure should remain stable for downstream tooling and operator scripts.
#   - Compatibility: Python 3.11+ with PyYAML available in the repository runtime.

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def read_cached_payload(path: Path, refresh: bool) -> dict[str, Any] | None:
    if refresh or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def write_bundle_files(
    artifact_dir: Path,
    json_files: dict[str, Any] | None = None,
    text_files: dict[str, str] | None = None,
) -> dict[str, str]:
    written: dict[str, str] = {}
    for name, payload in (json_files or {}).items():
        path = artifact_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written[name] = str(path.resolve())
    for name, content in (text_files or {}).items():
        path = artifact_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written[name] = str(path.resolve())
    return written


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml_file(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return raw
    raise ValueError(f"Expected YAML object at {path}")


def summarize_compose(compose_path: Path) -> dict[str, Any]:
    payload = load_yaml_file(compose_path)
    services = payload.get("services", {})
    if not isinstance(services, dict):
        raise ValueError(f"Invalid services section in {compose_path}")
    service_inventory: list[dict[str, Any]] = []
    for service_name, spec in services.items():
        if not isinstance(spec, dict):
            continue
        depends_on = spec.get("depends_on", [])
        if isinstance(depends_on, dict):
            depends = list(depends_on.keys())
        elif isinstance(depends_on, list):
            depends = [str(item) for item in depends_on]
        else:
            depends = []
        service_inventory.append(
            {
                "name": service_name,
                "image": str(spec.get("image", "")),
                "depends_on": depends,
                "has_healthcheck": "healthcheck" in spec,
                "volume_count": len(spec.get("volumes", [])),
                "port_count": len(spec.get("ports", [])),
            }
        )
    return {
        "compose_file": str(compose_path.resolve()),
        "service_count": len(service_inventory),
        "services": service_inventory,
    }


def load_env_sample(path: Path) -> dict[str, str]:
    variables: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        variables[key.strip()] = value.strip()
    return variables


def bool_to_status(validations: list[bool]) -> str:
    return "deployment_ready" if all(validations) else "needs_attention"


def _collect_service_names(payload: dict[str, Any]) -> list[str]:
    items = payload.get("service_inventory", [])
    names = [str(item.get("name", "")) for item in items if isinstance(item, dict)]
    return [name for name in names if name]


def _collect_dependency_names(payload: dict[str, Any]) -> list[str]:
    dependencies: set[str] = set()
    items = payload.get("service_inventory", [])
    for item in items:
        if not isinstance(item, dict):
            continue
        for dependency in item.get("depends_on", []) or []:
            text = str(dependency).strip()
            if text:
                dependencies.add(text)
    return sorted(dependencies)


def build_platform_deployment_plan(
    *, modules: dict[str, dict[str, Any]], artifact_root: Path, repo_root: Path
) -> dict[str, Any]:
    env_sample = load_env_sample(repo_root / "config" / "samples" / "pro.env")
    compose_files = [
        item for item in env_sample.get("COMPOSE_FILES", "").split(":") if item.strip()
    ]
    compose_chain = [str((repo_root / item).resolve()) for item in compose_files]
    compose_command = (
        "docker compose " + " ".join(f"-f {item}" for item in compose_files) + " up -d"
    )
    module_plans: dict[str, dict[str, Any]] = {}
    for module_name, payload in modules.items():
        module_plans[module_name] = {
            "module_name": payload.get("module_name", module_name),
            "status": payload.get("status", "needs_attention"),
            "compose_file": payload.get("compose_file", ""),
            "service_names": _collect_service_names(payload),
            "depends_on_services": _collect_dependency_names(payload),
            "bootstrap_commands": payload.get("bootstrap_commands", []),
            "health_checks": payload.get("health_checks", []),
            "generated_files": payload.get("generated_files", {}),
            "readiness_checks": payload.get("readiness_checks", {}),
        }
    operator_checklist = [
        "Prepare credentials and network access for PostgreSQL, object storage, metadata services, and serving runtimes.",
        "Export the variables from config/samples/pro.env into the target deployment environment.",
        "Start the compose chain in order, then register CDC connectors and validate streaming topics.",
        "Generate the Pro bundle artifacts and compare readiness checks before enabling production traffic.",
        "Validate health checks, model serving aliases, and feature-store materialization before going live.",
    ]
    return {
        "platform_surface": "extensions",
        "platform_name": "RetailOps Pro Data Platform",
        "artifact_root": str(artifact_root.resolve()),
        "generated_at": utc_now_iso(),
        "compose_chain": compose_chain,
        "compose_command": compose_command,
        "environment_variables": sorted(env_sample.keys()),
        "module_count": len(module_plans),
        "deployment_ready_count": sum(
            1 for item in modules.values() if item.get("status") == "deployment_ready"
        ),
        "modules": module_plans,
        "operator_checklist": operator_checklist,
    }
