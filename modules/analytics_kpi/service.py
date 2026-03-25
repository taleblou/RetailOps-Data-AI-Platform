from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DashboardCardArtifact:
    title: str
    value: str
    description: str


@dataclass(slots=True)
class DashboardArtifact:
    dashboard_id: str
    dashboard_title: str
    dashboard_url: str
    artifact_path: str
    cards: list[DashboardCardArtifact]

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


def _as_daily_sales_count(value: object) -> int:
    if not isinstance(value, list):
        return 0
    return sum(1 for item in value if isinstance(item, dict))


def publish_first_dashboard(
    *,
    upload_id: str,
    filename: str,
    transform_summary: dict[str, object],
    artifact_dir: Path,
) -> DashboardArtifact:
    artifact_dir.mkdir(parents=True, exist_ok=True)

    dashboard_id = f"dash_{uuid.uuid4().hex[:12]}"
    total_orders = int(_to_float(transform_summary.get("total_orders")))
    total_quantity = _to_float(transform_summary.get("total_quantity"))
    total_revenue = _to_float(transform_summary.get("total_revenue"))
    sales_days = _as_daily_sales_count(transform_summary.get("daily_sales"))

    cards = [
        DashboardCardArtifact(
            title="Total orders",
            value=str(total_orders),
            description="Unique orders in the starter transform output.",
        ),
        DashboardCardArtifact(
            title="Total quantity",
            value=f"{total_quantity:.2f}",
            description="Units sold across the loaded dataset.",
        ),
        DashboardCardArtifact(
            title="Total revenue",
            value=f"{total_revenue:.2f}",
            description="Quantity multiplied by unit price.",
        ),
        DashboardCardArtifact(
            title="Sales days",
            value=str(sales_days),
            description="Distinct daily buckets available for simple trend views.",
        ),
    ]

    artifact_path = artifact_dir / f"{upload_id}_{dashboard_id}.json"
    artifact = DashboardArtifact(
        dashboard_id=dashboard_id,
        dashboard_title=f"Starter KPI dashboard · {filename}",
        dashboard_url=f"/easy-csv/{upload_id}/dashboard/view",
        artifact_path=str(artifact_path),
        cards=cards,
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
