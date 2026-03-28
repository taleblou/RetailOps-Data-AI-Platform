from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHASE20_FEATURE_STORE_VERSION = "phase20-feature-store-v1"


def _read_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_phase20_feature_store_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "phase20_feature_store_blueprint.json"
    if not refresh:
        cached = _read_or_none(artifact_path)
        if cached is not None:
            return cached

    module_root = Path(__file__).resolve().parent
    payload = {
        "module_name": "feature_store",
        "phase": 20,
        "status": "blueprint_ready",
        "generated_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(artifact_path.resolve()),
        "engine": "feast",
        "offline_store": "postgres_and_iceberg",
        "online_store": "redis",
        "feature_views": [
            {
                "name": "stockout_features_view",
                "entity": "sku",
                "ttl_days": 14,
                "owner": "inventory-ai",
            },
            {
                "name": "shipment_delay_features_view",
                "entity": "shipment_id",
                "ttl_days": 7,
                "owner": "logistics-ai",
            },
        ],
        "materialization_jobs": [
            "materialize_stockout_features_hourly",
            "materialize_shipment_delay_features_every_15m",
        ],
        "config_templates": {
            "feature_store": str((module_root / "repo" / "feature_store.yaml").resolve()),
            "feature_views": str((module_root / "repo" / "feature_views.py").resolve()),
        },
    }
    return _write_payload(artifact_path, payload)
