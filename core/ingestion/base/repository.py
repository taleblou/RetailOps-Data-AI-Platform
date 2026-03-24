from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlparse

from core.ingestion.base.models import (
    ConnectorState,
    SourceCreateRequest,
    SourceErrorRecord,
    SourceRecord,
    SourceStatus,
    SourceType,
)

psycopg_module: Any | None
try:
    import psycopg as _psycopg
except ImportError:  # pragma: no cover
    psycopg_module = None
else:
    psycopg_module = _psycopg


SQLITE_SOURCE_SELECT = (
    "SELECT source_id, name, type, status, config_json, created_at, updated_at "
    "FROM ops_sources WHERE source_id = ?"
)
POSTGRES_SOURCE_SELECT = (
    "SELECT source_id, name, type, status, config_json, created_at, updated_at "
    "FROM ops.sources WHERE source_id = %s"
)
SQLITE_STATE_SELECT = (
    "SELECT source_id, last_sync_at, cursor_value, error_count, retry_count, "
    "last_error, last_run_status FROM ops_connector_state WHERE source_id = ?"
)
POSTGRES_STATE_SELECT = (
    "SELECT source_id, last_sync_at, cursor_value, error_count, retry_count, "
    "last_error, last_run_status FROM ops.connector_state WHERE source_id = %s"
)
SQLITE_ERRORS_SELECT = (
    "SELECT source_id, error_type, message, details_json, created_at "
    "FROM ops_connector_errors WHERE source_id = ? ORDER BY created_at DESC"
)
POSTGRES_ERRORS_SELECT = (
    "SELECT source_id, error_type, message, details_json, created_at "
    "FROM ops.connector_errors WHERE source_id = %s ORDER BY created_at DESC"
)


