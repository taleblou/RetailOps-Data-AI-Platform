# Project:      RetailOps Data & AI Platform
# Module:       core.ingestion.base
# File:         raw_loader.py
# Path:         core/ingestion/base/raw_loader.py
#
# Summary:      Provides implementation support for the ingestion base workflow.
# Purpose:      Supports the ingestion base layer inside the modular repository architecture.
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
#   - Main types: RawLoader
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, typing, core.ingestion.base.repository
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from typing import Any

from core.ingestion.base.repository import RepositoryProtocol


class RawLoader:
    def __init__(self, repository: RepositoryProtocol) -> None:
        self.repository = repository

    def load(
        self,
        source_id: int,
        import_job_id: int,
        rows: list[dict[str, Any]],
    ) -> int:
        return self.repository.insert_raw_rows(
            source_id=source_id,
            import_job_id=import_job_id,
            rows=rows,
        )
