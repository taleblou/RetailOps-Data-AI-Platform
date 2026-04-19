# Project:      RetailOps Data & AI Platform
# Module:       core.ingestion.base
# File:         state_store.py
# Path:         core/ingestion/base/state_store.py
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
#   - Main types: StateStore
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, datetime, core.ingestion.base.models, core.ingestion.base.repository
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from datetime import UTC, datetime

from core.ingestion.base.models import ConnectorState
from core.ingestion.base.repository import RepositoryProtocol


class StateStore:
    def __init__(self, repository: RepositoryProtocol) -> None:
        self.repository = repository

    def get(self, source_id: int) -> ConnectorState | None:
        return self.repository.get_state(source_id)

    def save_success(
        self,
        source_id: int,
        cursor_value: str | None,
        rows_loaded: int,
    ) -> ConnectorState:
        current = self.repository.get_state(source_id)
        state = ConnectorState(
            source_id=source_id,
            last_sync_at=datetime.now(tz=UTC),
            cursor_value=cursor_value or str(rows_loaded),
            error_count=current.error_count if current else 0,
            retry_count=current.retry_count if current else 0,
            last_error=None,
            last_run_status="success",
        )
        return self.repository.upsert_state(state)

    def save_failure(
        self,
        source_id: int,
        cursor_value: str | None,
        error_message: str,
    ) -> ConnectorState:
        current = self.repository.get_state(source_id)
        state = ConnectorState(
            source_id=source_id,
            last_sync_at=current.last_sync_at if current else None,
            cursor_value=cursor_value,
            error_count=(current.error_count if current else 0) + 1,
            retry_count=(current.retry_count if current else 0) + 1,
            last_error=error_message,
            last_run_status="failed",
        )
        return self.repository.upsert_state(state)
