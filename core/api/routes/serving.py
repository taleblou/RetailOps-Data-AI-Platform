from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from core.serving.schemas import (
    ServingBatchArtifactResponse,
    ServingBatchRunRequest,
    ServingExplainResponse,
    ServingPredictionResponse,
)
from core.serving.service import (
    ServingArtifactNotFoundError,
    get_forecast_explain_response,
    get_forecast_serving_response,
    get_manual_shipment_explain_response,
    get_manual_shipment_serving_response,
    get_or_create_phase16_batch_artifact,
    get_reorder_explain_response,
    get_reorder_serving_response,
    get_shipment_open_order_explain_response,
    get_shipment_open_order_serving_response,
    get_stockout_explain_response,
    get_stockout_serving_response,
)
from modules.shipment_risk.schemas import ShipmentDelayPredictRequest

router = APIRouter(prefix="/api/v1/serving", tags=["serving-layer"])


@router.post("/batch/run", response_model=ServingBatchArtifactResponse)
async def run_serving_batch_jobs(
    payload: ServingBatchRunRequest,
) -> ServingBatchArtifactResponse:
    try:
        result = get_or_create_phase16_batch_artifact(
            upload_id=payload.upload_id,
            uploads_dir=Path(payload.uploads_dir),
            forecast_artifact_dir=Path(payload.forecast_artifact_dir),
            shipment_artifact_dir=Path(payload.shipment_artifact_dir),
            stockout_artifact_dir=Path(payload.stockout_artifact_dir),
            artifact_dir=Path(payload.artifact_dir),
            refresh=payload.refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingBatchArtifactResponse.model_validate(result)


@router.get("/batch/summary", response_model=ServingBatchArtifactResponse)
async def get_serving_batch_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    forecast_artifact_dir: str = Query(default="data/artifacts/forecasts"),
    shipment_artifact_dir: str = Query(default="data/artifacts/shipment_risk"),
    stockout_artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    artifact_dir: str = Query(default="data/artifacts/serving"),
    refresh: bool = Query(default=False),
) -> ServingBatchArtifactResponse:
    try:
        result = get_or_create_phase16_batch_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            forecast_artifact_dir=Path(forecast_artifact_dir),
            shipment_artifact_dir=Path(shipment_artifact_dir),
            stockout_artifact_dir=Path(stockout_artifact_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingBatchArtifactResponse.model_validate(result)


@router.get("/forecast/products/{product_id}", response_model=ServingPredictionResponse)
async def get_serving_forecast_product(
    product_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/forecasts"),
    refresh: bool = Query(default=False),
) -> ServingPredictionResponse:
    try:
        result = get_forecast_serving_response(
            upload_id=upload_id,
            product_id=product_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (ServingArtifactNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingPredictionResponse.model_validate(result)


@router.get("/forecast/products/{product_id}/explain", response_model=ServingExplainResponse)
async def get_serving_forecast_explain(
    product_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/forecasts"),
    refresh: bool = Query(default=False),
) -> ServingExplainResponse:
    try:
        result = get_forecast_explain_response(
            upload_id=upload_id,
            product_id=product_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (ServingArtifactNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingExplainResponse.model_validate(result)


@router.get(
    "/shipment-risk/open-orders/{shipment_id}",
    response_model=ServingPredictionResponse,
)
async def get_serving_shipment_open_order(
    shipment_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/shipment_risk"),
    refresh: bool = Query(default=False),
) -> ServingPredictionResponse:
    try:
        result = get_shipment_open_order_serving_response(
            upload_id=upload_id,
            shipment_id=shipment_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (ServingArtifactNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingPredictionResponse.model_validate(result)


@router.get(
    "/shipment-risk/open-orders/{shipment_id}/explain",
    response_model=ServingExplainResponse,
)
async def get_serving_shipment_open_order_explain(
    shipment_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/shipment_risk"),
    refresh: bool = Query(default=False),
) -> ServingExplainResponse:
    try:
        result = get_shipment_open_order_explain_response(
            upload_id=upload_id,
            shipment_id=shipment_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (ServingArtifactNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingExplainResponse.model_validate(result)


@router.post("/predict/shipment-delay", response_model=ServingPredictionResponse)
async def post_serving_shipment_delay(
    payload: ShipmentDelayPredictRequest,
) -> ServingPredictionResponse:
    result = get_manual_shipment_serving_response(payload.model_dump())
    return ServingPredictionResponse.model_validate(result)


@router.post("/predict/shipment-delay/explain", response_model=ServingExplainResponse)
async def post_serving_shipment_delay_explain(
    payload: ShipmentDelayPredictRequest,
) -> ServingExplainResponse:
    result = get_manual_shipment_explain_response(payload.model_dump())
    return ServingExplainResponse.model_validate(result)


@router.get("/stockout-risk/{sku}", response_model=ServingPredictionResponse)
async def get_serving_stockout(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    refresh: bool = Query(default=False),
    store_code: str | None = Query(default=None),
) -> ServingPredictionResponse:
    try:
        result = get_stockout_serving_response(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            store_code=store_code,
        )
    except (ServingArtifactNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingPredictionResponse.model_validate(result)


@router.get("/stockout-risk/{sku}/explain", response_model=ServingExplainResponse)
async def get_serving_stockout_explain(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    refresh: bool = Query(default=False),
    store_code: str | None = Query(default=None),
) -> ServingExplainResponse:
    try:
        result = get_stockout_explain_response(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            store_code=store_code,
        )
    except (ServingArtifactNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingExplainResponse.model_validate(result)


@router.get("/reorder/{sku}", response_model=ServingPredictionResponse)
async def get_serving_reorder(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    forecast_artifact_dir: str = Query(default="data/artifacts/forecasts"),
    stockout_artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    artifact_dir: str = Query(default="data/artifacts/reorder"),
    refresh: bool = Query(default=False),
    store_code: str | None = Query(default=None),
) -> ServingPredictionResponse:
    try:
        result = get_reorder_serving_response(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            forecast_artifact_dir=Path(forecast_artifact_dir),
            stockout_artifact_dir=Path(stockout_artifact_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            store_code=store_code,
        )
    except (ServingArtifactNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingPredictionResponse.model_validate(result)


@router.get("/reorder/{sku}/explain", response_model=ServingExplainResponse)
async def get_serving_reorder_explain(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    forecast_artifact_dir: str = Query(default="data/artifacts/forecasts"),
    stockout_artifact_dir: str = Query(default="data/artifacts/stockout_risk"),
    artifact_dir: str = Query(default="data/artifacts/reorder"),
    refresh: bool = Query(default=False),
    store_code: str | None = Query(default=None),
) -> ServingExplainResponse:
    try:
        result = get_reorder_explain_response(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            forecast_artifact_dir=Path(forecast_artifact_dir),
            stockout_artifact_dir=Path(stockout_artifact_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            store_code=store_code,
        )
    except (ServingArtifactNotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ServingExplainResponse.model_validate(result)