class RepositoryProtocol(Protocol):
    def ensure_tables(self) -> None: ...

    def create_source(self, request: SourceCreateRequest) -> SourceRecord: ...

    def get_source(self, source_id: int) -> SourceRecord | None: ...

    def update_source_status(self, source_id: int, status: SourceStatus) -> None: ...

    def upsert_state(self, state: ConnectorState) -> ConnectorState: ...

    def get_state(self, source_id: int) -> ConnectorState | None: ...

    def record_error(
        self,
        source_id: int,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None: ...

    def list_errors(self, source_id: int) -> list[SourceErrorRecord]: ...

    def create_import_job(
        self,
        source_id: int,
        source_name: str,
        source_type: SourceType,
    ) -> int: ...

    def finish_import_job(
        self,
        import_job_id: int,
        status: str,
        rows_received: int,
        rows_loaded: int,
        error_message: str | None = None,
    ) -> None: ...

    def create_sync_run(
        self,
        source_name: str,
        cursor_value: str | None,
        sync_mode: str,
    ) -> int: ...

    def finish_sync_run(
        self,
        sync_run_id: int,
        status: str,
        rows_processed: int,
        cursor_value: str | None = None,
        error_message: str | None = None,
    ) -> None: ...

    def insert_raw_rows(
        self,
        source_id: int,
        import_job_id: int,
        rows: list[dict[str, Any]],
    ) -> int: ...


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Unsupported datetime value: {value!r}")


def _require_datetime(value: Any) -> datetime:
    parsed = _parse_datetime(value)
    if parsed is None:
        raise ValueError("Expected datetime value, got None.")
    return parsed


def _normalize_json(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, dict):
        return value
    return {}


def _row_to_mapping(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return dict(row)


class MemoryRepository:
    def __init__(self) -> None:
        self.sources: dict[int, SourceRecord] = {}
        self.states: dict[int, ConnectorState] = {}
        self.errors: dict[int, list[SourceErrorRecord]] = {}
        self.raw_rows: list[dict[str, Any]] = []
        self.import_jobs: dict[int, dict[str, Any]] = {}
        self.sync_runs: dict[int, dict[str, Any]] = {}
        self._source_id = 0
        self._import_job_id = 0
        self._sync_run_id = 0

    def ensure_tables(self) -> None:
        return None

    def create_source(self, request: SourceCreateRequest) -> SourceRecord:
        self._source_id += 1
        current_time = now_utc()
        record = SourceRecord(
            source_id=self._source_id,
            name=request.name,
            type=request.type,
            status=SourceStatus.CREATED,
            config=request.config,
            created_at=current_time,
            updated_at=current_time,
        )
        self.sources[record.source_id] = record
        return record

    def get_source(self, source_id: int) -> SourceRecord | None:
        return self.sources.get(source_id)

    def update_source_status(self, source_id: int, status: SourceStatus) -> None:
        record = self.sources[source_id]
        self.sources[source_id] = record.model_copy(
            update={"status": status, "updated_at": now_utc()}
        )

    def upsert_state(self, state: ConnectorState) -> ConnectorState:
        self.states[state.source_id] = state
        return state

    def get_state(self, source_id: int) -> ConnectorState | None:
        return self.states.get(source_id)

    def record_error(
        self,
        source_id: int,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        record = SourceErrorRecord(
            source_id=source_id,
            error_type=error_type,
            message=message,
            details=details or {},
            created_at=now_utc(),
        )
        self.errors.setdefault(source_id, []).append(record)

    def list_errors(self, source_id: int) -> list[SourceErrorRecord]:
        return self.errors.get(source_id, [])

    def create_import_job(
        self,
        source_id: int,
        source_name: str,
        source_type: SourceType,
    ) -> int:
        self._import_job_id += 1
        self.import_jobs[self._import_job_id] = {
            "source_id": source_id,
            "source_name": source_name,
            "source_type": source_type.value,
            "status": "running",
        }
        return self._import_job_id

    def finish_import_job(
        self,
        import_job_id: int,
        status: str,
        rows_received: int,
        rows_loaded: int,
        error_message: str | None = None,
    ) -> None:
        self.import_jobs[import_job_id].update(
            {
                "status": status,
                "rows_received": rows_received,
                "rows_loaded": rows_loaded,
                "error_message": error_message,
            }
        )

    def create_sync_run(
        self,
        source_name: str,
        cursor_value: str | None,
        sync_mode: str,
    ) -> int:
        self._sync_run_id += 1
        self.sync_runs[self._sync_run_id] = {
            "source_name": source_name,
            "cursor_value": cursor_value,
            "sync_mode": sync_mode,
            "status": "running",
        }
        return self._sync_run_id

    def finish_sync_run(
        self,
        sync_run_id: int,
        status: str,
        rows_processed: int,
        cursor_value: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self.sync_runs[sync_run_id].update(
            {
                "status": status,
                "rows_processed": rows_processed,
                "cursor_value": cursor_value,
                "error_message": error_message,
            }
        )

    def insert_raw_rows(
        self,
        source_id: int,
        import_job_id: int,
        rows: list[dict[str, Any]],
    ) -> int:
        for row_num, row in enumerate(rows, start=1):
            self.raw_rows.append(
                {
                    "source_id": source_id,
                    "import_job_id": import_job_id,
                    "row_num": row_num,
                    "payload_json": row,
                }
            )
        return len(rows)


class SqlRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        parsed = urlparse(database_url)
        self.scheme = parsed.scheme
        self.sqlite_path = parsed.path or ":memory:"

    @contextmanager
    def connect(self) -> Iterator[Any]:
        if self.scheme.startswith("sqlite"):
            sqlite_connection = sqlite3.connect(self.sqlite_path)
            sqlite_connection.row_factory = sqlite3.Row
            try:
                yield sqlite_connection
                sqlite_connection.commit()
            finally:
                sqlite_connection.close()
            return

        if self.scheme.startswith("postgres"):
            if psycopg_module is None:
                raise RuntimeError("psycopg is not installed. Run `uv sync`.")
            postgres_connection = psycopg_module.connect(self.database_url)
            try:
                yield postgres_connection
                postgres_connection.commit()
            finally:
                postgres_connection.close()
            return

        raise ValueError(f"Unsupported database URL scheme: {self.scheme}")

    def ensure_tables(self) -> None:
        statements = (
            self._sqlite_ddl() if self.scheme.startswith("sqlite") else self._postgres_ddl()
        )
        with self.connect() as connection:
            cursor = connection.cursor()
            for statement in statements:
                cursor.execute(statement)
            cursor.close()

    def create_source(self, request: SourceCreateRequest) -> SourceRecord:
        current_time = now_utc()
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                cursor.execute(
                    (
                        "INSERT INTO ops_sources "
                        "(name, type, status, config_json, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        request.name,
                        request.type.value,
                        SourceStatus.CREATED.value,
                        json.dumps(request.config),
                        current_time.isoformat(),
                        current_time.isoformat(),
                    ),
                )
                source_id = int(cursor.lastrowid)
            else:
                cursor.execute(
                    (
                        "INSERT INTO ops.sources "
                        "(name, type, status, config_json, created_at, updated_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING source_id"
                    ),
                    (
                        request.name,
                        request.type.value,
                        SourceStatus.CREATED.value,
                        json.dumps(request.config),
                        current_time,
                        current_time,
                    ),
                )
                source_id = int(cursor.fetchone()[0])
            cursor.close()

        return SourceRecord(
            source_id=source_id,
            name=request.name,
            type=request.type,
            status=SourceStatus.CREATED,
            config=request.config,
            created_at=current_time,
            updated_at=current_time,
        )

    def get_source(self, source_id: int) -> SourceRecord | None:
        with self.connect() as connection:
            cursor = connection.cursor()
            query = (
                SQLITE_SOURCE_SELECT if self.scheme.startswith("sqlite") else POSTGRES_SOURCE_SELECT
            )
            cursor.execute(query, (source_id,))
            values = _row_to_mapping(cursor.fetchone())
            cursor.close()

        if values is None:
            return None

        return SourceRecord(
            source_id=int(values["source_id"]),
            name=str(values["name"]),
            type=SourceType(values["type"]),
            status=SourceStatus(values["status"]),
            config=_normalize_json(values["config_json"]),
            created_at=_require_datetime(values["created_at"]),
            updated_at=_require_datetime(values["updated_at"]),
        )

    def update_source_status(self, source_id: int, status: SourceStatus) -> None:
        current_time = now_utc()
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                cursor.execute(
                    "UPDATE ops_sources SET status = ?, updated_at = ? WHERE source_id = ?",
                    (status.value, current_time.isoformat(), source_id),
                )
            else:
                cursor.execute(
                    "UPDATE ops.sources SET status = %s, updated_at = %s WHERE source_id = %s",
                    (status.value, current_time, source_id),
                )
            cursor.close()

    def upsert_state(self, state: ConnectorState) -> ConnectorState:
        current_time = now_utc()
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                cursor.execute(
                    (
                        "INSERT OR REPLACE INTO ops_connector_state "
                        "(source_id, last_sync_at, cursor_value, error_count, retry_count, "
                        "last_error, last_run_status, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        state.source_id,
                        state.last_sync_at.isoformat() if state.last_sync_at else None,
                        state.cursor_value,
                        state.error_count,
                        state.retry_count,
                        state.last_error,
                        state.last_run_status,
                        current_time.isoformat(),
                    ),
                )
            else:
                cursor.execute(
                    (
                        "INSERT INTO ops.connector_state "
                        "(source_id, last_sync_at, cursor_value, error_count, retry_count, "
                        "last_error, last_run_status, updated_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (source_id) DO UPDATE SET "
                        "last_sync_at = EXCLUDED.last_sync_at, "
                        "cursor_value = EXCLUDED.cursor_value, "
                        "error_count = EXCLUDED.error_count, "
                        "retry_count = EXCLUDED.retry_count, "
                        "last_error = EXCLUDED.last_error, "
                        "last_run_status = EXCLUDED.last_run_status, "
                        "updated_at = EXCLUDED.updated_at"
                    ),
                    (
                        state.source_id,
                        state.last_sync_at,
                        state.cursor_value,
                        state.error_count,
                        state.retry_count,
                        state.last_error,
                        state.last_run_status,
                        current_time,
                    ),
                )
            cursor.close()
        return state

    def get_state(self, source_id: int) -> ConnectorState | None:
        with self.connect() as connection:
            cursor = connection.cursor()
            query = (
                SQLITE_STATE_SELECT if self.scheme.startswith("sqlite") else POSTGRES_STATE_SELECT
            )
            cursor.execute(query, (source_id,))
            values = _row_to_mapping(cursor.fetchone())
            cursor.close()

        if values is None:
            return None

        return ConnectorState(
            source_id=int(values["source_id"]),
            last_sync_at=_parse_datetime(values["last_sync_at"]),
            cursor_value=values["cursor_value"],
            error_count=int(values["error_count"] or 0),
            retry_count=int(values["retry_count"] or 0),
            last_error=values["last_error"],
            last_run_status=values["last_run_status"],
        )

    def record_error(
        self,
        source_id: int,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        current_time = now_utc()
        payload = json.dumps(details or {})
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                cursor.execute(
                    (
                        "INSERT INTO ops_connector_errors "
                        "(source_id, error_type, message, details_json, created_at) "
                        "VALUES (?, ?, ?, ?, ?)"
                    ),
                    (
                        source_id,
                        error_type,
                        message,
                        payload,
                        current_time.isoformat(),
                    ),
                )
            else:
                cursor.execute(
                    (
                        "INSERT INTO ops.connector_errors "
                        "(source_id, error_type, message, details_json, created_at) "
                        "VALUES (%s, %s, %s, %s, %s)"
                    ),
                    (source_id, error_type, message, payload, current_time),
                )
            cursor.close()

    def list_errors(self, source_id: int) -> list[SourceErrorRecord]:
        with self.connect() as connection:
            cursor = connection.cursor()
            query = (
                SQLITE_ERRORS_SELECT if self.scheme.startswith("sqlite") else POSTGRES_ERRORS_SELECT
            )
            cursor.execute(query, (source_id,))
            rows = [_row_to_mapping(row) for row in cursor.fetchall()]
            cursor.close()

        output: list[SourceErrorRecord] = []
        for item in rows:
            if item is None:
                continue
            output.append(
                SourceErrorRecord(
                    source_id=int(item["source_id"]),
                    error_type=str(item["error_type"]),
                    message=str(item["message"]),
                    details=_normalize_json(item["details_json"]),
                    created_at=_require_datetime(item["created_at"]),
                )
            )
        return output

    def create_import_job(
        self,
        source_id: int,
        source_name: str,
        source_type: SourceType,
    ) -> int:
        current_time = now_utc()
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                cursor.execute(
                    (
                        "INSERT INTO ops_import_jobs "
                        "(source_id, source_type, source_name, status, started_at, "
                        "rows_received, rows_loaded) VALUES (?, ?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        source_id,
                        source_type.value,
                        source_name,
                        "running",
                        current_time.isoformat(),
                        0,
                        0,
                    ),
                )
                job_id = int(cursor.lastrowid)
            else:
                cursor.execute(
                    (
                        "INSERT INTO ops.import_jobs "
                        "(source_id, source_type, source_name, status, started_at, "
                        "rows_received, rows_loaded) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                        "RETURNING import_job_id"
                    ),
                    (
                        source_id,
                        source_type.value,
                        source_name,
                        "running",
                        current_time,
                        0,
                        0,
                    ),
                )
                job_id = int(cursor.fetchone()[0])
            cursor.close()
        return job_id

    def finish_import_job(
        self,
        import_job_id: int,
        status: str,
        rows_received: int,
        rows_loaded: int,
        error_message: str | None = None,
    ) -> None:
        current_time = now_utc()
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                cursor.execute(
                    (
                        "UPDATE ops_import_jobs SET status = ?, finished_at = ?, "
                        "rows_received = ?, rows_loaded = ?, error_message = ? "
                        "WHERE import_job_id = ?"
                    ),
                    (
                        status,
                        current_time.isoformat(),
                        rows_received,
                        rows_loaded,
                        error_message,
                        import_job_id,
                    ),
                )
            else:
                cursor.execute(
                    (
                        "UPDATE ops.import_jobs SET status = %s, finished_at = %s, "
                        "rows_received = %s, rows_loaded = %s, error_message = %s "
                        "WHERE import_job_id = %s"
                    ),
                    (
                        status,
                        current_time,
                        rows_received,
                        rows_loaded,
                        error_message,
                        import_job_id,
                    ),
                )
            cursor.close()

    def create_sync_run(
        self,
        source_name: str,
        cursor_value: str | None,
        sync_mode: str,
    ) -> int:
        current_time = now_utc()
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                cursor.execute(
                    (
                        "INSERT INTO ops_sync_runs "
                        "(connector_name, sync_mode, status, cursor_value, started_at, "
                        "rows_processed) VALUES (?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        source_name,
                        sync_mode,
                        "running",
                        cursor_value,
                        current_time.isoformat(),
                        0,
                    ),
                )
                sync_run_id = int(cursor.lastrowid)
            else:
                cursor.execute(
                    (
                        "INSERT INTO ops.sync_runs "
                        "(connector_name, sync_mode, status, cursor_value, started_at, "
                        "rows_processed) VALUES (%s, %s, %s, %s, %s, %s) "
                        "RETURNING sync_run_id"
                    ),
                    (
                        source_name,
                        sync_mode,
                        "running",
                        cursor_value,
                        current_time,
                        0,
                    ),
                )
                sync_run_id = int(cursor.fetchone()[0])
            cursor.close()
        return sync_run_id

    def finish_sync_run(
        self,
        sync_run_id: int,
        status: str,
        rows_processed: int,
        cursor_value: str | None = None,
        error_message: str | None = None,
    ) -> None:
        current_time = now_utc()
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                cursor.execute(
                    (
                        "UPDATE ops_sync_runs SET status = ?, finished_at = ?, "
                        "rows_processed = ?, cursor_value = ?, error_message = ? "
                        "WHERE sync_run_id = ?"
                    ),
                    (
                        status,
                        current_time.isoformat(),
                        rows_processed,
                        cursor_value,
                        error_message,
                        sync_run_id,
                    ),
                )
            else:
                cursor.execute(
                    (
                        "UPDATE ops.sync_runs SET status = %s, finished_at = %s, "
                        "rows_processed = %s, cursor_value = %s, error_message = %s "
                        "WHERE sync_run_id = %s"
                    ),
                    (
                        status,
                        current_time,
                        rows_processed,
                        cursor_value,
                        error_message,
                        sync_run_id,
                    ),
                )
            cursor.close()

    def insert_raw_rows(
        self,
        source_id: int,
        import_job_id: int,
        rows: list[dict[str, Any]],
    ) -> int:
        with self.connect() as connection:
            cursor = connection.cursor()
            if self.scheme.startswith("sqlite"):
                for row_num, row in enumerate(rows, start=1):
                    cursor.execute(
                        (
                            "INSERT INTO raw_import_rows "
                            "(source_id, import_job_id, row_num, payload_json, "
                            "ingested_at) VALUES (?, ?, ?, ?, ?)"
                        ),
                        (
                            source_id,
                            import_job_id,
                            row_num,
                            json.dumps(row),
                            now_utc().isoformat(),
                        ),
                    )
            else:
                for row_num, row in enumerate(rows, start=1):
                    cursor.execute(
                        (
                            "INSERT INTO raw.import_rows "
                            "(source_id, import_job_id, row_num, payload_json, "
                            "ingested_at) VALUES (%s, %s, %s, %s, %s)"
                        ),
                        (
                            source_id,
                            import_job_id,
                            row_num,
                            json.dumps(row),
                            now_utc(),
                        ),
                    )
            cursor.close()
        return len(rows)

    @staticmethod
    def _sqlite_ddl() -> list[str]:
        return [
            (
                "CREATE TABLE IF NOT EXISTS ops_sources ("
                "source_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT NOT NULL, "
                "type TEXT NOT NULL, "
                "status TEXT NOT NULL, "
                "config_json TEXT NOT NULL, "
                "created_at TEXT NOT NULL, "
                "updated_at TEXT NOT NULL)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS ops_connector_state ("
                "source_id INTEGER PRIMARY KEY, "
                "last_sync_at TEXT, "
                "cursor_value TEXT, "
                "error_count INTEGER NOT NULL DEFAULT 0, "
                "retry_count INTEGER NOT NULL DEFAULT 0, "
                "last_error TEXT, "
                "last_run_status TEXT, "
                "updated_at TEXT NOT NULL)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS ops_connector_errors ("
                "connector_error_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "source_id INTEGER NOT NULL, "
                "error_type TEXT NOT NULL, "
                "message TEXT NOT NULL, "
                "details_json TEXT, "
                "created_at TEXT NOT NULL)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS ops_import_jobs ("
                "import_job_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "source_id INTEGER NOT NULL, "
                "source_type TEXT NOT NULL, "
                "source_name TEXT NOT NULL, "
                "status TEXT NOT NULL, "
                "started_at TEXT, finished_at TEXT, "
                "rows_received INTEGER NOT NULL DEFAULT 0, "
                "rows_loaded INTEGER NOT NULL DEFAULT 0, "
                "error_message TEXT)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS ops_sync_runs ("
                "sync_run_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "connector_name TEXT NOT NULL, "
                "sync_mode TEXT, "
                "status TEXT NOT NULL, "
                "cursor_value TEXT, "
                "started_at TEXT, finished_at TEXT, "
                "rows_processed INTEGER NOT NULL DEFAULT 0, "
                "error_message TEXT)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS raw_import_rows ("
                "raw_row_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "source_id INTEGER NOT NULL, "
                "import_job_id INTEGER NOT NULL, "
                "row_num INTEGER NOT NULL, "
                "payload_json TEXT NOT NULL, "
                "ingested_at TEXT NOT NULL)"
            ),
        ]

    @staticmethod
    def _postgres_ddl() -> list[str]:
        return [
            "CREATE SCHEMA IF NOT EXISTS ops",
            "CREATE SCHEMA IF NOT EXISTS raw",
            (
                "CREATE TABLE IF NOT EXISTS ops.sources ("
                "source_id BIGSERIAL PRIMARY KEY, "
                "name TEXT NOT NULL, "
                "type TEXT NOT NULL, "
                "status TEXT NOT NULL, "
                "config_json JSONB NOT NULL DEFAULT '{}'::jsonb, "
                "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
                "updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
            ),
            (
                "CREATE TABLE IF NOT EXISTS ops.connector_state ("
                "source_id BIGINT PRIMARY KEY REFERENCES ops.sources(source_id) "
                "ON DELETE CASCADE, "
                "last_sync_at TIMESTAMPTZ, "
                "cursor_value TEXT, "
                "error_count INTEGER NOT NULL DEFAULT 0, "
                "retry_count INTEGER NOT NULL DEFAULT 0, "
                "last_error TEXT, "
                "last_run_status TEXT, "
                "updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
            ),
            (
                "CREATE TABLE IF NOT EXISTS ops.connector_errors ("
                "connector_error_id BIGSERIAL PRIMARY KEY, "
                "source_id BIGINT NOT NULL REFERENCES ops.sources(source_id) "
                "ON DELETE CASCADE, "
                "error_type TEXT NOT NULL, "
                "message TEXT NOT NULL, "
                "details_json JSONB NOT NULL DEFAULT '{}'::jsonb, "
                "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
            ),
            (
                "CREATE TABLE IF NOT EXISTS ops.import_jobs ("
                "import_job_id BIGSERIAL PRIMARY KEY, "
                "source_id BIGINT, "
                "source_type TEXT NOT NULL, "
                "source_name TEXT NOT NULL, "
                "status TEXT NOT NULL, "
                "started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ, "
                "rows_received BIGINT DEFAULT 0, "
                "rows_loaded BIGINT DEFAULT 0, "
                "error_message TEXT)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS ops.sync_runs ("
                "sync_run_id BIGSERIAL PRIMARY KEY, "
                "connector_name TEXT NOT NULL, "
                "sync_mode TEXT, "
                "status TEXT NOT NULL, "
                "cursor_value TEXT, "
                "started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ, "
                "rows_processed BIGINT DEFAULT 0, "
                "error_message TEXT)"
            ),
            (
                "CREATE TABLE IF NOT EXISTS raw.import_rows ("
                "raw_row_id BIGSERIAL PRIMARY KEY, "
                "source_id BIGINT NOT NULL REFERENCES ops.sources(source_id) "
                "ON DELETE CASCADE, "
                "import_job_id BIGINT NOT NULL REFERENCES "
                "ops.import_jobs(import_job_id) ON DELETE CASCADE, "
                "row_num INTEGER NOT NULL, "
                "payload_json JSONB NOT NULL, "
                "ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
            ),
        ]
