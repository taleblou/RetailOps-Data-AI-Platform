from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import CustomerIntelligenceArtifactResponse, CustomerSegmentResponse
from .service import get_customer_intelligence_artifact, get_customer_segment

router = APIRouter(prefix="/api/v1/customer-intelligence", tags=["customer-intelligence"])


@router.get("/summary", response_model=CustomerIntelligenceArtifactResponse)
async def get_customer_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/customer_intelligence"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> CustomerIntelligenceArtifactResponse:
    try:
        payload = get_customer_intelligence_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerIntelligenceArtifactResponse.model_validate(payload)


@router.get("/customers/{customer_id}", response_model=CustomerSegmentResponse)
async def get_customer_detail(
    customer_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/customer_intelligence"),
    refresh: bool = Query(default=False),
) -> CustomerSegmentResponse:
    try:
        payload = get_customer_segment(
            upload_id=upload_id,
            customer_id=customer_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerSegmentResponse.model_validate(payload)
