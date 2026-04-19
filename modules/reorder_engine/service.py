# Project:      RetailOps Data & AI Platform
# Module:       modules.reorder_engine
# File:         service.py
# Path:         modules/reorder_engine/service.py
#
# Summary:      Implements the reorder engine service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for reorder engine workflows.
# Scope:        internal
# Status:       stable
#
# Author(s):    Morteza Taleblou
# Website:      https://taleblou.ir/
# Repository:   https://github.com/taleblou/RetailOps-Data-AI-Platform
#
# License:      Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
# Copyright:    (c) 2025 Morteza Taleblou
#
# Notes:
#   - Main types: ReorderArtifactNotFoundError, ReorderRecommendationArtifact, ReorderSummaryArtifact, ReorderArtifact, _SupplyOverride
#   - Key APIs: run_reorder_engine, load_reorder_artifact, get_or_create_reorder_artifact, get_reorder_recommendations, get_reorder_recommendation
#   - Dependencies: __future__, csv, json, math, uuid, dataclasses, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import json
import math
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from modules.forecasting.service import get_or_create_batch_forecast_artifact
from modules.stockout_intelligence.service import get_or_create_stockout_artifact

REORDER_MODEL_VERSION = "reorder-engine-v1"
REORDER_ARTIFACT_SUFFIX = "reorder"
DEFAULT_SUPPLIER_MOQ = 1.0
DEFAULT_SERVICE_LEVEL_TARGET = 0.95
DEFAULT_LEAD_TIME_DAYS = 7.0


class ReorderArtifactNotFoundError(FileNotFoundError):
    """Raised when a reorder engine reorder artifact or SKU row cannot be located."""


@dataclass(slots=True)
class ReorderRecommendationArtifact:
    sku: str
    store_code: str
    as_of_date: str
    reorder_date: str
    reorder_quantity: float
    urgency: str
    urgency_score: float
    rationale: str
    current_inventory: float
    inbound_qty: float
    lead_time_days: float
    supplier_moq: float
    service_level_target: float
    demand_forecast_7d: float
    demand_forecast_14d: float
    demand_forecast_30d: float
    avg_daily_demand_7d: float
    stockout_probability: float
    days_to_stockout: float
    expected_lost_sales_estimate: float
    stockout_risk_band: str
    recommended_action: str
    feature_timestamp: str
    model_version: str


@dataclass(slots=True)
class ReorderSummaryArtifact:
    total_skus: int
    urgent_skus: int
    recommended_today: int
    total_reorder_quantity: float
    average_reorder_quantity: float
    average_stockout_probability: float
    output_table: str


@dataclass(slots=True)
class ReorderArtifact:
    reorder_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: ReorderSummaryArtifact
    recommendations: list[ReorderRecommendationArtifact]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class _SupplyOverride:
    supplier_moq: float
    service_level_target: float
    lead_time_days: float


