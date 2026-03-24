from datetime import UTC, datetime
from pathlib import Path

from core.ingestion.base.models import SourceRecord, SourceStatus, SourceType
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.repository import MemoryRepository
from core.ingestion.base.state_store import StateStore
from modules.connector_csv.connector import CsvConnector


def build_source(csv_path: Path) -> SourceRecord:
    return SourceRecord(
        source_id=1,
        name="orders-csv",
        type=SourceType.CSV,
        status=SourceStatus.CREATED,
        config={"file_path": str(csv_path)},
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )


def test_csv_connector_discovers_schema_and_extracts_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text(
        "order_id,qty,price_each\n1001,2,9.99\n1002,3,14.50\n",
        encoding="utf-8",
    )
    repository = MemoryRepository()
    connector = CsvConnector(
        source=build_source(csv_path),
        state_store=StateStore(repository),
        raw_loader=RawLoader(repository),
    )
    schema = connector.discover_schema()
    rows = connector.extract()
    assert [column.name for column in schema.columns] == [
        "order_id",
        "qty",
        "price_each",
    ]
    assert len(rows) == 2
    assert rows[0]["order_id"] == "1001"
