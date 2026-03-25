from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TransformDailyMetric:
    sales_date: str
    order_count: int
    total_quantity: float
    total_revenue: float


@dataclass(slots=True)
class FirstTransformArtifact:
    transform_run_id: str
    input_row_count: int
    output_row_count: int
    total_orders: int
    total_quantity: float
    total_revenue: float
    daily_sales: list[TransformDailyMetric]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class _DailyAccumulator:
    order_ids: set[str] = field(default_factory=set)
    total_quantity: float = 0.0
    total_revenue: float = 0.0


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


def _normalize_date(value: object) -> str:
    raw = _to_text(value)
    if not raw:
        return "unknown"
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt).date().isoformat()
        except ValueError:
            continue
    return raw[:10] if len(raw) >= 10 else raw


def run_first_transform(
    mapped_rows: list[dict[str, Any]],
    *,
    artifact_dir: Path,
    upload_id: str,
) -> FirstTransformArtifact:
    artifact_dir.mkdir(parents=True, exist_ok=True)

    transform_run_id = f"tr_{uuid.uuid4().hex[:12]}"
    total_quantity = 0.0
    total_revenue = 0.0
    all_order_ids: set[str] = set()
    per_day: dict[str, _DailyAccumulator] = {}

    for row in mapped_rows:
        order_id = _to_text(row.get("order_id"))
        sales_date = _normalize_date(row.get("order_date"))
        quantity = _to_float(row.get("quantity"))
        unit_price = _to_float(row.get("unit_price"))
        revenue = quantity * unit_price

        total_quantity += quantity
        total_revenue += revenue

        if order_id:
            all_order_ids.add(order_id)

        bucket = per_day.setdefault(sales_date, _DailyAccumulator())
        if order_id:
            bucket.order_ids.add(order_id)
        bucket.total_quantity += quantity
        bucket.total_revenue += revenue

    daily_sales: list[TransformDailyMetric] = []
    for sales_date in sorted(per_day):
        bucket = per_day[sales_date]
        daily_sales.append(
            TransformDailyMetric(
                sales_date=sales_date,
                order_count=len(bucket.order_ids) or 0,
                total_quantity=round(bucket.total_quantity, 2),
                total_revenue=round(bucket.total_revenue, 2),
            )
        )

    total_orders = len(all_order_ids) if all_order_ids else len(mapped_rows)
    artifact_path = artifact_dir / f"{upload_id}_{transform_run_id}.json"
    artifact = FirstTransformArtifact(
        transform_run_id=transform_run_id,
        input_row_count=len(mapped_rows),
        output_row_count=len(mapped_rows),
        total_orders=total_orders,
        total_quantity=round(total_quantity, 2),
        total_revenue=round(total_revenue, 2),
        daily_sales=daily_sales,
        artifact_path=str(artifact_path),
    )
    artifact_path.write_text(
        json.dumps(
            artifact.to_dict(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact
