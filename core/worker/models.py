# Project:      RetailOps Data & AI Platform
# Module:       core.worker
# File:         models.py
# Path:         core/worker/models.py
#
# Summary:      Defines typed request and result models for modular worker jobs.
# Purpose:      Standardizes worker queue payloads, lifecycle metadata, and persisted execution results.
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
#   - Main types: WorkerJobRequest, WorkerJobResult.
#   - Key APIs: to_dict(), from_dict().
#   - Dependencies: __future__, dataclasses, typing.
#   - Constraints: Field names should remain stable because queue files and worker result files are persisted as JSON.
#   - Compatibility: Python 3.11+ standard runtime.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WorkerJobRequest:
    job_id: str
    job_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    max_attempts: int = 3
    priority: int = 100
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "payload": self.payload,
            "created_at": self.created_at,
            "max_attempts": self.max_attempts,
            "priority": self.priority,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorkerJobRequest:
        return cls(
            job_id=str(payload.get("job_id", "")),
            job_type=str(payload.get("job_type", "")),
            payload=dict(payload.get("payload") or {}),
            created_at=str(payload.get("created_at", "")),
            max_attempts=int(payload.get("max_attempts", 3)),
            priority=int(payload.get("priority", 100)),
            tags=[str(item) for item in payload.get("tags", [])],
        )


@dataclass(slots=True)
class WorkerJobResult:
    job_id: str
    job_type: str
    status: str
    attempts: int
    started_at: str
    finished_at: str
    artifact_paths: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "attempts": self.attempts,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "artifact_paths": self.artifact_paths,
            "details": self.details,
            "error_message": self.error_message,
        }
