# Project:      RetailOps Data & AI Platform
# Module:       modules.stockout_intelligence
# File:         service.py
# Path:         modules/stockout_intelligence/service.py
#
# Summary:      Implements the stockout intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for stockout intelligence workflows.
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
#   - Main types: StockoutArtifactNotFoundError, StockoutObservationRow, StockoutSkuPredictionArtifact, StockoutRiskSummaryArtifact, StockoutRiskArtifact, _ResolvedUpload, ...
#   - Key APIs: run_stockout_risk_analysis, load_stockout_artifact, get_or_create_stockout_artifact, get_stockout_sku_predictions, get_stockout_sku_prediction
#   - Dependencies: __future__, csv, json, uuid, dataclasses, datetime, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

STOCKOUT_MODEL_VERSION = "stockout-intelligence-v1"
STOCKOUT_ARTIFACT_SUFFIX = "stockout"
DEFAULT_LEAD_TIME_DAYS = 7.0


class StockoutArtifactNotFoundError(FileNotFoundError):
    """Raised when a stockout intelligence stockout artifact or SKU row cannot be located."""


@dataclass(slots=True)
class StockoutObservationRow:
    observation_date: date
    sku: str
    store_code: str
    quantity: float
    unit_price: float
    available_qty: float
    inbound_qty: float
    lead_time_days: float


@dataclass(slots=True)
class StockoutSkuPredictionArtifact:
    sku: str
    store_code: str
    as_of_date: str
    available_qty: float
    inbound_qty: float
    avg_daily_demand_7d: float
    avg_daily_demand_28d: float
    demand_trend_ratio: float
    days_to_stockout: float
    lead_time_days: float
    stockout_probability: float
    reorder_urgency_score: float
    expected_lost_sales_estimate: float
    risk_band: str
    recommended_action: str
    feature_timestamp: str
    model_version: str
    explanation_summary: str


@dataclass(slots=True)
class StockoutRiskSummaryArtifact:
    total_skus: int
    at_risk_skus: int
    critical_skus: int
    average_days_to_stockout: float
    average_stockout_probability: float
    predictions_table: str


@dataclass(slots=True)
class StockoutRiskArtifact:
    stockout_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: StockoutRiskSummaryArtifact
    skus: list[StockoutSkuPredictionArtifact]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class _ResolvedUpload:
    upload_id: str
    csv_path: Path


@dataclass(slots=True)
class _SkuDemandSeries:
    sku: str
    store_code: str
    anchor_date: date
    daily_quantities: dict[date, float]
    recent_inventory_history: list[tuple[date, float]]
    available_qty: float
    inbound_qty: float
    unit_price: float
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


def _parse_date(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%d.%m.%Y",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def _resolve_upload_id(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    value = kwargs.get("upload_id")
    if value is None:
        for candidate in args:
            if isinstance(candidate, str) and candidate:
                value = candidate
                break
    text = _to_text(value)
    if not text:
        raise ValueError("upload_id is required for the stockout module.")
    return text


def _resolve_path(value: Any, *, default: str) -> Path:
    if value is None:
        return Path(default)
    return Path(str(value))


def _is_order_csv(csv_path: Path) -> bool:
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader, [])
    except OSError:
        return False
    normalized_headers = {_normalize_key(header) for header in headers}
    required = {"order_date", "sku", "quantity"}
    return required.issubset(normalized_headers)


def _resolve_upload(upload_id: str, uploads_dir: Path) -> _ResolvedUpload:
    metadata_path = uploads_dir / f"{upload_id}.json"
    if metadata_path.exists():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        stored_path = _to_text(payload.get("stored_path"))
        if stored_path:
            csv_path = Path(stored_path)
            if csv_path.exists() and _is_order_csv(csv_path):
                return _ResolvedUpload(upload_id=upload_id, csv_path=csv_path)

    candidates = sorted(uploads_dir.glob(f"{upload_id}_*.csv"))
    for candidate in candidates:
        if _is_order_csv(candidate):
            return _ResolvedUpload(upload_id=upload_id, csv_path=candidate)

    raise FileNotFoundError(
        "No order CSV was found for this upload_id. Expected metadata stored_path or an "
        "uploads file such as '<upload_id>_orders.csv'."
    )