def _to_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_float(value: object, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    text = _to_text(value)
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _normalize_key(value: str) -> str:
    return "_".join(value.strip().lower().replace("/", " ").replace("-", " ").split())


def _canonical_value(row: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        key = _normalize_key(alias)
        if key in row:
            return row[key]
    return ""


def _resolve_uploaded_csv_path(upload_id: str, uploads_dir: Path) -> Path:
    metadata_path = uploads_dir / f"{upload_id}.json"
    if metadata_path.exists():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            stored_path = _to_text(payload.get("stored_path"))
            if stored_path:
                csv_path = Path(stored_path)
                if csv_path.exists():
                    return csv_path
            filename = _to_text(payload.get("filename"))
            if filename:
                candidate = uploads_dir / f"{upload_id}_{filename}"
                if candidate.exists():
                    return candidate

    candidates = sorted(uploads_dir.glob(f"{upload_id}_*.csv"))
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"No uploaded CSV was found for upload_id={upload_id}.")


def _load_supply_overrides(
    upload_id: str, uploads_dir: Path
) -> dict[tuple[str, str], _SupplyOverride]:
    csv_path = _resolve_uploaded_csv_path(upload_id, uploads_dir)
    overrides: dict[tuple[str, str], _SupplyOverride] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for source_row in reader:
            normalized_row = {
                _normalize_key(str(key)): _to_text(value)
                for key, value in source_row.items()
                if key is not None
            }
            sku = _canonical_value(normalized_row, "sku", "product_id", "product sku")
            if not sku:
                continue
            store_code = _canonical_value(normalized_row, "store_code", "store code") or "unknown"
            supplier_moq = _to_float(
                _canonical_value(
                    normalized_row, "supplier_moq", "supplier moq", "moq", "min_order_qty"
                ),
                default=DEFAULT_SUPPLIER_MOQ,
            )
            service_level_target = _to_float(
                _canonical_value(
                    normalized_row,
                    "service_level_target",
                    "service level target",
                    "target_service_level",
                ),
                default=DEFAULT_SERVICE_LEVEL_TARGET,
            )
            lead_time_days = _to_float(
                _canonical_value(normalized_row, "lead_time_days", "lead time days"),
                default=DEFAULT_LEAD_TIME_DAYS,
            )
            key = (sku, store_code)
            overrides[key] = _SupplyOverride(
                supplier_moq=max(supplier_moq, DEFAULT_SUPPLIER_MOQ),
                service_level_target=min(max(service_level_target, 0.8), 0.995),
                lead_time_days=max(lead_time_days, 1.0),
            )
    return overrides


def _forecast_lookup(
    upload_id: str, uploads_dir: Path, artifact_dir: Path, refresh: bool
) -> dict[str, dict[str, Any]]:
    artifact = get_or_create_batch_forecast_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    products = artifact.get("products")
    if not isinstance(products, list):
        return {}
    lookup: dict[str, dict[str, Any]] = {}
    for item in products:
        if not isinstance(item, dict):
            continue
        product_id = _to_text(item.get("product_id"))
        if product_id:
            lookup[product_id] = item
    return lookup


def _stockout_predictions(
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool,
) -> list[dict[str, Any]]:
    artifact = get_or_create_stockout_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    predictions = artifact.get("skus")
    if not isinstance(predictions, list):
        raise ValueError(
            "Stockout intelligence stockout artifact is missing the SKU predictions list."
        )
    return [item for item in predictions if isinstance(item, dict)]


def _forecast_horizon(product: dict[str, Any], horizon_days: int) -> float:
    horizons = product.get("horizons")
    if not isinstance(horizons, list):
        return 0.0
    for item in horizons:
        if not isinstance(item, dict):
            continue
        if int(_to_float(item.get("horizon_days"))) != horizon_days:
            continue
        point_forecast = _to_float(item.get("point_forecast"))
        if point_forecast > 0:
            return round(point_forecast, 2)
        return round(_to_float(item.get("p50")), 2)
    return 0.0


def _ceil_to_multiple(value: float, multiple: float) -> float:
    step = max(multiple, 1.0)
    return round(math.ceil(max(value, 0.0) / step) * step, 2)


def _safe_divide(numerator: float, denominator: float, *, default: float = 0.0) -> float:
    if abs(denominator) < 1e-9:
        return default
    return numerator / denominator


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _urgency(stockout_probability: float, days_to_stockout: float, lead_time_days: float) -> str:
    if stockout_probability >= 0.8 or days_to_stockout <= lead_time_days:
        return "critical"
    if stockout_probability >= 0.6 or days_to_stockout <= lead_time_days + 2.0:
        return "high"
    if stockout_probability >= 0.35 or days_to_stockout <= lead_time_days + 7.0:
        return "medium"
    return "low"


def _urgency_score(
    *,
    stockout_probability: float,
    days_to_stockout: float,
    lead_time_days: float,
    expected_lost_sales_estimate: float,
) -> float:
    lost_sales_pressure = min(expected_lost_sales_estimate / 50.0, 25.0)
    runway_pressure = max(lead_time_days - days_to_stockout, 0.0) * 6.0
    return round(
        _clamp(stockout_probability * 100.0 + runway_pressure + lost_sales_pressure, 0.0, 100.0), 1
    )


def _reorder_date(
    *, as_of_date: date, urgency: str, days_to_stockout: float, lead_time_days: float
) -> date:
    if urgency in {"critical", "high"}:
        return as_of_date
    safety_buffer_days = 2.0 if urgency == "medium" else 0.0
    wait_days = max(days_to_stockout - lead_time_days - safety_buffer_days, 0.0)
    return as_of_date + timedelta(days=min(int(wait_days), 7))


def _rationale(
    *,
    sku: str,
    reorder_quantity: float,
    urgency: str,
    supplier_moq: float,
    demand_forecast_14d: float,
    stockout_probability: float,
    current_inventory: float,
    inbound_qty: float,
    lead_time_days: float,
) -> str:
    if reorder_quantity <= 0:
        return (
            f"{sku} stays below the reorder threshold because current plus inbound stock "
            f"is enough for the next {lead_time_days:.0f} days at the current demand "
            "signal. Continue monitoring."
        )
    return (
        f"{sku} is marked {urgency} because the 14-day forecast is "
        f"{demand_forecast_14d:.1f} units and stockout probability is "
        f"{stockout_probability:.0%}. Current stock plus inbound is "
        f"{current_inventory + inbound_qty:.1f} units, so the engine recommends "
        f"{reorder_quantity:.1f} units using MOQ {supplier_moq:.1f}."
    )


def _build_recommendation(
    *,
    stockout: dict[str, Any],
    forecast: dict[str, Any] | None,
    override: _SupplyOverride | None,
) -> ReorderRecommendationArtifact:
    sku = _to_text(stockout.get("sku"))
    store_code = _to_text(stockout.get("store_code")) or "unknown"
    as_of_date_text = _to_text(stockout.get("as_of_date"))
    as_of_date = datetime.fromisoformat(as_of_date_text).date()

    current_inventory = max(_to_float(stockout.get("available_qty")), 0.0)
    inbound_qty = max(_to_float(stockout.get("inbound_qty")), 0.0)
    stockout_probability = _clamp(_to_float(stockout.get("stockout_probability")), 0.0, 1.0)
    days_to_stockout = _to_float(stockout.get("days_to_stockout"), default=999.0)
    expected_lost_sales_estimate = max(_to_float(stockout.get("expected_lost_sales_estimate")), 0.0)
    avg_daily_demand_7d = max(_to_float(stockout.get("avg_daily_demand_7d")), 0.0)
    risk_band = _to_text(stockout.get("risk_band")) or "low"
    recommended_action = _to_text(stockout.get("recommended_action"))

    lead_time_days = max(
        _to_float(stockout.get("lead_time_days"), default=DEFAULT_LEAD_TIME_DAYS), 1.0
    )
    supplier_moq = DEFAULT_SUPPLIER_MOQ
    service_level_target = DEFAULT_SERVICE_LEVEL_TARGET
    if override is not None:
        supplier_moq = override.supplier_moq
        service_level_target = override.service_level_target
        lead_time_days = override.lead_time_days or lead_time_days

    demand_forecast_7d = 0.0
    demand_forecast_14d = 0.0
    demand_forecast_30d = 0.0
    if forecast is not None:
        demand_forecast_7d = _forecast_horizon(forecast, 7)
        demand_forecast_14d = _forecast_horizon(forecast, 14)
        demand_forecast_30d = _forecast_horizon(forecast, 30)

    if demand_forecast_7d <= 0:
        demand_forecast_7d = round(avg_daily_demand_7d * 7.0, 2)
    if demand_forecast_14d <= 0:
        demand_forecast_14d = round(avg_daily_demand_7d * 14.0, 2)
    if demand_forecast_30d <= 0:
        demand_forecast_30d = round(avg_daily_demand_7d * 30.0, 2)

    forecast_daily_7d = _safe_divide(demand_forecast_7d, 7.0)
    forecast_daily_14d = _safe_divide(demand_forecast_14d, 14.0)
    forecast_daily_30d = _safe_divide(demand_forecast_30d, 30.0)
    reference_daily_demand = max(avg_daily_demand_7d, forecast_daily_7d, forecast_daily_14d, 0.1)

    lead_time_demand = reference_daily_demand * lead_time_days
    review_cycle_demand = reference_daily_demand * 7.0
    trend_buffer = max(forecast_daily_30d - reference_daily_demand, 0.0) * 7.0
    service_buffer = lead_time_demand * max(service_level_target - 0.85, 0.05)
    risk_buffer = lead_time_demand * stockout_probability * 0.5
    target_stock_position = (
        lead_time_demand + review_cycle_demand + trend_buffer + service_buffer + risk_buffer
    )

    net_supply = current_inventory + inbound_qty
    raw_reorder_quantity = max(target_stock_position - net_supply, 0.0)
    reorder_quantity = (
        _ceil_to_multiple(raw_reorder_quantity, supplier_moq) if raw_reorder_quantity > 0 else 0.0
    )

    urgency = _urgency(stockout_probability, days_to_stockout, lead_time_days)
    urgency_score = _urgency_score(
        stockout_probability=stockout_probability,
        days_to_stockout=days_to_stockout,
        lead_time_days=lead_time_days,
        expected_lost_sales_estimate=expected_lost_sales_estimate,
    )
    reorder_date = _reorder_date(
        as_of_date=as_of_date,
        urgency=urgency,
        days_to_stockout=days_to_stockout,
        lead_time_days=lead_time_days,
    )
    feature_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    rationale = _rationale(
        sku=sku,
        reorder_quantity=reorder_quantity,
        urgency=urgency,
        supplier_moq=supplier_moq,
        demand_forecast_14d=demand_forecast_14d,
        stockout_probability=stockout_probability,
        current_inventory=current_inventory,
        inbound_qty=inbound_qty,
        lead_time_days=lead_time_days,
    )

    return ReorderRecommendationArtifact(
        sku=sku,
        store_code=store_code,
        as_of_date=as_of_date.isoformat(),
        reorder_date=reorder_date.isoformat(),
        reorder_quantity=reorder_quantity,
        urgency=urgency,
        urgency_score=urgency_score,
        rationale=rationale,
        current_inventory=round(current_inventory, 2),
        inbound_qty=round(inbound_qty, 2),
        lead_time_days=round(lead_time_days, 2),
        supplier_moq=round(max(supplier_moq, DEFAULT_SUPPLIER_MOQ), 2),
        service_level_target=round(_clamp(service_level_target, 0.8, 0.995), 3),
        demand_forecast_7d=round(demand_forecast_7d, 2),
        demand_forecast_14d=round(demand_forecast_14d, 2),
        demand_forecast_30d=round(demand_forecast_30d, 2),
        avg_daily_demand_7d=round(avg_daily_demand_7d, 4),
        stockout_probability=round(stockout_probability, 4),
        days_to_stockout=round(days_to_stockout, 2),
        expected_lost_sales_estimate=round(expected_lost_sales_estimate, 2),
        stockout_risk_band=risk_band,
        recommended_action=recommended_action,
        feature_timestamp=feature_timestamp,
        model_version=REORDER_MODEL_VERSION,
    )


def _build_summary(recommendations: list[ReorderRecommendationArtifact]) -> ReorderSummaryArtifact:
    total_quantity = round(sum(item.reorder_quantity for item in recommendations), 2)
    average_quantity = round(total_quantity / len(recommendations), 2) if recommendations else 0.0
    average_probability = (
        round(
            sum(item.stockout_probability for item in recommendations) / len(recommendations),
            4,
        )
        if recommendations
        else 0.0
    )
    return ReorderSummaryArtifact(
        total_skus=len(recommendations),
        urgent_skus=sum(1 for item in recommendations if item.urgency in {"critical", "high"}),
        recommended_today=sum(
            1
            for item in recommendations
            if item.reorder_date == item.as_of_date and item.reorder_quantity > 0
        ),
        total_reorder_quantity=total_quantity,
        average_reorder_quantity=average_quantity,
        average_stockout_probability=average_probability,
        output_table="predictions.reorder_recommendations",
    )


def run_reorder_engine(
    *,
    upload_id: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    stockout_artifact_dir: Path,
    artifact_dir: Path,
    refresh_forecast: bool = False,
    refresh_stockout: bool = False,
) -> ReorderArtifact:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    forecast_lookup = _forecast_lookup(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=forecast_artifact_dir,
        refresh=refresh_forecast,
    )
    stockout_predictions = _stockout_predictions(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=stockout_artifact_dir,
        refresh=refresh_stockout,
    )
    overrides = _load_supply_overrides(upload_id, uploads_dir)

    recommendations: list[ReorderRecommendationArtifact] = []
    for stockout in stockout_predictions:
        sku = _to_text(stockout.get("sku"))
        store_code = _to_text(stockout.get("store_code")) or "unknown"
        recommendation = _build_recommendation(
            stockout=stockout,
            forecast=forecast_lookup.get(sku),
            override=overrides.get((sku, store_code)) or overrides.get((sku, "unknown")),
        )
        recommendations.append(recommendation)

    recommendations.sort(
        key=lambda item: (item.urgency_score, item.stockout_probability, item.reorder_quantity),
        reverse=True,
    )
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    reorder_run_id = f"reo13_{uuid.uuid4().hex[:12]}"
    artifact_path = artifact_dir / f"{upload_id}_{REORDER_ARTIFACT_SUFFIX}_{reorder_run_id}.json"
    artifact = ReorderArtifact(
        reorder_run_id=reorder_run_id,
        upload_id=upload_id,
        generated_at=generated_at,
        model_version=REORDER_MODEL_VERSION,
        summary=_build_summary(recommendations),
        recommendations=recommendations,
        artifact_path=str(artifact_path),
    )
    artifact_path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return artifact


def _load_json_artifact(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Artifact file is invalid: {path}")
    return payload


def load_reorder_artifact(*, upload_id: str, artifact_dir: Path) -> dict[str, Any]:
    pattern = f"{upload_id}_{REORDER_ARTIFACT_SUFFIX}_*.json"
    matches = sorted(
        artifact_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True
    )
    if not matches:
        raise ReorderArtifactNotFoundError(
            f"No reorder engine reorder artifact exists for upload_id={upload_id}."
        )
    return _load_json_artifact(matches[0])


def get_or_create_reorder_artifact(
    *,
    upload_id: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    stockout_artifact_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    if not refresh:
        try:
            return load_reorder_artifact(upload_id=upload_id, artifact_dir=artifact_dir)
        except ReorderArtifactNotFoundError:
            pass
    artifact = run_reorder_engine(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=artifact_dir,
        refresh_forecast=refresh,
        refresh_stockout=refresh,
    )
    return artifact.to_dict()


def get_reorder_recommendations(
    *,
    upload_id: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    stockout_artifact_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
    store_code: str | None = None,
    urgency: str | None = None,
) -> dict[str, Any]:
    artifact = get_or_create_reorder_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    recommendations = artifact.get("recommendations") or []
    if store_code:
        recommendations = [item for item in recommendations if item.get("store_code") == store_code]
    if urgency:
        normalized_urgency = urgency.strip().lower()
        recommendations = [
            item
            for item in recommendations
            if _to_text(item.get("urgency")).lower() == normalized_urgency
        ]
    payload = dict(artifact)
    payload["recommendations"] = recommendations[:limit]
    return payload


def get_reorder_recommendation(
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
    recommendations = payload.get("recommendations") or []
    normalized_sku = sku.strip().lower()
    matches = [
        item for item in recommendations if _to_text(item.get("sku")).lower() == normalized_sku
    ]
    if not matches:
        raise ReorderArtifactNotFoundError(
            f"No reorder recommendation exists for sku={sku} and upload_id={upload_id}."
        )
    return matches[0]
