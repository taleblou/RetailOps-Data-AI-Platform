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
