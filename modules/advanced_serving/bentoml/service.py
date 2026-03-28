from __future__ import annotations

from bentoml import Service
from bentoml.io import JSON

svc = Service(name="retailops-advanced-serving")


@svc.api(input=JSON(), output=JSON())
def predict(payload: dict[str, object]) -> dict[str, object]:
    return {
        "status": "shadow_ready",
        "received": payload,
        "message": (
            "Phase 20 BentoML starter runtime is active and ready for "
            "project-specific model wiring."
        ),
    }
