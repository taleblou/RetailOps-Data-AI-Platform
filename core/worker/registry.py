# Project:      RetailOps Data & AI Platform
# Module:       core.worker
# File:         registry.py
# Path:         core/worker/registry.py
#
# Summary:      Registers the built-in worker jobs exposed by the modular worker service.
# Purpose:      Provides a stable lookup layer between queue job types and concrete execution handlers.
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
#   - Main types: JobRegistry.
#   - Key APIs: build_default_registry(), get_handler().
#   - Dependencies: dataclasses, core.worker.jobs.
#   - Constraints: Job type names are part of the operator-facing interface and should remain backward compatible.
#   - Compatibility: Python 3.11+ standard runtime.

from __future__ import annotations

from dataclasses import dataclass, field

from core.worker.jobs import (
    JobHandler,
    run_forecast_batch_job,
    run_monitoring_job,
    run_pro_bundle_job,
    run_reorder_job,
    run_returns_job,
    run_serving_batch_job,
    run_shipment_risk_job,
    run_stockout_job,
)


@dataclass(slots=True)
class JobRegistry:
    handlers: dict[str, JobHandler] = field(default_factory=dict)

    def register(self, job_type: str, handler: JobHandler) -> None:
        self.handlers[job_type] = handler

    def get_handler(self, job_type: str) -> JobHandler:
        if job_type not in self.handlers:
            raise KeyError(f"Unknown worker job type: {job_type}")
        return self.handlers[job_type]

    def list_job_types(self) -> list[str]:
        return sorted(self.handlers)


def build_default_registry() -> JobRegistry:
    registry = JobRegistry()
    registry.register("forecast_batch", run_forecast_batch_job)
    registry.register("shipment_risk_batch", run_shipment_risk_job)
    registry.register("stockout_batch", run_stockout_job)
    registry.register("reorder_batch", run_reorder_job)
    registry.register("returns_batch", run_returns_job)
    registry.register("serving_batch", run_serving_batch_job)
    registry.register("monitoring_batch", run_monitoring_job)
    registry.register("pro_platform_bundle", run_pro_bundle_job)
    return registry
