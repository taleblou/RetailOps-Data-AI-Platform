# Project:      RetailOps Data & AI Platform
# Module:       tests.business
# File:         test_executive_scorecards.py
# Path:         tests/business/test_executive_scorecards.py
#
# Summary:      Contains automated tests for the business workflows and behaviors.
# Purpose:      Validates business behavior and protects the repository against regressions.
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
#   - Key APIs: test_executive_scorecards_catalog_includes_new_reports, test_executive_scorecards_operating_and_benchmark_reports, test_executive_scorecards_markdown_and_demand_supply_reports, test_executive_scorecards_customer_and_cash_reports
#   - Dependencies: __future__, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, tests.business.test_portfolio_reporting, ...
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from core.api.main import create_app
from core.ingestion.base.repository import MemoryRepository
from tests.business.test_portfolio_reporting import _write_portfolio_reporting_upload


def test_executive_scorecards_catalog_includes_new_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_portfolio_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    response = client.get(
        "/api/v1/business-reports/catalog",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert response.status_code == 200, response.text
    report_names = {item["report_name"] for item in response.json()["report_index"]}
    assert "operating_executive_scorecard_report" in report_names
    assert "internal_benchmarking_report" in report_names
    assert "markdown_clearance_optimization_report" in report_names
    assert "demand_supply_risk_matrix_report" in report_names
    assert "customer_journey_friction_report" in report_names
    assert "cash_conversion_risk_report" in report_names


def test_executive_scorecards_operating_and_benchmark_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_portfolio_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    scorecard = client.get(
        "/api/v1/business-reports/operating-executive-scorecard",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
        },
    )
    assert scorecard.status_code == 200, scorecard.text
    score_payload = scorecard.json()
    assert score_payload["summary"]["pillar_count"] == 5
    assert score_payload["summary"]["overall_score"] > 0
    assert score_payload["pillars"]

    benchmark = client.get(
        "/api/v1/business-reports/internal-benchmarking",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "limit": 10,
        },
    )
    assert benchmark.status_code == 200, benchmark.text
    benchmark_payload = benchmark.json()
    assert benchmark_payload["summary"]["store_count"] >= 3
    assert benchmark_payload["summary"]["category_count"] >= 3
    assert benchmark_payload["store_benchmarks"]
    assert benchmark_payload["category_benchmarks"]


def test_executive_scorecards_markdown_and_demand_supply_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_portfolio_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    markdown = client.get(
        "/api/v1/business-reports/markdown-clearance-optimization",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "limit": 12,
        },
    )
    assert markdown.status_code == 200, markdown.text
    markdown_payload = markdown.json()
    assert markdown_payload["summary"]["clearance_candidate_count"] >= 1
    assert markdown_payload["summary"]["expected_cash_release"] > 0
    assert markdown_payload["candidates"]

    demand_supply = client.get(
        "/api/v1/business-reports/demand-supply-risk-matrix",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "limit": 15,
        },
    )
    assert demand_supply.status_code == 200, demand_supply.text
    matrix_payload = demand_supply.json()
    assert matrix_payload["summary"]["risk_zone_count"] >= 2
    assert matrix_payload["risk_zones"]
    assert matrix_payload["focus_skus"]


def test_executive_scorecards_customer_and_cash_reports(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_portfolio_reporting_upload(tmp_path)
    artifact_dir = tmp_path / "artifacts"
    app = create_app(repository=MemoryRepository())
    client = TestClient(app)

    friction = client.get(
        "/api/v1/business-reports/customer-journey-friction",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "limit": 15,
        },
    )
    assert friction.status_code == 200, friction.text
    friction_payload = friction.json()
    assert friction_payload["summary"]["friction_customer_count"] >= 1
    assert friction_payload["summary"]["revenue_at_risk"] > 0
    assert friction_payload["stages"]
    assert friction_payload["customers"]

    cash = client.get(
        "/api/v1/business-reports/cash-conversion-risk",
        params={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(artifact_dir),
            "refresh": "true",
            "limit": 20,
        },
    )
    assert cash.status_code == 200, cash.text
    cash_payload = cash.json()
    assert cash_payload["summary"]["total_cash_risk"] > 0
    assert cash_payload["drivers"]
    assert cash_payload["focus_entities"]
