from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modules.forecasting.service import get_or_create_phase10_batch_artifact
from modules.reorder_engine.service import get_reorder_recommendations
from modules.shipment_risk.service import (
    get_open_order_predictions,
    get_or_create_phase11_artifact,
    predict_shipment_delay,
)
from modules.stockout_intelligence.service import (
    get_or_create_phase12_stockout_artifact,
    get_stockout_sku_predictions,
)

PHASE16_ARTIFACT_SUFFIX = "phase16_serving_bundle"
STANDARD_RESPONSE_FIELDS = [
    "prediction",
    "confidence",
    "interval",
    "model_version",
    "feature_timestamp",
    "explanation_summary",
]
AVAILABLE_ONLINE_ENDPOINTS = [
    "/api/v1/serving/forecast/products/{product_id}",
    "/api/v1/serving/shipment-risk/open-orders/{shipment_id}",
    "/api/v1/serving/predict/shipment-delay",
    "/api/v1/serving/stockout-risk/{sku}",
    "/api/v1/serving/reorder/{sku}",
]


class ServingArtifactNotFoundError(FileNotFoundError):
    """Raised when a serving-layer entity cannot be found."""


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Artifact file is invalid: {path}")
    return payload


def _save_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _latest_artifact_path(upload_id: str, artifact_dir: Path) -> Path | None:
    pattern = f"{upload_id}_{PHASE16_ARTIFACT_SUFFIX}_*.json"
    matches = sorted(
        artifact_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True
    )
    if matches:
        return matches[0]
    return None


def _build_batch_job(
    *,
    job_name: str,
    prediction_type: str,
    source_module: str,
    generated_at: str,
    records_served: int,
    artifact_path: str,
) -> dict[str, Any]:
    return {
        "job_name": job_name,
        "prediction_type": prediction_type,
        "source_module": source_module,
        "status": "completed",
        "records_served": records_served,
        "generated_at": generated_at,
        "artifact_path": artifact_path,
    }


def run_phase16_batch_serving(
    *,
    upload_id: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    shipment_artifact_dir: Path,
    stockout_artifact_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    forecast_artifact = get_or_create_phase10_batch_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=forecast_artifact_dir,
        refresh=refresh,
    )
    shipment_artifact = get_or_create_phase11_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=shipment_artifact_dir,
        refresh=refresh,
    )
    stockout_artifact = get_or_create_phase12_stockout_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=stockout_artifact_dir,
        refresh=refresh,
    )

    generated_at = _utc_now_iso()
    serving_run_id = f"phase16-serving-{uuid.uuid4().hex[:12]}"
    jobs = [
        _build_batch_job(
            job_name="nightly_forecast",
            prediction_type="forecast",
            source_module="modules.forecasting",
            generated_at=generated_at,
            records_served=int((forecast_artifact.get("summary") or {}).get("active_products", 0)),
            artifact_path=str(forecast_artifact.get("artifact_path", "")),
        ),
        _build_batch_job(
            job_name="stockout_daily_scoring",
            prediction_type="stockout_risk",
            source_module="modules.stockout_intelligence",
            generated_at=generated_at,
            records_served=int((stockout_artifact.get("summary") or {}).get("total_skus", 0)),
            artifact_path=str(stockout_artifact.get("artifact_path", "")),
        ),
        _build_batch_job(
            job_name="shipment_open_order_scoring",
            prediction_type="shipment_delay",
            source_module="modules.shipment_risk",
            generated_at=generated_at,
            records_served=int((shipment_artifact.get("summary") or {}).get("open_orders", 0)),
            artifact_path=str(shipment_artifact.get("artifact_path", "")),
        ),
    ]

    payload = {
        "serving_run_id": serving_run_id,
        "upload_id": upload_id,
        "generated_at": generated_at,
        "status": "completed",
        "jobs": jobs,
        "available_online_endpoints": AVAILABLE_ONLINE_ENDPOINTS,
        "standard_response_fields": STANDARD_RESPONSE_FIELDS,
    }
    artifact_suffix = generated_at.replace(":", "").replace("+00:00", "Z")
    artifact_path = artifact_dir / f"{upload_id}_{PHASE16_ARTIFACT_SUFFIX}_{artifact_suffix}.json"
    payload["artifact_path"] = str(artifact_path)
    _save_json(payload, artifact_path)
    return payload


