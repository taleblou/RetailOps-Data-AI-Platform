from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.ml_registry.service import (
    get_phase15_registry_details,
    promote_phase15_registry_model,
    rollback_phase15_registry_model,
    run_phase15_model_registry,
)


def test_run_phase15_model_registry_builds_named_registries(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "model_registry"
    artifact = run_phase15_model_registry(artifact_dir=artifact_dir, refresh=True)

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


def test_promote_and_rollback_phase15_registry_updates_aliases(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "model_registry"
    run_phase15_model_registry(artifact_dir=artifact_dir, refresh=True)

    promoted = promote_phase15_registry_model(
        registry_name="forecasting_model",
        artifact_dir=artifact_dir,
    )
    assert promoted["aliases"]["champion"] == "phase15-forecasting-model-v2"
    assert promoted["aliases"]["challenger"] == "phase10-baseline-v1"
    assert promoted["promotion_history"]

    rolled_back = rollback_phase15_registry_model(
        registry_name="forecasting_model",
        artifact_dir=artifact_dir,
    )
    assert rolled_back["aliases"]["champion"] == "phase10-baseline-v1"
    assert rolled_back["rollback_history"]


def test_get_phase15_registry_details_exposes_threshold_gates(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "model_registry"
    run_phase15_model_registry(artifact_dir=artifact_dir, refresh=True)

    details = get_phase15_registry_details(
        registry_name="shipment_delay_model",
        artifact_dir=artifact_dir,
    )

    assert details["registry_name"] == "shipment_delay_model"
    assert details["aliases"]["champion"] == "phase11-shipment-risk-v1"
    assert len(details["threshold_gates"]) == 3
    assert all("passed" in gate for gate in details["threshold_gates"])


def test_phase15_router_returns_summary_details_promote_and_rollback(tmp_path: Path) -> None:
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
    assert details_payload["aliases"]["champion"] == "phase14-returns-intelligence-v1"

    promote_response = client.post(
        "/api/v1/ml-registry/models/return_risk_model/promote",
        params={"artifact_dir": str(artifact_dir)},
        json={"candidate_alias": "challenger"},
    )
    assert promote_response.status_code == 200, promote_response.text
    promote_payload = promote_response.json()
    assert promote_payload["aliases"]["champion"] == "phase15-return-risk-model-v2"

    rollback_response = client.post(
        "/api/v1/ml-registry/models/return_risk_model/rollback",
        params={"artifact_dir": str(artifact_dir)},
        json={},
    )
    assert rollback_response.status_code == 200, rollback_response.text
    rollback_payload = rollback_response.json()
    assert rollback_payload["aliases"]["champion"] == "phase14-returns-intelligence-v1"
