from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from modules.advanced_serving.service import build_phase20_advanced_serving_artifact
from modules.cdc.service import build_phase20_cdc_artifact
from modules.feature_store.service import build_phase20_feature_store_artifact
from modules.lakehouse.service import build_phase20_lakehouse_artifact
from modules.metadata.service import build_phase20_metadata_artifact
from modules.query_layer.service import build_phase20_query_layer_artifact
from modules.streaming.service import build_phase20_streaming_artifact


def test_phase20_services_generate_all_pro_platform_blueprints(tmp_path: Path) -> None:
    cdc = build_phase20_cdc_artifact(tmp_path / "cdc", refresh=True)
    streaming = build_phase20_streaming_artifact(tmp_path / "streaming", refresh=True)
    lakehouse = build_phase20_lakehouse_artifact(tmp_path / "lakehouse", refresh=True)
    query_layer = build_phase20_query_layer_artifact(tmp_path / "query_layer", refresh=True)
    metadata = build_phase20_metadata_artifact(tmp_path / "metadata", refresh=True)
    feature_store = build_phase20_feature_store_artifact(tmp_path / "feature_store", refresh=True)
    advanced_serving = build_phase20_advanced_serving_artifact(
        tmp_path / "advanced_serving",
        refresh=True,
    )

    assert cdc["connector_name"] == "retailops-postgres-cdc"
    assert streaming["runtime"] == "redpanda"
    assert lakehouse["table_format"] == "iceberg"
    assert query_layer["engine"] == "trino"
    assert metadata["platform"] == "openmetadata"
    assert feature_store["engine"] == "feast"
    assert advanced_serving["platform"] == "bentoml"

    for payload in [
        cdc,
        streaming,
        lakehouse,
        query_layer,
        metadata,
        feature_store,
        advanced_serving,
    ]:
        assert Path(payload["artifact_path"]).exists()


def test_phase20_api_exposes_module_blueprints_and_summary(tmp_path: Path) -> None:
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)
    artifact_root = tmp_path / "pro_platform"

    summary_response = client.get(
        "/api/v1/pro-platform/summary",
        params={"artifact_dir": str(artifact_root), "refresh": "true"},
    )
    assert summary_response.status_code == 200, summary_response.text
    summary_payload = summary_response.json()
    assert summary_payload["phase"] == 20
    assert summary_payload["module_count"] == 7
    assert "query_layer" in summary_payload["modules"]

    endpoints = {
        "/api/v1/pro/cdc/blueprint": (artifact_root / "cdc", "connector_name"),
        "/api/v1/pro/streaming/blueprint": (artifact_root / "streaming", "runtime"),
        "/api/v1/pro/lakehouse/blueprint": (artifact_root / "lakehouse", "table_format"),
        "/api/v1/pro/query-layer/blueprint": (artifact_root / "query_layer", "engine"),
        "/api/v1/pro/metadata/blueprint": (artifact_root / "metadata", "platform"),
        "/api/v1/pro/feature-store/blueprint": (artifact_root / "feature_store", "engine"),
        "/api/v1/pro/advanced-serving/blueprint": (
            artifact_root / "advanced_serving",
            "platform",
        ),
    }
    for endpoint, (artifact_dir, required_key) in endpoints.items():
        response = client.get(
            endpoint, params={"artifact_dir": str(artifact_dir), "refresh": "true"}
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert required_key in payload


def test_phase20_static_files_and_docs_exist() -> None:
    required_files = [
        Path("docs/pro_data_platform_phase20.md"),
        Path("docs/phase_1_to_20_gap_report.md"),
        Path("docs/phase_1_to_20_audit.md"),
        Path("compose/compose.streaming.yaml"),
        Path("compose/compose.query.yaml"),
        Path("compose/compose.feature_store.yaml"),
        Path("compose/compose.advanced_serving.yaml"),
        Path("modules/query_layer/config/catalogs/postgres.properties"),
        Path("modules/query_layer/config/catalogs/iceberg.properties"),
        Path("modules/feature_store/repo/feature_store.yaml"),
        Path("modules/advanced_serving/bentofile.yaml"),
    ]
    for path in required_files:
        assert path.exists(), f"Missing expected phase 20 file: {path}"
