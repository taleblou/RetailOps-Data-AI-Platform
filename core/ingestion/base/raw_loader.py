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