def get_or_create_phase16_batch_artifact(
    *,
    upload_id: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    shipment_artifact_dir: Path,
    stockout_artifact_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if not refresh:
        existing = _latest_artifact_path(upload_id=upload_id, artifact_dir=artifact_dir)
        if existing is not None:
            return _load_json(existing)
    return run_phase16_batch_serving(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        shipment_artifact_dir=shipment_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )


def _base_response(
    *,
    serving_type: str,
    entity_id: str,
    prediction: dict[str, Any],
    model_version: str,
    feature_timestamp: str,
    explanation_summary: str,
    source_artifact: str,
    confidence: float | None = None,
    interval: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "serving_type": serving_type,
        "entity_id": entity_id,
        "prediction": prediction,
        "confidence": confidence,
        "interval": interval,
        "model_version": model_version,
        "feature_timestamp": feature_timestamp,
        "explanation_summary": explanation_summary,
        "source_artifact": source_artifact,
        "metadata": metadata or {},
    }


def _find_forecast_product(
    *, upload_id: str, uploads_dir: Path, artifact_dir: Path, refresh: bool
) -> dict[str, Any]:
    artifact = get_or_create_phase10_batch_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    products = artifact.get("products") or []
    artifact_path = str(artifact.get("artifact_path", ""))
    return {"products": products, "artifact_path": artifact_path}


def _extract_forecast_horizon(product: dict[str, Any], *, horizon_days: int) -> dict[str, Any]:
    horizons = product.get("horizons") or []
    for item in horizons:
        if int(item.get("horizon_days", 0)) == horizon_days:
            return item
    return {}


def get_forecast_serving_response(
    *,
    upload_id: str,
    product_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact = _find_forecast_product(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    normalized_product_id = product_id.strip().lower()
    for product in artifact["products"]:
        if str(product.get("product_id", "")).lower() != normalized_product_id:
            continue
        horizon_7 = _extract_forecast_horizon(product, horizon_days=7)
        horizon_14 = _extract_forecast_horizon(product, horizon_days=14)
        horizon_30 = _extract_forecast_horizon(product, horizon_days=30)
        interval = None
        if horizon_7:
            interval = {
                "horizon_days": 7,
                "p10": _safe_float(horizon_7.get("p10")),
                "p50": _safe_float(horizon_7.get("p50")),
                "p90": _safe_float(horizon_7.get("p90")),
            }
        prediction = {
            "selected_model": str(product.get("selected_model", "")),
            "point_forecast_7d": _safe_float(horizon_7.get("p50")),
            "point_forecast_14d": _safe_float(horizon_14.get("p50")),
            "point_forecast_30d": _safe_float(horizon_30.get("p50")),
            "stockout_probability_7d": _safe_float(horizon_7.get("stockout_probability")),
        }
        metadata = {
            "category": str(product.get("category", "")),
            "product_group": str(product.get("product_group", "")),
            "history_points": int(product.get("history_points", 0)),
            "daily_forecast": product.get("daily_forecast") or [],
            "backtest_metrics": product.get("backtest_metrics") or {},
        }
        return _base_response(
            serving_type="forecast",
            entity_id=str(product.get("product_id", "")),
            prediction=prediction,
            interval=interval,
            confidence=None,
            model_version=str(product.get("model_version", "")),
            feature_timestamp=str(product.get("feature_timestamp", "")),
            explanation_summary=str(product.get("explanation_summary", "")),
            source_artifact=artifact["artifact_path"],
            metadata=metadata,
        )
    raise ServingArtifactNotFoundError(
        f"Forecast product was not found for product_id={product_id}."
    )


def get_forecast_explain_response(
    *,
    upload_id: str,
    product_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    response = get_forecast_serving_response(
        upload_id=upload_id,
        product_id=product_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    metadata = response.get("metadata") or {}
    interval = response.get("interval") or {}
    backtest_metrics = metadata.get("backtest_metrics") or {}
    return {
        "serving_type": "forecast",
        "entity_id": response["entity_id"],
        "explanation_summary": response["explanation_summary"],
        "top_factors": [
            f"Selected model: {response['prediction'].get('selected_model', '')}",
            f"7-day p50 forecast: {response['prediction'].get('point_forecast_7d', 0.0):.2f}",
            (
                "7-day interval width: "
                f"{(_safe_float(interval.get('p90')) - _safe_float(interval.get('p10'))):.2f}"
            ),
            f"Backtest MAPE: {_safe_float(backtest_metrics.get('mape')):.4f}",
        ],
        "supporting_signals": {
            "history_points": metadata.get("history_points", 0),
            "category": metadata.get("category", ""),
            "product_group": metadata.get("product_group", ""),
        },
        "recommended_action": None,
        "model_version": response["model_version"],
        "feature_timestamp": response["feature_timestamp"],
        "source_artifact": response["source_artifact"],
    }


def get_shipment_open_order_serving_response(
    *,
    upload_id: str,
    shipment_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    payload = get_open_order_predictions(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        limit=500,
    )
    for item in payload.get("open_orders") or []:
        if str(item.get("shipment_id", "")) != shipment_id:
            continue
        probability = _safe_float(item.get("probability"))
        return _base_response(
            serving_type="shipment_delay",
            entity_id=str(item.get("shipment_id", "")),
            prediction={
                "order_id": str(item.get("order_id", "")),
                "probability": probability,
                "risk_band": str(item.get("risk_band", "")),
                "recommended_action": str(item.get("recommended_action", "")),
                "manual_review_required": bool(item.get("manual_review_required", False)),
            },
            confidence=max(probability, 1.0 - probability),
            interval=None,
            model_version=str(item.get("model_version", "")),
            feature_timestamp=str(item.get("feature_timestamp", "")),
            explanation_summary=str(item.get("explanation_summary", "")),
            source_artifact=str(payload.get("artifact_path", "")),
            metadata={
                "carrier": str(item.get("carrier", "")),
                "shipment_status": str(item.get("shipment_status", "")),
                "top_factors": item.get("top_factors") or [],
                "manual_review_reason": str(item.get("manual_review_reason", "")),
                "overdue_days": _safe_float(item.get("overdue_days")),
            },
        )
    raise ServingArtifactNotFoundError(
        f"Shipment '{shipment_id}' was not found in the shipment-risk open-order artifact."
    )


def get_shipment_open_order_explain_response(
    *,
    upload_id: str,
    shipment_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    response = get_shipment_open_order_serving_response(
        upload_id=upload_id,
        shipment_id=shipment_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    metadata = response.get("metadata") or {}
    return {
        "serving_type": "shipment_delay",
        "entity_id": response["entity_id"],
        "explanation_summary": response["explanation_summary"],
        "top_factors": metadata.get("top_factors") or [],
        "supporting_signals": {
            "carrier": metadata.get("carrier", ""),
            "shipment_status": metadata.get("shipment_status", ""),
            "overdue_days": metadata.get("overdue_days", 0.0),
            "manual_review_reason": metadata.get("manual_review_reason", ""),
        },
        "recommended_action": response["prediction"].get("recommended_action"),
        "model_version": response["model_version"],
        "feature_timestamp": response["feature_timestamp"],
        "source_artifact": response["source_artifact"],
    }


def get_manual_shipment_serving_response(payload: dict[str, Any]) -> dict[str, Any]:
    result = predict_shipment_delay(payload)
    probability = _safe_float(result.get("probability"))
    return _base_response(
        serving_type="shipment_delay",
        entity_id=str(result.get("shipment_id", "manual-input")),
        prediction={
            "order_id": str(result.get("order_id", "")),
            "probability": probability,
            "risk_band": str(result.get("risk_band", "")),
            "recommended_action": str(result.get("recommended_action", "")),
            "manual_review_required": bool(result.get("manual_review_required", False)),
        },
        confidence=max(probability, 1.0 - probability),
        interval=None,
        model_version=str(result.get("model_version", "")),
        feature_timestamp=str(result.get("feature_timestamp", "")),
        explanation_summary=str(result.get("explanation_summary", "")),
        source_artifact="inline-request",
        metadata={
            "carrier": str(result.get("carrier", "")),
            "shipment_status": str(result.get("shipment_status", "")),
            "top_factors": result.get("top_factors") or [],
            "manual_review_reason": str(result.get("manual_review_reason", "")),
            "overdue_days": _safe_float(result.get("overdue_days")),
        },
    )


def get_manual_shipment_explain_response(payload: dict[str, Any]) -> dict[str, Any]:
    response = get_manual_shipment_serving_response(payload)
    metadata = response.get("metadata") or {}
    return {
        "serving_type": "shipment_delay",
        "entity_id": response["entity_id"],
        "explanation_summary": response["explanation_summary"],
        "top_factors": metadata.get("top_factors") or [],
        "supporting_signals": {
            "carrier": metadata.get("carrier", ""),
            "shipment_status": metadata.get("shipment_status", ""),
            "overdue_days": metadata.get("overdue_days", 0.0),
        },
        "recommended_action": response["prediction"].get("recommended_action"),
        "model_version": response["model_version"],
        "feature_timestamp": response["feature_timestamp"],
        "source_artifact": response["source_artifact"],
    }


def get_stockout_serving_response(
    *,
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    store_code: str | None = None,
) -> dict[str, Any]:
    payload = get_stockout_sku_predictions(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        limit=500,
        store_code=store_code,
    )
    normalized_sku = sku.strip().lower()
    for item in payload.get("skus") or []:
        if str(item.get("sku", "")).lower() != normalized_sku:
            continue
        probability = _safe_float(item.get("stockout_probability"))
        return _base_response(
            serving_type="stockout_risk",
            entity_id=str(item.get("sku", "")),
            prediction={
                "store_code": str(item.get("store_code", "")),
                "stockout_probability": probability,
                "risk_band": str(item.get("risk_band", "")),
                "recommended_action": str(item.get("recommended_action", "")),
                "days_to_stockout": _safe_float(item.get("days_to_stockout")),
            },
            confidence=max(probability, 1.0 - probability),
            interval=None,
            model_version=str(item.get("model_version", "")),
            feature_timestamp=str(item.get("feature_timestamp", "")),
            explanation_summary=str(item.get("explanation_summary", "")),
            source_artifact=str(payload.get("artifact_path", "")),
            metadata={
                "available_qty": _safe_float(item.get("available_qty")),
                "inbound_qty": _safe_float(item.get("inbound_qty")),
                "lead_time_days": _safe_float(item.get("lead_time_days")),
                "expected_lost_sales_estimate": _safe_float(
                    item.get("expected_lost_sales_estimate")
                ),
                "reorder_urgency_score": _safe_float(item.get("reorder_urgency_score")),
                "demand_trend_ratio": _safe_float(item.get("demand_trend_ratio")),
            },
        )
    raise ServingArtifactNotFoundError(
        f"No stockout prediction exists for sku={sku} and upload_id={upload_id}."
    )


def get_stockout_explain_response(
    *,
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    store_code: str | None = None,
) -> dict[str, Any]:
    response = get_stockout_serving_response(
        upload_id=upload_id,
        sku=sku,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        store_code=store_code,
    )
    metadata = response.get("metadata") or {}
    prediction = response.get("prediction") or {}
    return {
        "serving_type": "stockout_risk",
        "entity_id": response["entity_id"],
        "explanation_summary": response["explanation_summary"],
        "top_factors": [
            f"Days to stockout: {_safe_float(prediction.get('days_to_stockout')):.2f}",
            f"Lead time: {_safe_float(metadata.get('lead_time_days')):.2f} days",
            f"Demand trend ratio: {_safe_float(metadata.get('demand_trend_ratio')):.2f}",
            f"Reorder urgency score: {_safe_float(metadata.get('reorder_urgency_score')):.2f}",
        ],
        "supporting_signals": {
            "available_qty": metadata.get("available_qty", 0.0),
            "inbound_qty": metadata.get("inbound_qty", 0.0),
            "expected_lost_sales_estimate": metadata.get("expected_lost_sales_estimate", 0.0),
        },
        "recommended_action": prediction.get("recommended_action"),
        "model_version": response["model_version"],
        "feature_timestamp": response["feature_timestamp"],
        "source_artifact": response["source_artifact"],
    }


def get_reorder_serving_response(
    *,
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    stockout_artifact_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    store_code: str | None = None,
) -> dict[str, Any]:
    payload = get_reorder_recommendations(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        limit=500,
        store_code=store_code,
    )
    normalized_sku = sku.strip().lower()
    for item in payload.get("recommendations") or []:
        if str(item.get("sku", "")).lower() != normalized_sku:
            continue
        stockout_probability = _safe_float(item.get("stockout_probability"))
        urgency_score = _safe_float(item.get("urgency_score")) / 100.0
        decision_confidence = min(max(stockout_probability, urgency_score), 1.0)
        return _base_response(
            serving_type="reorder",
            entity_id=str(item.get("sku", "")),
            prediction={
                "store_code": str(item.get("store_code", "")),
                "reorder_date": str(item.get("reorder_date", "")),
                "reorder_quantity": _safe_float(item.get("reorder_quantity")),
                "urgency": str(item.get("urgency", "")),
                "recommended_action": str(item.get("recommended_action", "")),
            },
            confidence=decision_confidence,
            interval=None,
            model_version=str(item.get("model_version", "")),
            feature_timestamp=str(item.get("feature_timestamp", "")),
            explanation_summary=str(item.get("rationale", "")),
            source_artifact=str(payload.get("artifact_path", "")),
            metadata={
                "current_inventory": _safe_float(item.get("current_inventory")),
                "inbound_qty": _safe_float(item.get("inbound_qty")),
                "lead_time_days": _safe_float(item.get("lead_time_days")),
                "supplier_moq": _safe_float(item.get("supplier_moq")),
                "service_level_target": _safe_float(item.get("service_level_target")),
                "days_to_stockout": _safe_float(item.get("days_to_stockout")),
                "stockout_probability": stockout_probability,
                "urgency_score": _safe_float(item.get("urgency_score")),
            },
        )
    raise ServingArtifactNotFoundError(
        f"No reorder recommendation exists for sku={sku} and upload_id={upload_id}."
    )


def get_reorder_explain_response(
    *,
    upload_id: str,
    sku: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    stockout_artifact_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    store_code: str | None = None,
) -> dict[str, Any]:
    response = get_reorder_serving_response(
        upload_id=upload_id,
        sku=sku,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
        store_code=store_code,
    )
    metadata = response.get("metadata") or {}
    prediction = response.get("prediction") or {}
    return {
        "serving_type": "reorder",
        "entity_id": response["entity_id"],
        "explanation_summary": response["explanation_summary"],
        "top_factors": [
            f"Days to stockout: {_safe_float(metadata.get('days_to_stockout')):.2f}",
            f"Lead time: {_safe_float(metadata.get('lead_time_days')):.2f} days",
            f"Supplier MOQ: {_safe_float(metadata.get('supplier_moq')):.2f}",
            f"Service level target: {_safe_float(metadata.get('service_level_target')):.2f}",
        ],
        "supporting_signals": {
            "current_inventory": metadata.get("current_inventory", 0.0),
            "inbound_qty": metadata.get("inbound_qty", 0.0),
            "stockout_probability": metadata.get("stockout_probability", 0.0),
            "urgency_score": metadata.get("urgency_score", 0.0),
        },
        "recommended_action": prediction.get("recommended_action"),
        "model_version": response["model_version"],
        "feature_timestamp": response["feature_timestamp"],
        "source_artifact": response["source_artifact"],
    }
