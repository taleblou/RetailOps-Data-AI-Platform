# Project:      RetailOps Data & AI Platform
# Module:       tests.pro_platform
# File:         test_platform_extensions.py
# Path:         tests/pro_platform/test_platform_extensions.py
#
# Summary:      Validates the Pro platform deployment bundles and readiness APIs.
# Purpose:      Protects the repository against regressions in Pro platform bundle generation.
# Scope:        test
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

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.advanced_serving.service import build_advanced_serving_artifact
from modules.cdc.service import build_cdc_artifact
from modules.feature_store.service import build_feature_store_artifact
from modules.lakehouse.service import build_lakehouse_artifact
from modules.metadata.service import build_metadata_artifact
from modules.query_layer.service import build_query_layer_artifact
from modules.streaming.service import build_streaming_artifact


def test_platform_extensions_services_generate_all_pro_platform_bundles(tmp_path: Path) -> None:
    payloads = [
        build_cdc_artifact(tmp_path / "cdc", refresh=True),
        build_streaming_artifact(tmp_path / "streaming", refresh=True),
        build_lakehouse_artifact(tmp_path / "lakehouse", refresh=True),
        build_query_layer_artifact(tmp_path / "query_layer", refresh=True),
        build_metadata_artifact(tmp_path / "metadata", refresh=True),
        build_feature_store_artifact(tmp_path / "feature_store", refresh=True),
        build_advanced_serving_artifact(tmp_path / "advanced_serving", refresh=True),
    ]
    for payload in payloads:
        assert payload["status"] == "deployment_ready"
        assert Path(payload["artifact_path"]).exists()
        assert payload["service_inventory"]
        assert payload["generated_files"]
        assert all(Path(path).exists() for path in payload["generated_files"].values())


def test_platform_extensions_api_exposes_module_bundles_and_readiness(tmp_path: Path) -> None:
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)
    artifact_root = tmp_path / "pro_platform"
    summary_response = client.get(
        "/api/v1/pro-platform/summary",
        params={"artifact_dir": str(artifact_root), "refresh": "true"},
    )
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["module_count"] == 7
    assert summary_payload["deployment_ready_count"] == 7
    readiness_response = client.get(
        "/api/v1/pro-platform/readiness",
        params={"artifact_dir": str(artifact_root), "refresh": "true"},
    )
    assert readiness_response.status_code == 200
    readiness_payload = readiness_response.json()
    assert readiness_payload["deployment_ready_count"] == 7
    for item in readiness_payload["modules"]:
        assert item["status"] == "deployment_ready"
        assert all(item["readiness_checks"].values())


def test_platform_extensions_api_exposes_deployment_plan(tmp_path: Path) -> None:
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)
    artifact_root = tmp_path / "pro_platform"
    response = client.get(
        "/api/v1/pro-platform/deployment-plan",
        params={"artifact_dir": str(artifact_root), "refresh": "true"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["module_count"] == 7
    assert payload["deployment_ready_count"] == 7
    assert payload["compose_chain"]
    assert payload["compose_command"].startswith("docker compose")
    assert "APP_PROFILE" in payload["environment_variables"]
    assert payload["operator_checklist"]


def test_platform_extensions_static_files_and_docs_exist() -> None:
    required_files = [
        Path("docs/platform/pro_data_platform.md"),
        Path("docs/platform/platform_extensions_runbook.md"),
        Path("modules/query_layer/sql/federation_queries.sql"),
        Path("modules/feature_store/repo/materialization_schedule.yaml"),
        Path("modules/advanced_serving/config/runtime_deployments.yaml"),
        Path("modules/common/platform_extensions.py"),
    ]
    for path in required_files:
        assert path.exists()


def test_generate_pro_platform_bundle_script(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_pro_platform_bundle.py",
            "--artifact-dir",
            str(tmp_path / "generated_pro"),
            "--refresh",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary_path = Path(result.stdout.strip())
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["module_count"] == 7
    assert payload["deployment_ready_count"] == 7
    assert (tmp_path / "generated_pro" / "platform_extensions_deployment_plan.json").exists()
