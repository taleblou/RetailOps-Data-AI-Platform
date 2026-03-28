from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHASE20_CDC_VERSION = "phase20-cdc-v1"


def _read_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_phase20_cdc_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "phase20_cdc_blueprint.json"
    if not refresh:
        cached = _read_or_none(artifact_path)
        if cached is not None:
            return cached

    module_root = Path(__file__).resolve().parent
    payload = {
        "module_name": "cdc",
        "phase": 20,
        "status": "blueprint_ready",
        "generated_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(artifact_path.resolve()),
        "connector_name": "retailops-postgres-cdc",
        "source_database": "postgresql",
        "kafka_compatible_runtime": "redpanda",
        "raw_event_topic_prefix": "retailops.raw_cdc",
        "snapshot_mode": "initial",
        "replication_slot": "retailops_cdc_slot",
        "publication_name": "retailops_cdc_publication",
        "management_actions": [
            "create connector config",
            "bootstrap replication slot",
            "validate snapshot completion",
            "switch to streaming mode",
            "monitor connector lag",
        ],
        "emitted_topics": [
            "retailops.raw_cdc.public.products",
            "retailops.raw_cdc.public.orders",
            "retailops.raw_cdc.public.order_items",
            "retailops.raw_cdc.public.inventory_snapshots",
        ],
        "config_templates": {
            "debezium_connector": str(
                (module_root / "config" / "debezium-postgres.json").resolve()
            ),
            "cdc_profile": str((module_root / "config" / "cdc_profile.yaml").resolve()),
        },
        "connector_properties": {
            "plugin.name": "pgoutput",
            "slot.name": "retailops_cdc_slot",
            "publication.name": "retailops_cdc_publication",
            "topic.prefix": "retailops.raw_cdc",
            "snapshot.mode": "initial",
            "tombstones.on.delete": False,
            "decimal.handling.mode": "double",
            "heartbeat.interval.ms": 10000,
            "schema.history.internal": "io.debezium.storage.kafka.history.KafkaSchemaHistory",
        },
    }
    return _write_payload(artifact_path, payload)
