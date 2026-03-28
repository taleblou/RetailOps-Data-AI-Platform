from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHASE20_METADATA_VERSION = "phase20-metadata-v1"


def _read_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_phase20_metadata_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "phase20_metadata_blueprint.json"
    if not refresh:
        cached = _read_or_none(artifact_path)
        if cached is not None:
            return cached

    module_root = Path(__file__).resolve().parent
    payload = {
        "module_name": "metadata",
        "phase": 20,
        "status": "blueprint_ready",
        "generated_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(artifact_path.resolve()),
        "platform": "openmetadata",
        "lineage_enabled": True,
        "workflows": [
            {
                "name": "postgres_operational_ingestion",
                "source_type": "postgresql",
                "output": "operational schemas and tables",
            },
            {
                "name": "dbt_lineage_ingestion",
                "source_type": "dbt",
                "output": "model metadata and lineage",
            },
            {
                "name": "trino_catalog_ingestion",
                "source_type": "trino",
                "output": "lakehouse query-layer assets",
            },
        ],
        "config_templates": {
            "openmetadata_ingestion": str(
                (module_root / "config" / "openmetadata_ingestion.yaml").resolve()
            ),
        },
    }
    return _write_payload(artifact_path, payload)
