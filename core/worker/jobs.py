# Project:      RetailOps Data & AI Platform
# Module:       core.worker
# File:         jobs.py
# Path:         core/worker/jobs.py
#
# Summary:      Implements built-in worker jobs for analytics, serving, monitoring, and Pro bundles.
# Purpose:      Gives the worker service a real task catalog instead of a heartbeat-only process.
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
#   - Main types: JobHandler.
#   - Key APIs: run_forecast_batch_job(), run_shipment_risk_job(), run_stockout_job(), run_reorder_job(), run_returns_job(), run_serving_batch_job(), run_monitoring_job(), run_pro_bundle_job().
#   - Dependencies: pathlib and repository service modules.
#   - Constraints: Payload keys must stay aligned with artifact directories and upload metadata used elsewhere in the repository.
#   - Compatibility: Python 3.11+ with repository runtime dependencies.

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from core.monitoring.service import get_or_create_monitoring_artifact
from core.serving.service import get_or_create_batch_serving_artifact
from modules.advanced_serving.service import build_advanced_serving_artifact
from modules.cdc.service import build_cdc_artifact
from modules.feature_store.service import build_feature_store_artifact
from modules.forecasting.service import get_or_create_batch_forecast_artifact
from modules.lakehouse.service import build_lakehouse_artifact
from modules.metadata.service import build_metadata_artifact
from modules.query_layer.service import build_query_layer_artifact
from modules.reorder_engine.service import get_or_create_reorder_artifact
from modules.returns_intelligence.service import get_or_create_returns_artifact
from modules.shipment_risk.service import get_or_create_shipment_risk_artifact
from modules.stockout_intelligence.service import get_or_create_stockout_artifact
from modules.streaming.service import build_streaming_artifact

JobHandler = Callable[[dict[str, Any]], dict[str, Any]]


def _path(payload: dict[str, Any], key: str, default: str) -> Path:
    return Path(str(payload.get(key, default)))


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"Worker job payload is missing '{key}'.")
    return value


def run_forecast_batch_job(payload: dict[str, Any]) -> dict[str, Any]:
    upload_id = _require_text(payload, "upload_id")
    artifact = get_or_create_batch_forecast_artifact(
        upload_id=upload_id,
        uploads_dir=_path(payload, "uploads_dir", "data/uploads"),
        artifact_dir=_path(payload, "artifact_dir", "data/artifacts/forecasts"),
        refresh=bool(payload.get("refresh", False)),
    )
    return {
        "job_surface": "forecasting",
        "upload_id": upload_id,
        "artifact_path": str(artifact.get("artifact_path", "")),
        "summary": artifact.get("summary", {}),
    }


def run_shipment_risk_job(payload: dict[str, Any]) -> dict[str, Any]:
    upload_id = _require_text(payload, "upload_id")
    artifact = get_or_create_shipment_risk_artifact(
        upload_id=upload_id,
        uploads_dir=_path(payload, "uploads_dir", "data/uploads"),
        artifact_dir=_path(payload, "artifact_dir", "data/artifacts/shipment_risk"),
        refresh=bool(payload.get("refresh", False)),
    )
    return {
        "job_surface": "shipment_risk",
        "upload_id": upload_id,
        "artifact_path": str(artifact.get("artifact_path", "")),
        "summary": artifact.get("summary", {}),
    }


def run_stockout_job(payload: dict[str, Any]) -> dict[str, Any]:
    upload_id = _require_text(payload, "upload_id")
    artifact = get_or_create_stockout_artifact(
        upload_id=upload_id,
        uploads_dir=_path(payload, "uploads_dir", "data/uploads"),
        artifact_dir=_path(payload, "artifact_dir", "data/artifacts/stockout_risk"),
        refresh=bool(payload.get("refresh", False)),
    )
    return {
        "job_surface": "stockout_intelligence",
        "upload_id": upload_id,
        "artifact_path": str(artifact.get("artifact_path", "")),
        "summary": artifact.get("summary", {}),
    }


def run_reorder_job(payload: dict[str, Any]) -> dict[str, Any]:
    upload_id = _require_text(payload, "upload_id")
    artifact = get_or_create_reorder_artifact(
        upload_id=upload_id,
        uploads_dir=_path(payload, "uploads_dir", "data/uploads"),
        forecast_artifact_dir=_path(payload, "forecast_artifact_dir", "data/artifacts/forecasts"),
        stockout_artifact_dir=_path(
            payload, "stockout_artifact_dir", "data/artifacts/stockout_risk"
        ),
        artifact_dir=_path(payload, "artifact_dir", "data/artifacts/reorder"),
        refresh=bool(payload.get("refresh", False)),
    )
    return {
        "job_surface": "reorder_engine",
        "upload_id": upload_id,
        "artifact_path": str(artifact.get("artifact_path", "")),
        "summary": artifact.get("summary", {}),
    }


