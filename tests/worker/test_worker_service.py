# Project:      RetailOps Data & AI Platform
# Module:       tests.worker
# File:         test_worker_service.py
# Path:         tests/worker/test_worker_service.py
#
# Summary:      Validates the modular worker queue and built-in batch jobs.
# Purpose:      Prevents regressions in durable worker execution, run logging, and job orchestration.
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
#   - Key APIs: test_worker_runs_forecast_and_pro_bundle_jobs, test_worker_cli_drains_queue.
#   - Dependencies: json, subprocess, sys, pathlib, core.worker.service.
#   - Constraints: Uses temporary directories and deterministic sample uploads.
#   - Compatibility: Python 3.11+ with pytest.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from core.worker.service import WorkerRuntime, enqueue_job, get_worker_summary, run_until_empty


def _write_forecasting_upload(tmp_path: Path) -> tuple[str, Path]:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_id = "worker_forecasting_upload"
    csv_path = uploads_dir / f"{upload_id}_orders.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,order_date,sku,quantity,unit_price,category,store_code,on_hand_qty",
                "1,2026-03-01,SKU-001,4,10.0,beverages,HEL-01,25",
                "2,2026-03-02,SKU-001,5,10.0,beverages,HEL-01,24",
                "3,2026-03-03,SKU-001,6,10.0,beverages,HEL-01,22",
                "4,2026-03-04,SKU-001,5,10.0,beverages,HEL-01,21",
                "5,2026-03-05,SKU-001,7,10.0,beverages,HEL-01,20",
                "6,2026-03-06,SKU-002,2,20.0,snacks,HEL-02,30",
                "7,2026-03-07,SKU-002,3,20.0,snacks,HEL-02,29",
                "8,2026-03-08,SKU-002,4,20.0,snacks,HEL-02,28",
                "9,2026-03-09,SKU-002,3,20.0,snacks,HEL-02,27",
                "10,2026-03-10,SKU-002,5,20.0,snacks,HEL-02,26",
            ]
        ),
        encoding="utf-8",
    )
    metadata_path = uploads_dir / f"{upload_id}.json"
    metadata_path.write_text(
        json.dumps(
            {
                "upload_id": upload_id,
                "filename": "orders.csv",
                "stored_path": str(csv_path),
                "mapping": {"order_date": "order_date", "sku": "sku", "quantity": "quantity"},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return upload_id, uploads_dir


def test_worker_runs_forecast_and_pro_bundle_jobs(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_forecasting_upload(tmp_path)
    runtime = WorkerRuntime(
        queue_path=tmp_path / "worker" / "queue.json", run_dir=tmp_path / "worker" / "runs"
    )
    enqueue_job(
        runtime,
        job_type="forecast_batch",
        payload={
            "upload_id": upload_id,
            "uploads_dir": str(uploads_dir),
            "artifact_dir": str(tmp_path / "artifacts" / "forecasts"),
            "refresh": True,
        },
    )
    enqueue_job(
        runtime,
        job_type="pro_platform_bundle",
        payload={"artifact_dir": str(tmp_path / "artifacts" / "pro_platform"), "refresh": True},
    )
    results = run_until_empty(runtime)
    assert len(results) == 2
    assert all(item.status == "completed" for item in results)
    summary = get_worker_summary(runtime)
    assert summary["queued_jobs"] == 0
    assert summary["completed_runs"] == 2


def test_worker_cli_drains_queue(tmp_path: Path) -> None:
    upload_id, uploads_dir = _write_forecasting_upload(tmp_path)
    queue_path = tmp_path / "queue.json"
    run_dir = tmp_path / "runs"
    enqueue_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "core.worker.main",
            "--queue-path",
            str(queue_path),
            "--run-dir",
            str(run_dir),
            "enqueue",
            "forecast_batch",
            "--payload",
            json.dumps(
                {
                    "upload_id": upload_id,
                    "uploads_dir": str(uploads_dir),
                    "artifact_dir": str(tmp_path / "artifacts" / "forecasts"),
                    "refresh": True,
                }
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "forecast_batch" in enqueue_result.stdout
    drain_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "core.worker.main",
            "--queue-path",
            str(queue_path),
            "--run-dir",
            str(run_dir),
            "drain",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "completed" in drain_result.stdout
