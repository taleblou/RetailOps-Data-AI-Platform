#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

UPLOAD_ID="demo-packaging"

while [ $# -gt 0 ]; do
  case "$1" in
    --upload-id)
      UPLOAD_ID="$2"
      shift 2
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

ensure_runtime_dirs
bootstrap_env_file "standard"

log "Generating demo artifacts for upload_id '$UPLOAD_ID'"
run_repo_python - "$ROOT_DIR" "$UPLOAD_ID" <<'PYCODE'
from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1])
upload_id = sys.argv[2]

sys.path.insert(0, str(root))

from core.transformations.service import run_first_transform
from modules.analytics_kpi.service import publish_first_dashboard
from modules.dashboard_hub.service import publish_dashboard_workspace
from modules.forecasting.service import run_first_forecast
from modules.ml_registry.service import run_model_registry


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_inventory_by_sku(path: Path) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in read_csv_rows(path):
        sku = str(row.get("SKU") or "").strip()
        if not sku:
            continue
        previous = output.get(sku)
        snapshot_date = str(row.get("Snapshot Date") or "")
        if previous is None or snapshot_date >= str(previous.get("Snapshot Date") or ""):
            output[sku] = row
    return output


def build_controlled_orders() -> list[dict[str, str]]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    plan: list[tuple[str, str, str, str, str, int, float, str, str, str, int, int, int, int, float]] = [
        ("ORD001", "C001", "P001", "SKU001", "Beverages", 8, 10.50, "ST-01", "Drinks", "Beverage Core", 2, 0, 7, 12, 0.95),
        ("ORD001", "C001", "P002", "SKU002", "Snacks", 2, 12.00, "ST-01", "Snacks", "Snack Core", 24, 4, 6, 10, 0.97),
        ("ORD002", "C001", "P001", "SKU001", "Beverages", 9, 10.50, "ST-01", "Drinks", "Beverage Core", 2, 0, 7, 12, 0.95),
        ("ORD002", "C001", "P002", "SKU002", "Snacks", 3, 12.00, "ST-01", "Snacks", "Snack Core", 23, 4, 6, 10, 0.97),
        ("ORD003", "C002", "P001", "SKU001", "Beverages", 10, 10.50, "ST-01", "Drinks", "Beverage Core", 1, 0, 7, 12, 0.95),
        ("ORD003", "C002", "P003", "SKU003", "Produce", 1, 8.90, "ST-02", "Fresh", "Produce Picks", 32, 3, 4, 8, 0.94),
        ("ORD004", "C002", "P002", "SKU002", "Snacks", 7, 12.00, "ST-01", "Snacks", "Snack Core", 21, 4, 6, 10, 0.97),
        ("ORD004", "C002", "P001", "SKU001", "Beverages", 6, 10.50, "ST-01", "Drinks", "Beverage Core", 1, 0, 7, 12, 0.95),
        ("ORD005", "C003", "P001", "SKU001", "Beverages", 11, 10.50, "ST-01", "Drinks", "Beverage Core", 1, 0, 7, 12, 0.95),
        ("ORD005", "C003", "P002", "SKU002", "Snacks", 4, 12.00, "ST-02", "Snacks", "Snack Core", 20, 4, 6, 10, 0.97),
        ("ORD006", "C003", "P004", "SKU004", "Household", 3, 18.40, "ST-02", "Home", "Household Basics", 28, 2, 9, 16, 0.93),
        ("ORD006", "C003", "P001", "SKU001", "Beverages", 8, 10.50, "ST-02", "Drinks", "Beverage Core", 2, 0, 7, 12, 0.95),
        ("ORD007", "C004", "P002", "SKU002", "Snacks", 8, 12.00, "ST-02", "Snacks", "Snack Core", 18, 3, 6, 10, 0.97),
        ("ORD007", "C004", "P003", "SKU003", "Produce", 2, 8.90, "ST-02", "Fresh", "Produce Picks", 31, 3, 4, 8, 0.94),
        ("ORD008", "C004", "P001", "SKU001", "Beverages", 8, 10.50, "ST-03", "Drinks", "Beverage Core", 2, 0, 7, 12, 0.95),
        ("ORD008", "C004", "P002", "SKU002", "Snacks", 5, 12.00, "ST-03", "Snacks", "Snack Core", 16, 3, 6, 10, 0.97),
        ("ORD009", "C005", "P003", "SKU003", "Produce", 4, 8.90, "ST-03", "Fresh", "Produce Picks", 29, 3, 4, 8, 0.94),
        ("ORD010", "C005", "P001", "SKU001", "Beverages", 10, 10.50, "ST-03", "Drinks", "Beverage Core", 1, 0, 7, 12, 0.95),
        ("ORD011", "C006", "P002", "SKU002", "Snacks", 6, 12.00, "ST-01", "Snacks", "Snack Core", 14, 3, 6, 10, 0.97),
        ("ORD012", "C006", "P001", "SKU001", "Beverages", 12, 10.50, "ST-01", "Drinks", "Beverage Core", 1, 0, 7, 12, 0.95),
    ]
    rows: list[dict[str, str]] = []
    for index, item in enumerate(plan):
        (
            order_id,
            customer_id,
            product_id,
            sku,
            _category_key,
            quantity,
            unit_price,
            store_code,
            category_label,
            product_group,
            available_qty,
            in_transit_qty,
            lead_time_days,
            supplier_moq,
            service_level_target,
        ) = item
        payment_amount = float(quantity) * float(unit_price)
        refund_amount = 0.0 if order_id != "ORD005" else round(payment_amount * 0.15, 2)
        discount_rate = 0.05 if sku == "SKU001" else 0.02
        rows.append(
            {
                "Order ID": order_id,
                "Order Date": (start + timedelta(days=index // 2)).date().isoformat(),
                "Customer ID": customer_id,
                "Product ID": product_id,
                "SKU": sku,
                "Quantity": str(quantity),
                "Unit Price": f"{unit_price:.2f}",
                "Store Code": store_code,
                "Category": category_label,
                "Product Group": product_group,
                "Available Qty": str(available_qty),
                "In Transit Qty": str(in_transit_qty),
                "Lead Time Days": str(lead_time_days),
                "Supplier MOQ": str(supplier_moq),
                "Service Level Target": f"{service_level_target:.2f}",
                "Supplier ID": "demo",
                "Supplier Name": "Demo Supplier",
                "Received Qty": str(max(quantity - (1 if order_id in {"ORD002", "ORD006"} else 0), 0)),
                "Promised Date": ((start + timedelta(days=index // 2)).date() + timedelta(days=lead_time_days)).isoformat(),
                "Actual Delivery Date": "" if order_id in {"ORD001", "ORD004", "ORD007", "ORD012"} else ((start + timedelta(days=index // 2)).date() + timedelta(days=lead_time_days + (2 if order_id in {"ORD002", "ORD006"} else 0))).isoformat(),
                "Payment Provider": "stripe" if store_code != "ST-03" else "paypal",
                "Payment Amount": f"{payment_amount:.2f}",
                "Refund Amount": f"{refund_amount:.2f}",
                "Order Status": "returned" if order_id == "ORD005" else "completed",
                "Discount Rate": f"{discount_rate:.2f}",
                "Returned Qty": "1" if order_id == "ORD005" else "0",
            }
        )
    return rows


def build_enriched_orders(
    *,
    source_orders: list[dict[str, str]],
    products: dict[str, dict[str, str]],
    inventory_by_sku: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    output = build_controlled_orders()
    for index, row in enumerate(source_orders, start=1):
        sku = str(row.get("SKU") or "").strip()
        product_row = products.get(sku, {})
        inventory_row = inventory_by_sku.get(sku, {})
        quantity = int(float(row.get("Quantity") or 0))
        available_qty = str(inventory_row.get("Available Qty") or max(14, 48 - (index % 22)))
        category = str(product_row.get("Category") or "General Merchandise").strip()
        group_name = f"{category} Portfolio"
        unit_price = str(row.get("Unit Price") or product_row.get("Unit Price") or "0")
        payment_amount = float(unit_price or 0) * float(quantity)
        returned_qty = "1" if index % 37 == 0 else "0"
        output.append(
            {
                "Order ID": str(row.get("Order ID") or f"ORD-X{index:04d}"),
                "Order Date": str(row.get("Order Date") or "2026-01-01"),
                "Customer ID": str(row.get("Customer ID") or f"C{100 + index:03d}"),
                "Product ID": str(product_row.get("Product ID") or f"PX{index:04d}"),
                "SKU": sku or f"SKU-X{index:04d}",
                "Quantity": str(quantity),
                "Unit Price": unit_price,
                "Store Code": str(row.get("Store Code") or "ST-01"),
                "Category": category,
                "Product Group": group_name,
                "Available Qty": available_qty,
                "In Transit Qty": str(2 + (index % 7)),
                "Lead Time Days": str(4 + (index % 6)),
                "Supplier MOQ": str(8 + (index % 5) * 2),
                "Service Level Target": f"{0.90 + (index % 5) * 0.01:.2f}",
                "Supplier ID": "demo",
                "Supplier Name": "Demo Supplier",
                "Received Qty": str(max(quantity - (1 if index % 19 == 0 else 0), 0)),
                "Promised Date": str(row.get("Order Date") or "2026-01-01"),
                "Actual Delivery Date": str(row.get("Order Date") or "2026-01-01"),
                "Payment Provider": "stripe" if index % 3 else "paypal",
                "Payment Amount": f"{payment_amount:.2f}",
                "Refund Amount": "0.00",
                "Order Status": "returned" if returned_qty == "1" else "completed",
                "Discount Rate": f"{0.01 * (index % 4):.2f}",
                "Returned Qty": returned_qty,
            }
        )
    return output


def build_demo_shipments() -> list[dict[str, str]]:
    base_date = datetime(2025, 1, 7, tzinfo=UTC)
    plan = [
        ("S001", "ORD001", "ST-01", "DHL", "processing", 2, None),
        ("S002", "ORD002", "ST-01", "UPS", "delayed", 2, 4),
        ("S003", "ORD003", "ST-02", "DHL", "delivered", 2, 2),
        ("S004", "ORD004", "ST-02", "FedEx", "in_transit", 2, None),
        ("S005", "ORD005", "ST-02", "UPS", "delivered", 2, 1),
        ("S006", "ORD006", "ST-03", "DHL", "delayed", 2, 5),
        ("S007", "ORD007", "ST-03", "FedEx", "processing", 2, None),
        ("S008", "ORD008", "ST-03", "UPS", "delivered", 2, 2),
        ("S009", "ORD009", "ST-01", "DHL", "delivered", 2, 3),
        ("S010", "ORD010", "ST-01", "UPS", "in_transit", 2, None),
        ("S011", "ORD011", "ST-01", "DHL", "delivered", 2, 2),
        ("S012", "ORD012", "ST-01", "FedEx", "processing", 2, None),
    ]
    rows: list[dict[str, str]] = []
    for index, (shipment_id, order_id, store_code, carrier, status, promised_offset, actual_offset) in enumerate(plan):
        order_date = (base_date + timedelta(days=index)).date()
        promised_date = order_date + timedelta(days=promised_offset)
        actual_date = "" if actual_offset is None else (order_date + timedelta(days=actual_offset)).isoformat()
        rows.append(
            {
                "Shipment ID": shipment_id,
                "Order ID": order_id,
                "Store Code": store_code,
                "Carrier": carrier,
                "Shipment Status": status,
                "Promised Date": promised_date.isoformat(),
                "Actual Delivery Date": actual_date,
                "Order Date": order_date.isoformat(),
                "Inventory Lag Days": str(max(promised_offset - 1, 0)),
            }
        )
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def clear_stale_upload_artifacts(*, root: Path, upload_id: str) -> None:
    artifact_root = root / "data" / "artifacts"
    if artifact_root.exists():
        for candidate in artifact_root.rglob(f"{upload_id}_*.json"):
            candidate.unlink(missing_ok=True)
    for candidate in [
        root / "data" / "uploads" / f"{upload_id}.json",
        root / "data" / "uploads" / f"{upload_id}_orders.csv",
        root / "data" / "uploads" / f"{upload_id}_shipments.csv",
        root / "data" / "artifacts" / "setup" / "sessions" / "demo-session.json",
        root / "data" / "uploads" / "demo-session.json",
    ]:
        candidate.unlink(missing_ok=True)


def write_setup_session(
    *,
    setup_dir: Path,
    uploads_dir: Path,
    metadata: dict[str, object],
    transform_payload: dict[str, object],
    forecast_payload: dict[str, object],
    dashboard_payload: dict[str, object],
) -> None:
    now_value = datetime.now(UTC).replace(microsecond=0).isoformat()
    session = {
        "session_id": "demo-session",
        "created_at": now_value,
        "updated_at": now_value,
        "sample_mode": True,
        "store": {
            "name": "RetailOps Demo Store",
            "code": "DEMO",
            "currency": "EUR",
            "timezone": "Europe/Helsinki",
        },
        "source": {
            "type": "csv",
            "name": "demo-session-csv",
            "config": {
                "file_path": str(metadata["stored_path"]),
                "delimiter": ",",
                "encoding": "utf-8",
            },
            "source_id": 1,
            "discovered_columns": list(metadata.get("mapping", {}).values()),
        },
        "mapping": dict(metadata.get("mapping", {})),
        "enabled_modules": [
            "analytics_kpi",
            "forecasting",
            "shipment_risk",
            "stockout_intelligence",
            "reorder_engine",
            "returns_intelligence",
            "dashboard_hub",
        ],
        "artifacts": {
            "upload_metadata_path": str(uploads_dir / "demo-session.json"),
            "transform_artifact_path": transform_payload.get("artifact_path"),
            "forecast_artifact_path": forecast_payload.get("artifact_path"),
            "dashboard_artifact_path": dashboard_payload.get("artifact_path"),
        },
        "transform_summary": transform_payload,
        "dashboard_summary": dashboard_payload,
        "forecast_summary": forecast_payload,
        "training_summary": {
            "status": "not_run",
            "message": "Starter demo session uses baseline models.",
        },
        "steps": {
            "create_store": {"key": "create_store", "label": "Create store", "status": "done", "message": "Demo store created.", "attempts": 1, "artifact_path": None, "last_updated_at": now_value},
            "configure_source": {"key": "configure_source", "label": "Configure source", "status": "done", "message": "Demo CSV source configured.", "attempts": 1, "artifact_path": None, "last_updated_at": now_value},
            "test_connection": {"key": "test_connection", "label": "Test connection", "status": "done", "message": "Demo files are local and reachable.", "attempts": 1, "artifact_path": None, "last_updated_at": now_value},
            "map_columns": {"key": "map_columns", "label": "Map columns", "status": "done", "message": "Column mapping pre-filled for the demo session.", "attempts": 1, "artifact_path": None, "last_updated_at": now_value},
            "import_data": {"key": "import_data", "label": "Import data", "status": "done", "message": "Demo upload metadata has been written.", "attempts": 1, "artifact_path": str(uploads_dir / "demo-session.json"), "last_updated_at": now_value},
            "run_transform": {"key": "run_transform", "label": "Run transform", "status": "done", "message": "Starter transform completed.", "attempts": 1, "artifact_path": transform_payload.get("artifact_path"), "last_updated_at": now_value},
            "enable_modules": {"key": "enable_modules", "label": "Enable modules", "status": "done", "message": "Default demo modules enabled.", "attempts": 1, "artifact_path": None, "last_updated_at": now_value},
            "train_models": {"key": "train_models", "label": "Train models", "status": "done", "message": "Baseline forecast artifact prepared for the demo.", "attempts": 1, "artifact_path": forecast_payload.get("artifact_path"), "last_updated_at": now_value},
            "publish_dashboards": {"key": "publish_dashboards", "label": "Publish dashboards", "status": "done", "message": "Dashboard artifacts published.", "attempts": 1, "artifact_path": dashboard_payload.get("artifact_path"), "last_updated_at": now_value},
        },
        "logs": [
            {
                "timestamp": now_value,
                "step": "session",
                "level": "info",
                "message": "Demo session prepared by scripts/load_demo_data.sh.",
            }
        ],
    }
    session_dir = setup_dir / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "demo-session.json").write_text(
        json.dumps(session, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    demo_metadata = dict(metadata)
    demo_metadata["upload_id"] = "demo-session"
    (uploads_dir / "demo-session.json").write_text(
        json.dumps(demo_metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


sample_orders_path = root / "data" / "demo_csv" / "sample_orders_easy_csv_150.csv"
sample_products_path = root / "data" / "demo_csv" / "sample_products_120.csv"
sample_inventory_path = root / "data" / "demo_csv" / "sample_inventory_snapshots_360.csv"
if not sample_orders_path.exists():
    raise SystemExit(f"Missing demo source CSV: {sample_orders_path}")
if not sample_products_path.exists():
    raise SystemExit(f"Missing demo products CSV: {sample_products_path}")
if not sample_inventory_path.exists():
    raise SystemExit(f"Missing demo inventory CSV: {sample_inventory_path}")

uploads_dir = root / "data" / "uploads"
transforms_dir = root / "data" / "artifacts" / "transforms"
dashboards_dir = root / "data" / "artifacts" / "dashboards"
forecasts_dir = root / "data" / "artifacts" / "forecasts"
setup_dir = root / "data" / "artifacts" / "setup"
dashboard_hub_dir = root / "data" / "artifacts" / "dashboard_hub"
model_registry_dir = root / "data" / "artifacts" / "model_registry"

clear_stale_upload_artifacts(root=root, upload_id=upload_id)

for directory in (
    uploads_dir,
    transforms_dir,
    dashboards_dir,
    forecasts_dir,
    setup_dir,
    dashboard_hub_dir,
    model_registry_dir,
):
    directory.mkdir(parents=True, exist_ok=True)

orders_fieldnames = [
    "Order ID",
    "Order Date",
    "Customer ID",
    "Product ID",
    "SKU",
    "Quantity",
    "Unit Price",
    "Store Code",
    "Category",
    "Product Group",
    "Available Qty",
    "In Transit Qty",
    "Lead Time Days",
    "Supplier MOQ",
    "Service Level Target",
    "Supplier ID",
    "Supplier Name",
    "Received Qty",
    "Promised Date",
    "Actual Delivery Date",
    "Payment Provider",
    "Payment Amount",
    "Refund Amount",
    "Order Status",
    "Discount Rate",
    "Returned Qty",
]
shipments_fieldnames = [
    "Shipment ID",
    "Order ID",
    "Store Code",
    "Carrier",
    "Shipment Status",
    "Promised Date",
    "Actual Delivery Date",
    "Order Date",
    "Inventory Lag Days",
]

products = {row["SKU"]: row for row in read_csv_rows(sample_products_path)}
inventory_by_sku = latest_inventory_by_sku(sample_inventory_path)
orders_rows = build_enriched_orders(
    source_orders=read_csv_rows(sample_orders_path),
    products=products,
    inventory_by_sku=inventory_by_sku,
)
shipments_rows = build_demo_shipments()

orders_csv = uploads_dir / f"{upload_id}_orders.csv"
shipments_csv = uploads_dir / f"{upload_id}_shipments.csv"
write_csv(orders_csv, orders_fieldnames, orders_rows)
write_csv(shipments_csv, shipments_fieldnames, shipments_rows)

metadata = {
    "upload_id": upload_id,
    "filename": orders_csv.name,
    "stored_path": str(orders_csv),
    "delimiter": ",",
    "encoding": "utf-8",
    "mapping": {
        "order_id": "Order ID",
        "order_date": "Order Date",
        "customer_id": "Customer ID",
        "product_id": "Product ID",
        "sku": "SKU",
        "quantity": "Quantity",
        "unit_price": "Unit Price",
        "store_code": "Store Code",
        "category": "Category",
        "product_group": "Product Group",
        "inventory": "Available Qty",
    },
    "columns": orders_fieldnames,
    "related_files": {
        "orders_csv": str(orders_csv),
        "shipments_csv": str(shipments_csv),
    },
    "transform_summary": None,
    "forecast_summary": None,
    "dashboard_summary": None,
}
metadata_path = uploads_dir / f"{upload_id}.json"
metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

transform = run_first_transform(upload_id=upload_id, artifact_dir=transforms_dir, metadata=metadata)
transform_payload = transform.to_dict()
forecast = run_first_forecast(upload_id=upload_id, artifact_dir=forecasts_dir, transform_summary=transform_payload)
forecast_payload = forecast.to_dict()
dashboard = publish_first_dashboard(
    upload_id=upload_id,
    filename=orders_csv.name,
    transform_summary=transform_payload,
    artifact_dir=dashboards_dir,
)
dashboard_payload = dashboard.to_dict()

metadata["transform_summary"] = transform_payload
metadata["forecast_summary"] = forecast_payload
metadata["dashboard_summary"] = dashboard_payload
metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

manifest = {
    "upload_id": upload_id,
    "metadata_path": str(metadata_path),
    "orders_csv_path": str(orders_csv),
    "shipments_csv_path": str(shipments_csv),
    "transform_artifact_path": transform_payload["artifact_path"],
    "forecast_artifact_path": forecast_payload["artifact_path"],
    "dashboard_artifact_path": dashboard_payload["artifact_path"],
}
manifest_path = setup_dir / f"{upload_id}_manifest.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

publish_dashboard_workspace(
    upload_id=upload_id,
    uploads_dir=uploads_dir,
    artifact_root=dashboard_hub_dir,
    refresh=True,
    max_rows=8,
)
run_model_registry(artifact_dir=model_registry_dir, refresh=True)

alias_dashboard_path = dashboards_dir / f"{upload_id}_1.json"
alias_dashboard_payload = dict(dashboard_payload)
alias_dashboard_payload["dashboard_id"] = "1"
alias_dashboard_payload["artifact_path"] = str(alias_dashboard_path)
alias_dashboard_path.write_text(
    json.dumps(alias_dashboard_payload, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

write_setup_session(
    setup_dir=setup_dir,
    uploads_dir=uploads_dir,
    metadata=metadata,
    transform_payload=transform_payload,
    forecast_payload=forecast_payload,
    dashboard_payload=alias_dashboard_payload,
)

manifest["dashboard_workspace_artifact_path"] = str((dashboard_hub_dir / f"{upload_id}_workspace.json").resolve())
manifest["model_registry_artifact_path"] = str((model_registry_dir / "model_registry.json").resolve())
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(manifest, ensure_ascii=False, indent=2))
PYCODE