def run_returns_job(payload: dict[str, Any]) -> dict[str, Any]:
    upload_id = _require_text(payload, "upload_id")
    artifact = get_or_create_returns_artifact(
        upload_id=upload_id,
        uploads_dir=_path(payload, "uploads_dir", "data/uploads"),
        artifact_dir=_path(payload, "artifact_dir", "data/artifacts/returns_risk"),
        refresh=bool(payload.get("refresh", False)),
    )
    return {
        "job_surface": "returns_intelligence",
        "upload_id": upload_id,
        "artifact_path": str(artifact.get("artifact_path", "")),
        "summary": artifact.get("summary", {}),
    }


def run_serving_batch_job(payload: dict[str, Any]) -> dict[str, Any]:
    upload_id = _require_text(payload, "upload_id")
    artifact = get_or_create_batch_serving_artifact(
        upload_id=upload_id,
        uploads_dir=_path(payload, "uploads_dir", "data/uploads"),
        forecast_artifact_dir=_path(payload, "forecast_artifact_dir", "data/artifacts/forecasts"),
        shipment_artifact_dir=_path(
            payload, "shipment_artifact_dir", "data/artifacts/shipment_risk"
        ),
        stockout_artifact_dir=_path(
            payload, "stockout_artifact_dir", "data/artifacts/stockout_risk"
        ),
        artifact_dir=_path(payload, "artifact_dir", "data/artifacts/serving"),
        refresh=bool(payload.get("refresh", False)),
    )
    return {
        "job_surface": "serving",
        "upload_id": upload_id,
        "artifact_path": str(artifact.get("artifact_path", "")),
        "jobs": artifact.get("jobs", []),
    }


def run_monitoring_job(payload: dict[str, Any]) -> dict[str, Any]:
    upload_id = _require_text(payload, "upload_id")
    artifact = get_or_create_monitoring_artifact(
        upload_id=upload_id,
        uploads_dir=_path(payload, "uploads_dir", "data/uploads"),
        forecast_artifact_dir=_path(payload, "forecast_artifact_dir", "data/artifacts/forecasts"),
        shipment_artifact_dir=_path(
            payload, "shipment_artifact_dir", "data/artifacts/shipment_risk"
        ),
        stockout_artifact_dir=_path(
            payload, "stockout_artifact_dir", "data/artifacts/stockout_risk"
        ),
        serving_artifact_dir=_path(payload, "serving_artifact_dir", "data/artifacts/serving"),
        registry_artifact_dir=_path(payload, "registry_artifact_dir", "data/artifacts/ml_registry"),
        artifact_dir=_path(payload, "artifact_dir", "data/artifacts/monitoring"),
        override_dir=_path(payload, "override_dir", "data/artifacts/monitoring/overrides"),
        refresh=bool(payload.get("refresh", False)),
    )
    return {
        "job_surface": "monitoring",
        "upload_id": upload_id,
        "artifact_path": str(artifact.get("artifact_path", "")),
        "summary": artifact.get("summary", {}),
    }


def run_pro_bundle_job(payload: dict[str, Any]) -> dict[str, Any]:
    artifact_root = _path(payload, "artifact_dir", "data/artifacts/pro_platform")
    refresh = bool(payload.get("refresh", False))
    modules = {
        "cdc": build_cdc_artifact(artifact_root / "cdc", refresh),
        "streaming": build_streaming_artifact(artifact_root / "streaming", refresh),
        "lakehouse": build_lakehouse_artifact(artifact_root / "lakehouse", refresh),
        "query_layer": build_query_layer_artifact(artifact_root / "query_layer", refresh),
        "metadata": build_metadata_artifact(artifact_root / "metadata", refresh),
        "feature_store": build_feature_store_artifact(artifact_root / "feature_store", refresh),
        "advanced_serving": build_advanced_serving_artifact(
            artifact_root / "advanced_serving", refresh
        ),
    }
    return {
        "job_surface": "pro_platform",
        "artifact_root": str(artifact_root),
        "module_count": len(modules),
        "deployment_ready_count": sum(
            1 for item in modules.values() if item.get("status") == "deployment_ready"
        ),
        "modules": modules,
    }
