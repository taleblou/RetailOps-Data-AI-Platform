# Project:      RetailOps Data & AI Platform
# Module:       core.worker
# File:         service.py
# Path:         core/worker/service.py
#
# Summary:      Implements queue persistence and execution orchestration for modular worker jobs.
# Purpose:      Turns the worker service into a reusable background-processing engine with durable JSON queues and run logs.
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
#   - Main types: WorkerRuntime.
#   - Key APIs: enqueue_job(), run_next_job(), run_until_empty(), read_queue_file(), write_queue_file().
#   - Dependencies: dataclasses, json, uuid, pathlib, core.worker.models, core.worker.registry.
#   - Constraints: Queue and run files are JSON for portability, observability, and script compatibility.
#   - Compatibility: Python 3.11+ standard runtime.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.worker.models import WorkerJobRequest, WorkerJobResult
from core.worker.registry import JobRegistry, build_default_registry


@dataclass(slots=True)
class WorkerRuntime:
    queue_path: Path = Path("data/artifacts/worker/queue.json")
    run_dir: Path = Path("data/artifacts/worker/runs")
    registry: JobRegistry = field(default_factory=build_default_registry)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_queue_file(queue_path: Path) -> list[WorkerJobRequest]:
    raw = _load_json(queue_path, default=[])
    if not isinstance(raw, list):
        raise ValueError(f"Invalid worker queue file: {queue_path}")
    jobs = [WorkerJobRequest.from_dict(item) for item in raw if isinstance(item, dict)]
    return sorted(jobs, key=lambda item: (item.priority, item.created_at, item.job_id))


def write_queue_file(queue_path: Path, jobs: list[WorkerJobRequest]) -> None:
    _write_json(queue_path, [job.to_dict() for job in jobs])


def enqueue_job(
    runtime: WorkerRuntime,
    *,
    job_type: str,
    payload: dict[str, Any],
    priority: int = 100,
    max_attempts: int = 3,
    tags: list[str] | None = None,
) -> WorkerJobRequest:
    runtime.registry.get_handler(job_type)
    jobs = read_queue_file(runtime.queue_path)
    job = WorkerJobRequest(
        job_id=f"job_{uuid.uuid4().hex[:12]}",
        job_type=job_type,
        payload=payload,
        created_at=_utc_now_iso(),
        max_attempts=max_attempts,
        priority=priority,
        tags=list(tags or []),
    )
    jobs.append(job)
    write_queue_file(runtime.queue_path, jobs)
    return job


def _persist_result(runtime: WorkerRuntime, result: WorkerJobResult) -> None:
    status_dir = runtime.run_dir / result.status
    status_dir.mkdir(parents=True, exist_ok=True)
    _write_json(status_dir / f"{result.job_id}.json", result.to_dict())


def run_next_job(runtime: WorkerRuntime) -> WorkerJobResult | None:
    jobs = read_queue_file(runtime.queue_path)
    if not jobs:
        return None
    job = jobs.pop(0)
    write_queue_file(runtime.queue_path, jobs)
    started_at = _utc_now_iso()
    try:
        handler = runtime.registry.get_handler(job.job_type)
        details = handler(job.payload)
        artifact_paths: list[str] = []
        for key in ["artifact_path", "artifact_root"]:
            if key in details and details.get(key):
                artifact_paths.append(str(details[key]))
        if isinstance(details.get("generated_files"), dict):
            artifact_paths.extend(str(path) for path in details["generated_files"].values())
        result = WorkerJobResult(
            job_id=job.job_id,
            job_type=job.job_type,
            status="completed",
            attempts=1,
            started_at=started_at,
            finished_at=_utc_now_iso(),
            artifact_paths=artifact_paths,
            details=details,
        )
    except Exception as exc:
        result = WorkerJobResult(
            job_id=job.job_id,
            job_type=job.job_type,
            status="failed",
            attempts=1,
            started_at=started_at,
            finished_at=_utc_now_iso(),
            error_message=str(exc),
        )
    _persist_result(runtime, result)
    return result


def run_until_empty(runtime: WorkerRuntime, max_jobs: int | None = None) -> list[WorkerJobResult]:
    results: list[WorkerJobResult] = []
    processed = 0
    while True:
        if max_jobs is not None and processed >= max_jobs:
            break
        result = run_next_job(runtime)
        if result is None:
            break
        results.append(result)
        processed += 1
    return results


def get_worker_summary(runtime: WorkerRuntime) -> dict[str, Any]:
    queue_jobs = read_queue_file(runtime.queue_path)
    completed_dir = runtime.run_dir / "completed"
    failed_dir = runtime.run_dir / "failed"
    completed_runs = sorted(completed_dir.glob("*.json")) if completed_dir.exists() else []
    failed_runs = sorted(failed_dir.glob("*.json")) if failed_dir.exists() else []
    return {
        "job_types": runtime.registry.list_job_types(),
        "queued_jobs": len(queue_jobs),
        "completed_runs": len(completed_runs),
        "failed_runs": len(failed_runs),
        "queue_path": str(runtime.queue_path),
        "run_dir": str(runtime.run_dir),
    }