def _load_observation_rows(upload_id: str, uploads_dir: Path) -> list[StockoutObservationRow]:
    resolved = _resolve_upload(upload_id, uploads_dir)
    rows: list[StockoutObservationRow] = []
    with resolved.csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for source_row in reader:
            normalized_row = {
                _normalize_key(str(key)): _to_text(value)
                for key, value in source_row.items()
                if key is not None
            }
            observation_date = _parse_date(
                _canonical_value(normalized_row, "order_date", "order date", "snapshot_date")
            )
            sku = _canonical_value(normalized_row, "sku", "product sku")
            if observation_date is None or not sku:
                continue
            store_code = _canonical_value(normalized_row, "store_code", "store code") or "unknown"
            quantity = _to_float(
                _canonical_value(normalized_row, "quantity", "units", "units_sold", "units sold"),
                default=0.0,
            )
            available_qty = _to_float(
                _canonical_value(
                    normalized_row,
                    "available_qty",
                    "available qty",
                    "on_hand_qty",
                    "on hand qty",
                ),
                default=0.0,
            )
            inbound_qty = _to_float(
                _canonical_value(
                    normalized_row,
                    "in_transit_qty",
                    "in transit qty",
                    "inbound_qty",
                    "inbound qty",
                ),
                default=0.0,
            )
            lead_time_days = _to_float(
                _canonical_value(normalized_row, "lead_time_days", "lead time days"),
                default=DEFAULT_LEAD_TIME_DAYS,
            )
            unit_price = _to_float(
                _canonical_value(normalized_row, "unit_price", "unit price"),
                default=0.0,
            )
            rows.append(
                StockoutObservationRow(
                    observation_date=observation_date,
                    sku=sku,
                    store_code=store_code,
                    quantity=max(quantity, 0.0),
                    unit_price=max(unit_price, 0.0),
                    available_qty=max(available_qty, 0.0),
                    inbound_qty=max(inbound_qty, 0.0),
                    lead_time_days=max(lead_time_days, 1.0),
                )
            )
    if not rows:
        raise ValueError("No usable stockout rows were found in the uploaded CSV.")
    return rows


def _fallback_inventory(daily_quantities: dict[date, float]) -> float:
    latest_demands = list(daily_quantities.values())[-7:]
    if not latest_demands:
        return 0.0
    average_recent = sum(latest_demands) / len(latest_demands)
    return round(max(average_recent * 7.0, 1.0), 2)


def _build_sku_series(upload_id: str, uploads_dir: Path) -> list[_SkuDemandSeries]:
    rows = _load_observation_rows(upload_id, uploads_dir)
    grouped: dict[tuple[str, str], list[StockoutObservationRow]] = {}
    for row in rows:
        grouped.setdefault((row.sku, row.store_code), []).append(row)

    series_list: list[_SkuDemandSeries] = []
    for (sku, store_code), group in grouped.items():
        ordered_group = sorted(group, key=lambda item: item.observation_date)
        anchor_date = ordered_group[-1].observation_date
        daily_quantities: dict[date, float] = {}
        recent_inventory_history: list[tuple[date, float]] = []
        available_qty = 0.0
        inbound_qty = 0.0
        unit_price = 0.0
        lead_time_days = DEFAULT_LEAD_TIME_DAYS

        for item in ordered_group:
            daily_quantities[item.observation_date] = (
                daily_quantities.get(item.observation_date, 0.0) + item.quantity
            )
            if item.available_qty > 0:
                available_qty = item.available_qty
            if item.inbound_qty >= 0:
                inbound_qty = item.inbound_qty
            if item.unit_price > 0:
                unit_price = item.unit_price
            if item.lead_time_days > 0:
                lead_time_days = item.lead_time_days
            recent_inventory_history.append((item.observation_date, item.available_qty))

        if available_qty <= 0:
            available_qty = _fallback_inventory(daily_quantities)

        series_list.append(
            _SkuDemandSeries(
                sku=sku,
                store_code=store_code,
                anchor_date=anchor_date,
                daily_quantities=daily_quantities,
                recent_inventory_history=recent_inventory_history[-14:],
                available_qty=round(available_qty, 2),
                inbound_qty=round(inbound_qty, 2),
                unit_price=round(unit_price, 2),
                lead_time_days=round(max(lead_time_days, 1.0), 2),
            )
        )

    if not series_list:
        raise ValueError("No stockout-ready SKU history was found in the uploaded CSV.")
    return series_list


