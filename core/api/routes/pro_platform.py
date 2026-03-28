from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from core.api.schemas.pro_platform import ProPlatformSummaryResponse
from modules.advanced_serving.service import build_phase20_advanced_serving_artifact
from modules.cdc.service import build_phase20_cdc_artifact
from modules.feature_store.service import build_phase20_feature_store_artifact
from modules.lakehouse.service import build_phase20_lakehouse_artifact
from modules.metadata.service import build_phase20_metadata_artifact
from modules.query_layer.service import build_phase20_query_layer_artifact
from modules.streaming.service import build_phase20_streaming_artifact

router = APIRouter(prefix="/api/v1/pro-platform", tags=["pro-platform"])


@router.get("/summary", response_model=ProPlatformSummaryResponse)
async def get_phase20_pro_platform_summary(
    artifact_dir: str = Query(default="data/artifacts/pro_platform"),
    refresh: bool = Query(default=False),
) -> ProPlatformSummaryResponse:
    try:
        base_dir = Path(artifact_dir)
        modules = {
            "cdc": build_phase20_cdc_artifact(
                artifact_dir=base_dir / "cdc",
                refresh=refresh,
            ),
            "streaming": build_phase20_streaming_artifact(
                artifact_dir=base_dir / "streaming",
                refresh=refresh,
            ),
            "lakehouse": build_phase20_lakehouse_artifact(
                artifact_dir=base_dir / "lakehouse",
                refresh=refresh,
            ),
            "query_layer": build_phase20_query_layer_artifact(
                artifact_dir=base_dir / "query_layer",
                refresh=refresh,
            ),
            "metadata": build_phase20_metadata_artifact(
                artifact_dir=base_dir / "metadata",
                refresh=refresh,
            ),
            "feature_store": build_phase20_feature_store_artifact(
                artifact_dir=base_dir / "feature_store",
                refresh=refresh,
            ),
            "advanced_serving": build_phase20_advanced_serving_artifact(
                artifact_dir=base_dir / "advanced_serving",
                refresh=refresh,
            ),
        }
        payload = {
            "phase": 20,
            "platform_name": "RetailOps Pro Data Platform",
            "modules": modules,
            "module_count": len(modules),
            "artifact_root": str(base_dir.resolve()),
        }
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProPlatformSummaryResponse.model_validate(payload)
