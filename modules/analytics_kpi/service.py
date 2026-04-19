# Project:      RetailOps Data & AI Platform
# Module:       modules.analytics_kpi
# File:         service.py
# Path:         modules/analytics_kpi/service.py
#
# Summary:      Implements the analytics kpi service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for analytics kpi workflows.
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
#   - Main types: DashboardCardArtifact, DashboardArtifact, SalesDailyItem, CategoryRevenueItem, InventoryHealthItem, ShipmentSummary, ...
#   - Key APIs: build_sales_daily, build_revenue_by_category, build_inventory_health, build_shipment_summary, build_overview, build_dashboard_cards, ...
#   - Dependencies: __future__, json, uuid, dataclasses, datetime, pathlib, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, TypedDict

from . import queries


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


class SalesDailyItem(TypedDict):
    sales_date: str
    revenue: float
    order_count: int


class CategoryRevenueItem(TypedDict):
    category: str
    revenue: float
    order_count: int


class InventoryHealthItem(TypedDict):
    sku: str
    on_hand: float
    days_of_cover: float
    low_stock: bool


class ShipmentSummary(TypedDict):
    total_shipments: int
    delayed_shipments: int
    on_time_shipments: int
    on_time_rate: float
    avg_delay_days: float


class OverviewMetrics(TypedDict):
    total_orders: int
    total_quantity: float
    total_revenue: float
    avg_order_value: float
    sales_days: int
    delayed_shipments: int
    low_stock_items: int


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


def _to_int(value: object, *, default: int = 0) -> int:
    return int(_to_float(value, default=float(default)))


def _to_bool(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "delayed", "late"}:
            return True
        if text in {"0", "false", "no", "n", "on-time", "on_time"}:
            return False
    return default


def _parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _as_daily_sales_count(value: object) -> int:
    if not isinstance(value, list):
        return 0
    return sum(1 for item in value if isinstance(item, dict))


def build_sales_daily(transform_summary: dict[str, object]) -> list[SalesDailyItem]:
    rows = queries.get_first_sequence(transform_summary, queries.DAILY_SALES_KEYS)
    items: list[SalesDailyItem] = []
    for row in rows:
        sales_date = str(row.get("sales_date") or row.get("date") or row.get("day") or "unknown")
        items.append(
            {
                "sales_date": sales_date,
                "revenue": _to_float(
                    row.get("revenue") or row.get("total_revenue") or row.get("sales_revenue")
                ),
                "order_count": _to_int(
                    row.get("order_count") or row.get("orders") or row.get("total_orders")
                ),
            }
        )
    items.sort(key=lambda item: item["sales_date"])
    return items


def build_revenue_by_category(transform_summary: dict[str, object]) -> list[CategoryRevenueItem]:
    rows = queries.get_first_sequence(
        transform_summary,
        queries.CATEGORY_REVENUE_KEYS,
    )
    items: list[CategoryRevenueItem] = []
    for row in rows:
        items.append(
            {
                "category": str(
                    row.get("category") or row.get("category_name") or row.get("name") or "unknown"
                ),
                "revenue": _to_float(row.get("revenue") or row.get("total_revenue")),
                "order_count": _to_int(row.get("order_count") or row.get("orders")),
            }
        )
    items.sort(key=lambda item: (-item["revenue"], item["category"]))
    return items


def build_inventory_health(transform_summary: dict[str, object]) -> list[InventoryHealthItem]:
    rows = queries.get_first_sequence(
        transform_summary,
        queries.INVENTORY_HEALTH_KEYS,
    )
    items: list[InventoryHealthItem] = []
    for row in rows:
        days_of_cover = _to_float(
            row.get("days_of_cover") or row.get("stock_coverage_days") or row.get("coverage_days")
        )
        low_stock = _to_bool(
            row.get("low_stock"), default=days_of_cover < queries.LOW_STOCK_DAYS_THRESHOLD
        )
        items.append(
            {
                "sku": str(row.get("sku") or row.get("product_id") or row.get("item") or "unknown"),
                "on_hand": _to_float(
                    row.get("on_hand") or row.get("inventory_on_hand") or row.get("quantity")
                ),
                "days_of_cover": days_of_cover,
                "low_stock": low_stock,
            }
        )
    items.sort(key=lambda item: (item["days_of_cover"], item["sku"]))
    return items


