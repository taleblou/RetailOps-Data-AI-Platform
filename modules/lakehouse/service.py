from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHASE20_LAKEHOUSE_VERSION = "phase20-lakehouse-v1"


def _read_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_phase20_lakehouse_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "phase20_lakehouse_blueprint.json"
    if not refresh:
        cached = _read_or_none(artifact_path)
        if cached is not None:
            return cached

    module_root = Path(__file__).resolve().parent
    payload = {
        "module_name": "lakehouse",
        "phase": 20,
        "status": "blueprint_ready",
        "generated_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(artifact_path.resolve()),
        "catalog_type": "iceberg-rest",
        "table_format": "iceberg",
        "object_storage": "minio",
        "layers": [
            {
                "layer_name": "bronze",
                "purpose": "immutable landing zone for raw CDC and batch events",
                "tables": ["bronze_orders", "bronze_order_items", "bronze_inventory_snapshots"],
            },
            {
                "layer_name": "silver",
                "purpose": "cleaned retail entities and conformed history",
                "tables": ["silver_orders", "silver_products", "silver_shipments"],
            },
            {
                "layer_name": "gold",
                "purpose": "analytics and AI-ready marts",
                "tables": [
                    "gold_store_kpis",
                    "gold_stockout_features",
                    "gold_shipment_delay_features",
                ],
            },
        ],
        "spark_jobs": [
            "bronze_to_silver_orders",
            "silver_to_gold_store_kpis",
            "materialize_stockout_features",
        ],
        "config_templates": {
            "layout": str((module_root / "config" / "lakehouse_layout.yaml").resolve()),
            "job_template": str((module_root / "jobs" / "bronze_to_silver.sql").resolve()),
        },
    }
    return _write_payload(artifact_path, payload)
