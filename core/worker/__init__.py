# Project:      RetailOps Data & AI Platform
# Module:       core.worker
# File:         __init__.py
# Path:         core/worker/__init__.py
#
# Summary:      Exposes the modular worker package surface and key runtime helpers.
# Purpose:      Keeps worker queue models and orchestration helpers importable without deep module paths.
# Scope:        internal
# Status:       internal
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
#   - Main types: WorkerJobRequest, WorkerJobResult, WorkerRuntime.
#   - Key APIs: enqueue_job(), run_next_job(), run_until_empty(), get_worker_summary().
#   - Dependencies: core.worker.models, core.worker.service.
#   - Constraints: Package exports should stay lightweight and avoid introducing import cycles.
#   - Compatibility: Python 3.11+ standard runtime.

from core.worker.models import WorkerJobRequest, WorkerJobResult
from core.worker.service import (
    WorkerRuntime,
    enqueue_job,
    get_worker_summary,
    run_next_job,
    run_until_empty,
)

__all__ = [
    "WorkerJobRequest",
    "WorkerJobResult",
    "WorkerRuntime",
    "enqueue_job",
    "get_worker_summary",
    "run_next_job",
    "run_until_empty",
]
