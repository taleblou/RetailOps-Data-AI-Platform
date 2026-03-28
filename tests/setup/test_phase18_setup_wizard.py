from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository


def test_phase18_setup_api_flow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    repository = MemoryRepository()
    app = create_app(repository=repository)
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/setup/sessions",
        json={
            "store_name": "RetailOps Demo Store",
            "store_code": "DEMO-01",
            "sample_mode": True,
        },
    )
    assert create_response.status_code == 201, create_response.text
    session_payload = create_response.json()
    session_id = session_payload["session_id"]
    assert session_payload["progress_percent"] >= 11

    source_response = client.post(
        f"/api/v1/setup/sessions/{session_id}/source",
        json={
            "source_type": "csv",
            "source_name": "Demo CSV source",
            "config": {},
        },
    )
    assert source_response.status_code == 200, source_response.text

    test_response = client.post(f"/api/v1/setup/sessions/{session_id}/test-connection")
    assert test_response.status_code == 200, test_response.text
    assert test_response.json()["source"]["discovered_columns"]

    mapping_response = client.post(
        f"/api/v1/setup/sessions/{session_id}/mapping",
        json={"mappings": {}},
    )
    assert mapping_response.status_code == 200, mapping_response.text
    assert mapping_response.json()["mapping"]["order_id"]

    import_response = client.post(f"/api/v1/setup/sessions/{session_id}/import")
    assert import_response.status_code == 200, import_response.text

    dbt_response = client.post(f"/api/v1/setup/sessions/{session_id}/dbt-run")
    assert dbt_response.status_code == 200, dbt_response.text
    dbt_payload = dbt_response.json()
    assert dbt_payload["transform_summary"]["total_orders"] > 0

    modules_response = client.post(
        f"/api/v1/setup/sessions/{session_id}/enable-modules",
        json={"modules": ["analytics_kpi", "forecasting", "monitoring"]},
    )
    assert modules_response.status_code == 200, modules_response.text

    train_response = client.post(f"/api/v1/setup/sessions/{session_id}/train")
    assert train_response.status_code == 200, train_response.text
    assert train_response.json()["training_summary"]["artifact_path"]

    dashboards_response = client.post(f"/api/v1/setup/sessions/{session_id}/publish-dashboards")
    assert dashboards_response.status_code == 200, dashboards_response.text
    dashboards_payload = dashboards_response.json()
    assert dashboards_payload["dashboard_summary"]["dashboard_title"]
    assert dashboards_payload["progress_percent"] == 100
    assert Path(dashboards_payload["artifacts"]["dashboard_artifact_path"]).exists()
    assert len(dashboards_payload["logs"]) >= 7


def test_phase18_setup_wizard_html_pages(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    home_response = client.get("/setup/wizard")
    assert home_response.status_code == 200
    assert "RetailOps Phase 18 Setup Wizard" in home_response.text

    start_response = client.post(
        "/setup/wizard/start",
        data={
            "store_name": "Wizard Demo Store",
            "store_code": "WIZ-01",
            "sample_mode": "on",
        },
        follow_redirects=False,
    )
    assert start_response.status_code == 303
    redirect_url = start_response.headers["location"]
    assert "/setup/sessions/" in redirect_url and "/wizard" in redirect_url

    detail_response = client.get(redirect_url)
    assert detail_response.status_code == 200
    assert "Progress" in detail_response.text
    assert "Create store" in detail_response.text
    assert "Run first model training" in detail_response.text
