# Project:      RetailOps Data & AI Platform
# Module:       modules.advanced_serving.bentoml
# File:         service.py
# Path:         modules/advanced_serving/bentoml/service.py
#
# Summary:      Exposes a lightweight BentoML runtime for advanced-serving validation.
# Purpose:      Provides a realistic local runtime that reports primary and shadow routing decisions for Pro serving.
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
#   - Main types: None.
#   - Key APIs: svc, predict
#   - Dependencies: __future__, bentoml, bentoml.io, modules.advanced_serving.service
#   - Constraints: Runtime response shape should stay stable because deployment smoke tests depend on it.
#   - Compatibility: Python 3.11+ with BentoML-compatible runtime dependencies.

from __future__ import annotations

from bentoml import Service
from bentoml.io import JSON

from modules.advanced_serving.service import route_runtime_request

svc = Service(name="retailops-advanced-serving")


@svc.api(input=JSON(), output=JSON())
def predict(payload: dict[str, object]) -> dict[str, object]:
    routing = route_runtime_request(dict(payload))
    return {
        "status": "deployment_ready",
        "received": payload,
        "routing": routing,
        "message": "RetailOps BentoML runtime is active with primary and shadow routing.",
    }
