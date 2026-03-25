from __future__ import annotations

import csv
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TransformDailyMetricArtifact:
    sales_date: str
    order_count: int
    unit_count: float
    revenue: float


@dataclass(slots=True)
class TransformArtifact:
    transform_run_id: str
    upload_id: str
    row_count: int
    total_orders: int
    total_quantity: float
    total_revenue: float
    unique_customers: int
    unique_skus: int
    daily_sales: list[TransformDailyMetricArtifact]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _to_float(value: object, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            return float(text)
        except ValueError:
            return default
    return default


def _to_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": _to_text(row.get("order_id")),
        "order_date": _to_text(row.get("order_date")),
        "customer_id": _to_text(row.get("customer_id")),
        "sku": _to_text(row.get("sku")),
        "quantity": _to_float(row.get("quantity")),
        "unit_price": _to_float(row.get("unit_price")),
        "store_code": _to_text(row.get("store_code")),
    }


def _read_csv_rows_from_metadata(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    stored_path_value = metadata.get("stored_path")
    mapping = metadata.get("mapping") or {}
    if not stored_path_value or not mapping:
        return []

    stored_path = Path(str(stored_path_value))
    delimiter = str(metadata.get("delimiter", ","))
    encoding = str(metadata.get("encoding", "utf-8"))

    rows: list[dict[str, Any]] = []
    with stored_path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for source_row in reader:
            canonical_row: dict[str, Any] = {}
            for canonical_name, source_name in mapping.items():
                canonical_row[canonical_name] = source_row.get(str(source_name))
            rows.append(_normalize_canonical_row(canonical_row))
    return rows


def _extract_rows(kwargs: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_names = [
        "mapped_rows",
        "rows",
        "canonical_rows",
        "validated_rows",
        "import_rows",
    ]
    for name in candidate_names:
        value = kwargs.get(name)
        if isinstance(value, list):
            normalized_rows: list[dict[str, Any]] = []
            for item in value:
                if isinstance(item, dict):
                    normalized_rows.append(_normalize_canonical_row(item))
            if normalized_rows:
                return normalized_rows

    metadata_names = [
        "metadata",
        "upload_metadata",
        "import_summary",
        "transform_input",
    ]
    for name in metadata_names:
        value = kwargs.get(name)
        if isinstance(value, dict):
            rows = _read_csv_rows_from_metadata(value)
            if rows:
                return rows
    return []


def _parse_sales_date(value: str) -> str:
    text = value.strip()
    if not text:
        return "unknown"
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        return text


def _resolve_upload_id(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    value = kwargs.get("upload_id")
    if value is None and args:
        value = args[0]
    text = _to_text(value)
    if not text:
        raise ValueError("upload_id is required for the first transform run.")
    return text


def _resolve_artifact_dir(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Path:
    value = kwargs.get("artifact_dir")
    if value is None:
        for candidate in args:
            if isinstance(candidate, Path):
                value = candidate
                break
            if isinstance(candidate, str) and ("/" in candidate or candidate.endswith(".json")):
                value = candidate
                break
    if value is None:
        raise ValueError("artifact_dir is required for the first transform run.")
    return Path(str(value))


def run_first_transform(*args: Any, **kwargs: Any) -> TransformArtifact:
    upload_id = _resolve_upload_id(args, kwargs)
    artifact_dir = _resolve_artifact_dir(args, kwargs)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    rows = _extract_rows(kwargs)
    if not rows:
        raise ValueError(
            "No canonical rows were available for the first transform run. "
            "Pass mapped_rows or metadata with stored_path, delimiter, encoding, and mapping."
        )

    transform_run_id = f"tr_{uuid.uuid4().hex[:12]}"
    order_ids: set[str] = set()
    customer_ids: set[str] = set()
    skus: set[str] = set()
    daily_buckets: dict[str, dict[str, Any]] = {}
    total_quantity = 0.0
    total_revenue = 0.0

    for row in rows:
        order_id = _to_text(row.get("order_id"))
        customer_id = _to_text(row.get("customer_id"))
        sku = _to_text(row.get("sku"))
        sales_date = _parse_sales_date(_to_text(row.get("order_date")))
        quantity = _to_float(row.get("quantity"))
        unit_price = _to_float(row.get("unit_price"))
        revenue = round(quantity * unit_price, 2)

        if order_id:
            order_ids.add(order_id)
        if customer_id:
            customer_ids.add(customer_id)
        if sku:
            skus.add(sku)

        total_quantity += quantity
        total_revenue += revenue

        bucket = daily_buckets.setdefault(
            sales_date,
            {
                "sales_date": sales_date,
                "order_ids": set(),
                "unit_count": 0.0,
                "revenue": 0.0,
            },
        )
        if order_id:
            bucket["order_ids"].add(order_id)
        bucket["unit_count"] += quantity
        bucket["revenue"] += revenue

    daily_sales = [
        TransformDailyMetricArtifact(
            sales_date=sales_date,
            order_count=len(bucket["order_ids"]),
            unit_count=round(float(bucket["unit_count"]), 2),
            revenue=round(float(bucket["revenue"]), 2),
        )
        for sales_date, bucket in sorted(daily_buckets.items(), key=lambda item: item[0])
    ]

    artifact_path = artifact_dir / f"{upload_id}_{transform_run_id}.json"
    artifact = TransformArtifact(
        transform_run_id=transform_run_id,
        upload_id=upload_id,
        row_count=len(rows),
        total_orders=len(order_ids),
        total_quantity=round(total_quantity, 2),
        total_revenue=round(total_revenue, 2),
        unique_customers=len(customer_ids),
        unique_skus=len(skus),
        daily_sales=daily_sales,
        artifact_path=str(artifact_path),
    )
    artifact_path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return artifact
