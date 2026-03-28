from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHASE20_STREAMING_VERSION = "phase20-streaming-v1"


def _read_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_phase20_streaming_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "phase20_streaming_blueprint.json"
    if not refresh:
        cached = _read_or_none(artifact_path)
        if cached is not None:
            return cached

    module_root = Path(__file__).resolve().parent
    payload = {
        "module_name": "streaming",
        "phase": 20,
        "status": "blueprint_ready",
        "generated_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(artifact_path.resolve()),
        "runtime": "redpanda",
        "consumer_groups": [
            "retailops-cdc-consumers",
            "retailops-lakehouse-writers",
            "retailops-feature-materialization",
            "retailops-ops-alerts",
        ],
        "topics": [
            {
                "name": "retailops.raw_cdc.public.orders",
                "partitions": 6,
                "retention_hours": 168,
                "cleanup_policy": "delete",
            },
            {
                "name": "retailops.bronze.orders",
                "partitions": 6,
                "retention_hours": 720,
                "cleanup_policy": "compact,delete",
            },
            {
                "name": "retailops.features.materialized.stockout",
                "partitions": 3,
                "retention_hours": 168,
                "cleanup_policy": "compact",
            },
        ],
        "processors": [
            {
                "name": "cdc_to_bronze_router",
                "input_topic": "retailops.raw_cdc.public.orders",
                "output_topic": "retailops.bronze.orders",
                "responsibility": "normalize Debezium envelopes into bronze events",
            },
            {
                "name": "shipment_delay_feature_enricher",
                "input_topic": "retailops.bronze.shipments",
                "output_topic": "retailops.features.materialized.shipment_delay",
                "responsibility": (
                    "attach carrier and regional aggregates before feature materialization"
                ),
            },
        ],
        "config_templates": {
            "topics": str((module_root / "config" / "topics.yaml").resolve()),
            "processors": str((module_root / "config" / "processors.yaml").resolve()),
        },
    }
    return _write_payload(artifact_path, payload)