def _rolling_average(daily_quantities: dict[date, float], *, anchor_date: date, days: int) -> float:
    values = [
        daily_quantities.get(anchor_date - timedelta(days=offset), 0.0) for offset in range(days)
    ]
    return round(sum(values) / max(days, 1), 4)


def _safe_divide(numerator: float, denominator: float, *, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _risk_band(probability: float) -> str:
    if probability >= 0.8:
        return "critical"
    if probability >= 0.6:
        return "high"
    if probability >= 0.35:
        return "medium"
    return "low"


def _recommended_action(risk_band: str) -> str:
    if risk_band == "critical":
        return "Create a reorder today and escalate the supplier ETA."
    if risk_band == "high":
        return "Place a reorder within 24 hours and watch inbound stock closely."
    if risk_band == "medium":
        return "Plan the reorder this week and review demand acceleration."
    return "No urgent reorder is needed. Continue daily monitoring."


def _recent_stockout_days(history: list[tuple[date, float]], *, anchor_date: date) -> int:
    floor_date = anchor_date - timedelta(days=13)
    return sum(
        1
        for observed_date, available_qty in history
        if observed_date >= floor_date and available_qty <= 0
    )


def _build_prediction(series: _SkuDemandSeries) -> StockoutSkuPredictionArtifact:
    avg_daily_demand_7d = _rolling_average(
        series.daily_quantities, anchor_date=series.anchor_date, days=7
    )
    avg_daily_demand_28d = _rolling_average(
        series.daily_quantities, anchor_date=series.anchor_date, days=28
    )
    if avg_daily_demand_28d <= 0:
        demand_trend_ratio = 1.0 if avg_daily_demand_7d > 0 else 0.0
    else:
        demand_trend_ratio = round(avg_daily_demand_7d / avg_daily_demand_28d, 4)

    if avg_daily_demand_7d <= 0:
        days_to_stockout = 999.0
    else:
        days_to_stockout = round(series.available_qty / avg_daily_demand_7d, 2)

    recent_stockout_days_14d = _recent_stockout_days(
        series.recent_inventory_history,
        anchor_date=series.anchor_date,
    )
    demand_during_lead_time = avg_daily_demand_7d * series.lead_time_days
    inbound_coverage_ratio = _safe_divide(
        series.inbound_qty,
        max(demand_during_lead_time, 1.0),
        default=0.0,
    )
    lead_time_pressure = _clamp(
        _safe_divide(
            series.lead_time_days - days_to_stockout, max(series.lead_time_days, 1.0), default=0.0
        ),
        0.0,
        1.0,
    )
    buffer_cover_days = _safe_divide(
        series.available_qty + series.inbound_qty,
        max(avg_daily_demand_7d, 0.1),
        default=999.0,
    )
    buffer_pressure = _clamp((7.0 - buffer_cover_days) / 7.0, 0.0, 1.0)
    trend_pressure = _clamp(demand_trend_ratio - 1.0, 0.0, 1.0)
    history_pressure = _clamp(recent_stockout_days_14d / 4.0, 0.0, 1.0)
    inbound_relief = _clamp(inbound_coverage_ratio, 0.0, 1.0)

    base_probability = 0.05 if avg_daily_demand_7d > 0 else 0.02
    if series.available_qty <= 0:
        base_probability = 0.85

    stockout_probability = round(
        _clamp(
            base_probability
            + 0.5 * lead_time_pressure
            + 0.2 * buffer_pressure
            + 0.15 * trend_pressure
            + 0.1 * history_pressure
            - 0.1 * inbound_relief,
            0.01,
            0.99,
        ),
        4,
    )
    expected_inventory_gap = max(
        demand_during_lead_time - (series.available_qty + series.inbound_qty), 0.0
    )
    expected_lost_sales_estimate = round(expected_inventory_gap * max(series.unit_price, 0.0), 2)
    reorder_urgency_score = round(
        _clamp(
            stockout_probability * 100.0 + max(0.0, series.lead_time_days - days_to_stockout) * 5.0,
            0.0,
            100.0,
        ),
        1,
    )
    risk_band = _risk_band(stockout_probability)
    feature_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    explanation_summary = (
        f"{series.sku} has {days_to_stockout} cover days versus a "
        f"{series.lead_time_days}-day lead time. "
        f"Recent daily demand is {avg_daily_demand_7d} and the trend ratio is "
        f"{demand_trend_ratio}."
    )
    return StockoutSkuPredictionArtifact(
        sku=series.sku,
        store_code=series.store_code,
        as_of_date=series.anchor_date.isoformat(),
        available_qty=series.available_qty,
        inbound_qty=series.inbound_qty,
        avg_daily_demand_7d=avg_daily_demand_7d,
        avg_daily_demand_28d=avg_daily_demand_28d,
        demand_trend_ratio=round(demand_trend_ratio, 4),
        days_to_stockout=days_to_stockout,
        lead_time_days=series.lead_time_days,
        stockout_probability=stockout_probability,
        reorder_urgency_score=reorder_urgency_score,
        expected_lost_sales_estimate=expected_lost_sales_estimate,
        risk_band=risk_band,
        recommended_action=_recommended_action(risk_band),
        feature_timestamp=feature_timestamp,
        model_version=STOCKOUT_MODEL_VERSION,
        explanation_summary=explanation_summary,
    )


def _build_summary(predictions: list[StockoutSkuPredictionArtifact]) -> StockoutRiskSummaryArtifact:
    eligible_days = [item.days_to_stockout for item in predictions if item.days_to_stockout < 999]
    average_days_to_stockout = (
        round(
            sum(eligible_days) / len(eligible_days),
            2,
        )
        if eligible_days
        else 999.0
    )
    average_stockout_probability = round(
        sum(item.stockout_probability for item in predictions) / max(len(predictions), 1),
        4,
    )
    return StockoutRiskSummaryArtifact(
        total_skus=len(predictions),
        at_risk_skus=sum(
            1 for item in predictions if item.risk_band in {"medium", "high", "critical"}
        ),
        critical_skus=sum(1 for item in predictions if item.risk_band == "critical"),
        average_days_to_stockout=average_days_to_stockout,
        average_stockout_probability=average_stockout_probability,
        predictions_table="predictions.stockout_risk_daily",
    )


def run_stockout_risk_analysis(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
) -> StockoutRiskArtifact:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    sku_series = _build_sku_series(upload_id=upload_id, uploads_dir=uploads_dir)
    predictions = [_build_prediction(series) for series in sku_series]
    predictions.sort(
        key=lambda item: (
            item.reorder_urgency_score,
            item.stockout_probability,
            item.expected_lost_sales_estimate,
        ),
        reverse=True,
    )
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    stockout_run_id = f"stk12_{uuid.uuid4().hex[:12]}"
    artifact_path = artifact_dir / f"{upload_id}_{STOCKOUT_ARTIFACT_SUFFIX}_{stockout_run_id}.json"
    artifact = StockoutRiskArtifact(
        stockout_run_id=stockout_run_id,
        upload_id=upload_id,
        generated_at=generated_at,
        model_version=STOCKOUT_MODEL_VERSION,
        summary=_build_summary(predictions),
        skus=predictions,
        artifact_path=str(artifact_path),
    )
    artifact_path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return artifact


def _load_json_artifact(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Artifact file is invalid: {path}")
    return payload


def load_stockout_artifact(*, upload_id: str, artifact_dir: Path) -> dict[str, Any]:
    pattern = f"{upload_id}_{STOCKOUT_ARTIFACT_SUFFIX}_*.json"
    matches = sorted(
        artifact_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True
    )
    if not matches:
        raise StockoutArtifactNotFoundError(
            f"No stockout intelligence stockout artifact exists for upload_id={upload_id}."
        )
    return _load_json_artifact(matches[0])


def get_or_create_stockout_artifact(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    if not refresh:
        try:
            return load_stockout_artifact(upload_id=upload_id, artifact_dir=artifact_dir)
        except StockoutArtifactNotFoundError:
            pass
    artifact = run_stockout_risk_analysis(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )
    return artifact.to_dict()


def get_stockout_sku_predictions(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 50,
    store_code: str | None = None,
) -> dict[str, Any]:
    artifact = get_or_create_stockout_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    predictions = artifact.get("skus") or []
    if store_code:
        predictions = [item for item in predictions if item.get("store_code") == store_code]
    payload = dict(artifact)
    payload["skus"] = predictions[:limit]
    return payload


def get_stockout_sku_prediction(
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
    predictions = payload.get("skus") or []
    matches = [item for item in predictions if item.get("sku") == sku]
    if not matches:
        raise StockoutArtifactNotFoundError(
            f"No stockout prediction exists for sku={sku} and upload_id={upload_id}."
        )
    return matches[0]
