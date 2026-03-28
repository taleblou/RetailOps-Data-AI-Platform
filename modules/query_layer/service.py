from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHASE20_QUERY_LAYER_VERSION = "phase20-query-layer-v1"


def _read_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_phase20_query_layer_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "phase20_query_layer_blueprint.json"
    if not refresh:
        cached = _read_or_none(artifact_path)
        if cached is not None:
            return cached

    module_root = Path(__file__).resolve().parent
    payload = {
        "module_name": "query_layer",
        "phase": 20,
        "status": "blueprint_ready",
        "generated_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(artifact_path.resolve()),
        "engine": "trino",
        "catalogs": [
            {
                "name": "postgres",
                "connector_name": "postgresql",
                "target": "operational retail database",
            },
            {
                "name": "iceberg",
                "connector_name": "iceberg",
                "target": "lakehouse analytics tables",
            },
        ],
        "federation_queries": [
            (
                "SELECT o.order_id, f.stockout_probability "
                "FROM postgres.mart.orders o "
                "JOIN iceberg.gold.stockout_features f ON o.sku = f.sku"
            ),
            "SELECT store_code, SUM(revenue) FROM iceberg.gold.store_kpis GROUP BY 1",
        ],
        "config_templates": {
            "postgres_catalog": str(
                (module_root / "config" / "catalogs" / "postgres.properties").resolve()
            ),
            "iceberg_catalog": str(
                (module_root / "config" / "catalogs" / "iceberg.properties").resolve()
            ),
        },
    }
    return _write_payload(artifact_path, payload)