def build_shipment_summary(transform_summary: dict[str, object]) -> ShipmentSummary:
    rows = queries.get_first_sequence(transform_summary, queries.SHIPMENT_KEYS)
    total_shipments = 0
    delayed_shipments = 0
    total_delay_days = 0.0

    for row in rows:
        total_shipments += 1
        delay_days = _to_float(row.get("delay_days"))
        delayed = _to_bool(row.get("delayed"), default=False)
        if not delayed:
            promised_date = _parse_iso_date(row.get("promised_date") or row.get("sla_date"))
            delivered_date = _parse_iso_date(
                row.get("delivered_date") or row.get("actual_delivery_date")
            )
            if promised_date and delivered_date and delivered_date > promised_date:
                delayed = True
                delay_days = max((delivered_date - promised_date).days, delay_days)

        if delayed:
            delayed_shipments += 1
            total_delay_days += delay_days

    on_time_shipments = max(total_shipments - delayed_shipments, 0)
    on_time_rate = round(on_time_shipments / total_shipments, 4) if total_shipments else 0.0
    avg_delay_days = round(total_delay_days / delayed_shipments, 2) if delayed_shipments else 0.0
    return {
        "total_shipments": total_shipments,
        "delayed_shipments": delayed_shipments,
        "on_time_shipments": on_time_shipments,
        "on_time_rate": on_time_rate,
        "avg_delay_days": avg_delay_days,
    }


def build_overview(transform_summary: dict[str, object]) -> OverviewMetrics:
    daily_sales = build_sales_daily(transform_summary)
    inventory_health = build_inventory_health(transform_summary)
    shipment_summary = build_shipment_summary(transform_summary)

    total_orders = _to_int(
        queries.get_first_scalar(
            transform_summary,
            queries.TOTAL_ORDER_KEYS,
            default=sum(item["order_count"] for item in daily_sales),
        )
    )
    total_quantity = _to_float(
        queries.get_first_scalar(
            transform_summary,
            queries.TOTAL_QUANTITY_KEYS,
            default=0.0,
        )
    )
    total_revenue = _to_float(
        queries.get_first_scalar(
            transform_summary,
            queries.TOTAL_REVENUE_KEYS,
            default=sum(item["revenue"] for item in daily_sales),
        )
    )
    avg_order_value = _to_float(
        queries.get_first_scalar(
            transform_summary,
            queries.AVG_ORDER_VALUE_KEYS,
            default=(total_revenue / total_orders if total_orders else 0.0),
        )
    )
    low_stock_items = sum(1 for item in inventory_health if item["low_stock"])

    return {
        "total_orders": total_orders,
        "total_quantity": total_quantity,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "sales_days": _as_daily_sales_count(transform_summary.get("daily_sales")),
        "delayed_shipments": shipment_summary["delayed_shipments"],
        "low_stock_items": low_stock_items,
    }


def build_dashboard_cards(transform_summary: dict[str, object]) -> list[DashboardCardArtifact]:
    overview = build_overview(transform_summary)
    return [
        DashboardCardArtifact(
            title="Total orders",
            value=str(overview["total_orders"]),
            description="Unique orders in the starter transform output.",
        ),
        DashboardCardArtifact(
            title="Total quantity",
            value=f"{overview['total_quantity']:.2f}",
            description="Units sold across the loaded dataset.",
        ),
        DashboardCardArtifact(
            title="Total revenue",
            value=f"{overview['total_revenue']:.2f}",
            description="Quantity multiplied by unit price.",
        ),
        DashboardCardArtifact(
            title="Sales days",
            value=str(overview["sales_days"]),
            description="Distinct daily buckets available for simple trend views.",
        ),
    ]


def publish_first_dashboard(
    *,
    upload_id: str,
    filename: str,
    transform_summary: dict[str, object],
    artifact_dir: Path,
) -> DashboardArtifact:
    artifact_dir.mkdir(parents=True, exist_ok=True)

    dashboard_id = f"dash_{uuid.uuid4().hex[:12]}"
    cards = build_dashboard_cards(transform_summary)

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


def load_dashboard_artifact(
    *,
    upload_id: str,
    dashboard_id: str,
    artifact_dir: Path,
) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_{dashboard_id}.json"
    if not artifact_path.exists():
        raise FileNotFoundError(f"Dashboard artifact not found: {artifact_path}")
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def load_transform_summary_from_upload(
    *,
    upload_id: str,
    uploads_dir: Path = Path("data/uploads"),
) -> dict[str, Any]:
    metadata_path = uploads_dir / f"{upload_id}.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Upload metadata not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    transform_summary = metadata.get("transform_summary")
    if not isinstance(transform_summary, dict):
        raise ValueError(f"Transform summary not found in upload metadata: {metadata_path}")
    return transform_summary
