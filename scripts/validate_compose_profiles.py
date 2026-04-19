# Project:      RetailOps Data & AI Platform
# Module:       scripts
# File:         validate_compose_profiles.py
# Path:         scripts/validate_compose_profiles.py
#
# Summary:      Validates Compose overlays, referenced Dockerfiles, and profile sample files.
# Purpose:      Provides a repeatable repository-level packaging check before deployment.
# Scope:        tool
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
#   - Main types: ValidationIssue.
#   - Key APIs: main().
#   - Dependencies: argparse, pathlib, yaml.
#   - Constraints: Expects execution from anywhere inside the repository checkout.
#   - Compatibility: Python 3.11+ with PyYAML installed.

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ValidationIssue:
    path: Path
    message: str


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected mapping at top level: {path}")
    return payload


def validate_compose_file(repo_root: Path, path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    payload = load_yaml(path)
    services = payload.get("services", {})
    if not isinstance(services, dict) or not services:
        issues.append(ValidationIssue(path, "Compose file has no services mapping."))
        return issues

    for service_name, service in services.items():
        if not isinstance(service, dict):
            issues.append(ValidationIssue(path, f"Service '{service_name}' is not a mapping."))
            continue
        build = service.get("build")
        if isinstance(build, dict):
            dockerfile = build.get("dockerfile")
            if isinstance(dockerfile, str):
                dockerfile_path = (repo_root / dockerfile).resolve()
                if not dockerfile_path.exists():
                    issues.append(
                        ValidationIssue(
                            path,
                            f"Service '{service_name}' references missing Dockerfile: {dockerfile}",
                        )
                    )
        env_file = service.get("env_file")
        if isinstance(env_file, list):
            for raw_env_path in env_file:
                if not isinstance(raw_env_path, str):
                    issues.append(
                        ValidationIssue(
                            path, f"Service '{service_name}' has non-string env_file entry."
                        )
                    )
                    continue
                resolved_env_path = (path.parent / raw_env_path).resolve()
                if resolved_env_path.exists():
                    continue
                fallback_env_path = repo_root / ".env.example"
                if raw_env_path.endswith(".env") and fallback_env_path.exists():
                    continue
                issues.append(
                    ValidationIssue(
                        path,
                        f"Service '{service_name}' references missing env_file: {raw_env_path}",
                    )
                )
    return issues


def validate_profiles(repo_root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_connector_files = [
        repo_root / "compose" / "compose.connector_csv.yaml",
        repo_root / "compose" / "compose.connector_db.yaml",
        repo_root / "compose" / "compose.connector_shopify.yaml",
        repo_root / "compose" / "compose.connector_woocommerce.yaml",
        repo_root / "compose" / "compose.connector_adobe_commerce.yaml",
        repo_root / "compose" / "compose.connector_bigcommerce.yaml",
        repo_root / "compose" / "compose.connector_prestashop.yaml",
    ]
    for connector_file in required_connector_files:
        if not connector_file.exists():
            issues.append(ValidationIssue(connector_file, "Missing connector compose overlay."))

    for profile in ("lite", "standard", "pro"):
        sample = repo_root / "config" / "samples" / f"{profile}.env"
        if not sample.exists():
            issues.append(ValidationIssue(sample, "Missing profile sample file."))
            continue
        content = sample.read_text(encoding="utf-8")
        if "ENABLED_CONNECTORS=" not in content:
            issues.append(ValidationIssue(sample, "Profile sample is missing ENABLED_CONNECTORS."))
        if "ENABLED_OPTIONAL_EXTRAS=" not in content:
            issues.append(
                ValidationIssue(sample, "Profile sample is missing ENABLED_OPTIONAL_EXTRAS.")
            )

    dockerfile_requirements = {
        repo_root / "core" / "api" / "Dockerfile": "--extra reporting",
        repo_root / "modules" / "feature_store" / "Dockerfile": "--extra feature-store",
        repo_root / "modules" / "advanced_serving" / "Dockerfile": "--extra advanced-serving",
    }
    for dockerfile, expected_token in dockerfile_requirements.items():
        if not dockerfile.exists():
            issues.append(ValidationIssue(dockerfile, "Missing Dockerfile."))
            continue
        content = dockerfile.read_text(encoding="utf-8")
        if expected_token not in content:
            issues.append(
                ValidationIssue(
                    dockerfile,
                    f"Dockerfile is missing expected optional extra wiring: {expected_token}",
                )
            )
    return issues


def collect_issues(repo_root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for compose_path in sorted((repo_root / "compose").glob("*.yaml")):
        issues.extend(validate_compose_file(repo_root, compose_path))
    issues.extend(validate_profiles(repo_root))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate compose overlays and profile samples.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    issues = collect_issues(repo_root)
    if issues:
        for issue in issues:
            print(f"[ERROR] {issue.path.relative_to(repo_root)} :: {issue.message}")
        return 1
    print("All compose overlays and profile samples passed validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
