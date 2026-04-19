# Project:      RetailOps Data & AI Platform
# Module:       tests.ml_registry
# File:         test_ml_registry.py
# Path:         tests/ml_registry/test_ml_registry.py
#
# Summary:      Contains automated tests for the ml registry workflows and behaviors.
# Purpose:      Validates ml registry behavior and protects the repository against regressions.
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
#
# Notes:
#   - Main types: None.
#   - Key APIs: test_run_model_registry_builds_named_registries, test_promote_and_rollback_registry_registry_updates_aliases, test_get_model_registry_details_exposes_threshold_gates, test_registry_router_returns_summary_details_promote_and_rollback
#   - Dependencies: __future__, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, modules.ml_registry.service, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.ml_registry.service import (
    get_model_registry_details,
    promote_registry_model,
    rollback_registry_model,
    run_model_registry,
)


def test_run_model_registry_builds_named_registries(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "model_registry"
    artifact = run_model_registry(artifact_dir=artifact_dir, refresh=True)

    assert artifact.experiment_tracking_enabled is True
    assert len(artifact.registries) == 4
    registry_names = {item.registry_name for item in artifact.registries}
    assert registry_names == {
        "forecasting_model",
        "shipment_delay_model",
        "stockout_model",
        "return_risk_model",
    }
    assert Path(artifact.artifact_path).exists()


def test_promote_and_rollback_registry_registry_updates_aliases(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "model_registry"
    run_model_registry(artifact_dir=artifact_dir, refresh=True)

    promoted = promote_registry_model(
        registry_name="forecasting_model",
        artifact_dir=artifact_dir,
    )
    assert promoted["aliases"]["champion"] == "registry-forecasting-model-v2"
    assert promoted["aliases"]["challenger"] == "forecasting-baseline-v1"
    assert promoted["promotion_history"]

    rolled_back = rollback_registry_model(
        registry_name="forecasting_model",
        artifact_dir=artifact_dir,
    )
    assert rolled_back["aliases"]["champion"] == "forecasting-baseline-v1"
    assert rolled_back["rollback_history"]


def test_get_model_registry_details_exposes_threshold_gates(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "model_registry"
    run_model_registry(artifact_dir=artifact_dir, refresh=True)

    details = get_model_registry_details(
        registry_name="shipment_delay_model",
        artifact_dir=artifact_dir,
    )

    assert details["registry_name"] == "shipment_delay_model"
    assert details["aliases"]["champion"] == "shipment-risk-v1"
    assert len(details["threshold_gates"]) == 3
    assert all("passed" in gate for gate in details["threshold_gates"])


def test_registry_router_returns_summary_details_promote_and_rollback(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "model_registry"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    summary_response = client.get(
        "/api/v1/ml-registry/summary",
        params={"artifact_dir": str(artifact_dir), "refresh": "true"},
    )
    assert summary_response.status_code == 200, summary_response.text
    summary_payload = summary_response.json()
    assert summary_payload["experiment_tracking_enabled"] is True
    assert len(summary_payload["registries"]) == 4

    details_response = client.get(
        "/api/v1/ml-registry/models/return_risk_model",
        params={"artifact_dir": str(artifact_dir)},
    )
    assert details_response.status_code == 200, details_response.text
    details_payload = details_response.json()
    assert details_payload["aliases"]["champion"] == "returns-intelligence-v1"

    promote_response = client.post(
        "/api/v1/ml-registry/models/return_risk_model/promote",
        params={"artifact_dir": str(artifact_dir)},
        json={"candidate_alias": "challenger"},
    )
    assert promote_response.status_code == 200, promote_response.text
    promote_payload = promote_response.json()
    assert promote_payload["aliases"]["champion"] == "registry-return-risk-model-v2"

    rollback_response = client.post(
        "/api/v1/ml-registry/models/return_risk_model/rollback",
        params={"artifact_dir": str(artifact_dir)},
        json={},
    )
    assert rollback_response.status_code == 200, rollback_response.text
    rollback_payload = rollback_response.json()
    assert rollback_payload["aliases"]["champion"] == "returns-intelligence-v1"
