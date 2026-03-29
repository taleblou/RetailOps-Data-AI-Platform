from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import SupplierProcurementArtifactResponse, SupplierProcurementResponse
from .service import get_supplier_procurement_artifact, get_supplier_procurement_item

router = APIRouter(prefix="/api/v1/supplier-procurement", tags=["supplier-procurement"])


@router.get("/summary", response_model=SupplierProcurementArtifactResponse)
async def get_supplier_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/supplier_procurement"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> SupplierProcurementArtifactResponse:
    try:
        payload = get_supplier_procurement_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SupplierProcurementArtifactResponse.model_validate(payload)


@router.get("/suppliers/{supplier_id}", response_model=SupplierProcurementResponse)
async def get_supplier_detail(
    supplier_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/supplier_procurement"),
    refresh: bool = Query(default=False),
) -> SupplierProcurementResponse:
    try:
        payload = get_supplier_procurement_item(
            upload_id=upload_id,
            supplier_id=supplier_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SupplierProcurementResponse.model_validate(payload)
