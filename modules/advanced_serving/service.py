from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHASE20_ADVANCED_SERVING_VERSION = "phase20-advanced-serving-v1"


def _read_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def build_phase20_advanced_serving_artifact(
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_path = artifact_dir / "phase20_advanced_serving_blueprint.json"
    if not refresh:
        cached = _read_or_none(artifact_path)
        if cached is not None:
            return cached

    module_root = Path(__file__).resolve().parent
    payload = {
        "module_name": "advanced_serving",
        "phase": 20,
        "status": "blueprint_ready",
        "generated_at": datetime.now(UTC).isoformat(),
        "artifact_path": str(artifact_path.resolve()),
        "platform": "bentoml",
        "services": [
            {
                "name": "forecasting-runtime",
                "model_alias": "champion",
                "deployment_mode": "primary",
            },
            {
                "name": "shipment-risk-runtime",
                "model_alias": "challenger",
                "deployment_mode": "shadow",
            },
        ],
        "shadow_deployments": [
            "shipment-risk-runtime",
            "return-risk-runtime",
        ],
        "config_templates": {
            "bentofile": str((module_root / "bentofile.yaml").resolve()),
            "service": str((module_root / "bentoml" / "service.py").resolve()),
        },
    }
    return _write_payload(artifact_path, payload)
