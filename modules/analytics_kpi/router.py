from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from .export import csv_response, json_download_response
from .schemas import (
    DailySalesPoint,
    DashboardArtifactResponse,
    DashboardPublishRequest,
    InventoryHealthItem,
    KpiOverviewResponse,
    RevenueByCategoryPoint,
    ShipmentSummaryResponse,
    TransformSummaryPayload,
)
from .service import (
    build_inventory_health,
    build_overview,
    build_revenue_by_category,
    build_sales_daily,
    build_shipment_summary,
    load_dashboard_artifact,
    publish_first_dashboard,
)

router = APIRouter(prefix="/api/v1/kpis", tags=["analytics-kpi"])


@router.post("/overview", response_model=KpiOverviewResponse)
async def get_overview(payload: TransformSummaryPayload) -> KpiOverviewResponse:
    return KpiOverviewResponse.model_validate(build_overview(payload.model_dump()))


@router.post("/sales-daily", response_model=list[DailySalesPoint])
async def get_sales_daily(
    payload: TransformSummaryPayload,
    format: Literal["json", "csv"] = Query(default="json"),
):
    rows = build_sales_daily(payload.model_dump())
    if format == "csv":
        return csv_response(
            filename="sales_daily.csv",
            rows=rows,
            headers=["sales_date", "revenue", "order_count"],
        )
    return [DailySalesPoint.model_validate(row) for row in rows]


@router.post("/revenue-by-category", response_model=list[RevenueByCategoryPoint])
async def get_revenue_by_category(
    payload: TransformSummaryPayload,
    format: Literal["json", "csv"] = Query(default="json"),
):
    rows = build_revenue_by_category(payload.model_dump())
    if format == "csv":
        return csv_response(
            filename="revenue_by_category.csv",
            rows=rows,
            headers=["category", "revenue", "order_count"],
        )
    return [RevenueByCategoryPoint.model_validate(row) for row in rows]


@router.post("/inventory-health", response_model=list[InventoryHealthItem])
async def get_inventory_health(
    payload: TransformSummaryPayload,
    format: Literal["json", "csv"] = Query(default="json"),
):
    rows = build_inventory_health(payload.model_dump())
    if format == "csv":
        return csv_response(
            filename="inventory_health.csv",
            rows=rows,
            headers=["sku", "on_hand", "days_of_cover", "low_stock"],
        )
    return [InventoryHealthItem.model_validate(row) for row in rows]


@router.post("/shipments", response_model=ShipmentSummaryResponse)
async def get_shipments(payload: TransformSummaryPayload) -> ShipmentSummaryResponse:
    return ShipmentSummaryResponse.model_validate(build_shipment_summary(payload.model_dump()))


@router.post("/dashboard/publish", response_model=DashboardArtifactResponse)
async def publish_dashboard(
    payload: DashboardPublishRequest,
) -> DashboardArtifactResponse:
    artifact = publish_first_dashboard(
        upload_id=payload.upload_id,
        filename=payload.filename,
        transform_summary=payload.transform_summary.model_dump(),
        artifact_dir=Path(payload.artifact_dir),
    )
    return DashboardArtifactResponse.model_validate(artifact.to_dict())


@router.get(
    "/dashboard/artifact/{upload_id}/{dashboard_id}",
    response_model=DashboardArtifactResponse,
)
async def get_dashboard_artifact(
    upload_id: str,
    dashboard_id: str,
    artifact_dir: str = Query(default="artifacts/analytics_kpi"),
) -> DashboardArtifactResponse:
    try:
        artifact = load_dashboard_artifact(
            upload_id=upload_id,
            dashboard_id=dashboard_id,
            artifact_dir=Path(artifact_dir),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DashboardArtifactResponse.model_validate(artifact)


@router.post("/dashboard/export/cards")
async def export_dashboard_cards(
    payload: TransformSummaryPayload,
    format: Literal["json", "csv"] = Query(default="csv"),
):
    overview = KpiOverviewResponse.model_validate(build_overview(payload.model_dump()))
    rows = [
        {"metric": "total_orders", "value": overview.total_orders},
        {"metric": "total_quantity", "value": overview.total_quantity},
        {"metric": "total_revenue", "value": overview.total_revenue},
        {"metric": "avg_order_value", "value": overview.avg_order_value},
        {"metric": "sales_days", "value": overview.sales_days},
        {"metric": "delayed_shipments", "value": overview.delayed_shipments},
        {"metric": "low_stock_items", "value": overview.low_stock_items},
    ]
    if format == "json":
        return json_download_response(filename="dashboard_cards.json", payload=rows)
    return csv_response(
        filename="dashboard_cards.csv",
        rows=rows,
        headers=["metric", "value"],
    )
