from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from urllib.parse import urlparse

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import ColumnInfo, SchemaDiscoveryResult, TestConnectionResult
from modules.connector_db.schemas import DatabaseConnectorConfig

psycopg_module: Any | None
try:
    import psycopg as _psycopg
except ImportError:  # pragma: no cover
    psycopg_module = None
else:
    psycopg_module = _psycopg


class DatabaseConnector(BaseConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config = DatabaseConnectorConfig.model_validate(self.source.config)
        self.scheme = urlparse(self.config.database_url).scheme

    @contextmanager
    def connect(self) -> Iterator[Any]:
        if self.scheme.startswith("sqlite"):
            parsed = urlparse(self.config.database_url)
            path = parsed.path or ":memory:"
            sqlite_connection = sqlite3.connect(path)
            sqlite_connection.row_factory = sqlite3.Row
            try:
                yield sqlite_connection
            finally:
                sqlite_connection.close()
            return

        if self.scheme.startswith("postgres"):
            if psycopg_module is None:
                raise RuntimeError(
                    "psycopg is not installed. Run `uv sync` before using PostgreSQL."
                )
            postgres_connection = psycopg_module.connect(self.config.database_url)
            try:
                yield postgres_connection
            finally:
                postgres_connection.close()
            return

        raise ValueError(f"Unsupported database scheme: {self.scheme}")

    def test_connection(self) -> TestConnectionResult:
        try:
            with self.connect() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            return TestConnectionResult(
                ok=True,
                message="Database source is reachable.",
            )
        except Exception as exc:
            return TestConnectionResult(ok=False, message=str(exc))

    def discover_schema(self) -> SchemaDiscoveryResult:
        query = (
            f"SELECT * FROM ({self.config.query}) AS source_query LIMIT {self.config.sample_limit}"
        )
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            description = cursor.description
            cursor.close()

        columns = [
            ColumnInfo(
                name=self._column_name(item),
                dtype="string",
                position=index,
            )
            for index, item in enumerate(description, start=1)
        ]
        sample_rows = [self._row_to_dict(row, description) for row in rows]
        return SchemaDiscoveryResult(columns=columns, sample_rows=sample_rows)

    def extract(
        self,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        _ = cursor
        query = self.config.query
        if limit is not None:
            query = f"SELECT * FROM ({query}) AS source_query LIMIT {limit}"
        with self.connect() as connection:
            db_cursor = connection.cursor()
            db_cursor.execute(query)
            rows = db_cursor.fetchall()
            description = db_cursor.description
            db_cursor.close()
        return [self._row_to_dict(row, description) for row in rows]

    @staticmethod
    def _column_name(item: Any) -> str:
        return str(item[0] if isinstance(item, tuple) else getattr(item, "name", item))

    def _row_to_dict(self, row: Any, description: Any) -> dict[str, Any]:
        if hasattr(row, "keys"):
            return {key: row[key] for key in row.keys()}
        column_names = [self._column_name(item) for item in description]
        return dict(zip(column_names, row, strict=False))
