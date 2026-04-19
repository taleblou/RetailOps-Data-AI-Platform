# Project:      RetailOps Data & AI Platform
# Module:       core.monitoring
# File:         service.py
# Path:         core/monitoring/service.py
#
# Summary:      Implements the monitoring service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for monitoring workflows.
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
#   - Main types: MonitoringArtifactNotFoundError, MonitoringCheckArtifact, MonitoringAlertArtifact, MonitoringDashboardMetricArtifact, MonitoringOverrideEntryArtifact, MonitoringOverrideSummaryArtifact, ...
#   - Key APIs: log_manual_override, get_override_summary, run_monitoring, get_or_create_monitoring_artifact
#   - Dependencies: __future__, csv, json, uuid, collections, dataclasses, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import json
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from core.serving.service import get_or_create_batch_serving_artifact
from modules.forecasting.service import get_or_create_batch_forecast_artifact
from modules.ml_registry.service import run_model_registry
from modules.shipment_risk.service import get_or_create_shipment_risk_artifact
from modules.stockout_intelligence.service import get_or_create_stockout_artifact

MONITORING_ARTIFACT_SUFFIX = "monitoring_summary"
OVERRIDE_FILE_SUFFIX = "monitoring_overrides"


class MonitoringArtifactNotFoundError(FileNotFoundError):
    """Raised when a monitoring artifact or override file cannot be found."""


@dataclass(slots=True)
class MonitoringCheckArtifact:
    check_name: str
    category: str
    status: str
    metric_name: str
    metric_value: float
    threshold_value: float
    message: str
    recommended_action: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class MonitoringAlertArtifact:
    alert_id: str
    severity: str
    category: str
    check_name: str
    message: str
    recommended_action: str
    retrain_recommended: bool
    disable_prediction_recommended: bool


@dataclass(slots=True)
class MonitoringDashboardMetricArtifact:
    metric_name: str
    value: float
    unit: str
    status: str
    description: str


@dataclass(slots=True)
class MonitoringOverrideEntryArtifact:
    override_id: str
    upload_id: str
    prediction_type: str
    entity_id: str
    original_decision: dict[str, Any]
    override_decision: dict[str, Any]
    reason: str
    feedback_label: str | None
    user_id: str | None
    retraining_feedback_kept: bool
    created_at: str


@dataclass(slots=True)
class MonitoringOverrideSummaryArtifact:
    upload_id: str
    total_overrides: int
    by_prediction_type: dict[str, int]
    last_override_at: str | None
    entries: list[MonitoringOverrideEntryArtifact]


@dataclass(slots=True)
class MonitoringSummaryArtifact:
    source_row_count: int
    source_file_count: int
    total_alerts: int
    warning_alerts: int
    critical_alerts: int
    retrain_recommended: bool
    disable_prediction_recommended: bool
    model_usage_total: int
    model_coverage: float
    abstention_rate: float
    api_latency_ms: float


@dataclass(slots=True)
class MonitoringArtifact:
    monitoring_run_id: str
    upload_id: str
    generated_at: str
    summary: MonitoringSummaryArtifact
    data_checks: list[MonitoringCheckArtifact]
    ml_checks: list[MonitoringCheckArtifact]
    alerts: list[MonitoringAlertArtifact]
    dashboard_metrics: list[MonitoringDashboardMetricArtifact]
    override_summary: MonitoringOverrideSummaryArtifact
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class _UploadStats:
    row_count: int
    file_count: int
    null_rate: float
    out_of_range_rate: float
    latest_event_date: str | None
    freshness_days: float
    unique_skus: set[str]
    unique_products: set[str]
    unique_shipments: set[str]
    checked_columns: list[str]


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_key(value: str) -> str:
    return "_".join(value.strip().lower().replace("/", " ").replace("-", " ").split())


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


def _save_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Artifact file is invalid: {path}")
    return payload


def _latest_artifact_path(upload_id: str, artifact_dir: Path) -> Path | None:
    pattern = f"{upload_id}_{MONITORING_ARTIFACT_SUFFIX}_*.json"
    matches = sorted(
        artifact_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True
    )
    if matches:
        return matches[0]
    return None


def _previous_artifact_path(upload_id: str, artifact_dir: Path) -> Path | None:
    pattern = f"{upload_id}_{MONITORING_ARTIFACT_SUFFIX}_*.json"
    matches = sorted(
        artifact_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True
    )
    if len(matches) >= 2:
        return matches[1]
    return None


def _resolve_upload_files(upload_id: str, uploads_dir: Path) -> list[Path]:
    matches = sorted(uploads_dir.glob(f"{upload_id}_*.csv"))
    if matches:
        return matches
    raise FileNotFoundError(
        f"No upload files were found for upload_id '{upload_id}'. Expected files like "
        f"'{upload_id}_orders.csv' or '{upload_id}_shipments.csv'."
    )


def _collect_upload_stats(upload_id: str, uploads_dir: Path) -> _UploadStats:
    upload_files = _resolve_upload_files(upload_id, uploads_dir)
    required_candidates = {
        "order_date",
        "sku",
        "product_id",
        "quantity",
        "unit_price",
        "shipment_id",
        "promised_date",
        "actual_delivery_date",
        "available_qty",
        "lead_time_days",
    }
    date_candidates = {
        "order_date",
        "forecast_date",
        "promised_date",
        "actual_delivery_date",
        "snapshot_date",
        "event_date",
    }
    numeric_bounds = {
        "quantity": (0.0, 50000.0),
        "unit_price": (0.0, 100000.0),
        "available_qty": (0.0, 50000.0),
        "lead_time_days": (0.0, 365.0),
        "inventory_lag_days": (0.0, 365.0),
        "overdue_days": (-30.0, 365.0),
    }
    row_count = 0
    null_count = 0
    null_total = 0
    out_of_range_count = 0
    out_of_range_total = 0
    latest_date: date | None = None
    unique_skus: set[str] = set()
    unique_products: set[str] = set()
    unique_shipments: set[str] = set()
    checked_columns: set[str] = set()

    for csv_path in upload_files:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw_row in reader:
                normalized_row = {
                    _normalize_key(str(key)): (str(value).strip() if value is not None else "")
                    for key, value in raw_row.items()
                }
                row_count += 1
                for column_name in required_candidates:
                    if column_name in normalized_row:
                        checked_columns.add(column_name)
                        null_total += 1
                        if not normalized_row[column_name]:
                            null_count += 1
                for column_name, (lower, upper) in numeric_bounds.items():
                    if column_name not in normalized_row or not normalized_row[column_name]:
                        continue
                    out_of_range_total += 1
                    value = _safe_float(normalized_row[column_name])
                    if value < lower or value > upper:
                        out_of_range_count += 1
                for column_name in date_candidates:
                    if column_name not in normalized_row or not normalized_row[column_name]:
                        continue
                    parsed = _parse_date(normalized_row[column_name])
                    if parsed is not None and (latest_date is None or parsed > latest_date):
                        latest_date = parsed
                sku = normalized_row.get("sku", "")
                if sku:
                    unique_skus.add(sku)
                product_id = normalized_row.get("product_id", "")
                if product_id:
                    unique_products.add(product_id)
                shipment_id = normalized_row.get("shipment_id", "")
                if shipment_id:
                    unique_shipments.add(shipment_id)

    null_rate = (null_count / null_total) if null_total else 0.0
    out_of_range_rate = (out_of_range_count / out_of_range_total) if out_of_range_total else 0.0
    freshness_days = 999.0
    latest_event_date_text: str | None = None
    if latest_date is not None:
        freshness_days = float((datetime.now(UTC).date() - latest_date).days)
        latest_event_date_text = latest_date.isoformat()

    return _UploadStats(
        row_count=row_count,
        file_count=len(upload_files),
        null_rate=round(null_rate, 4),
        out_of_range_rate=round(out_of_range_rate, 4),
        latest_event_date=latest_event_date_text,
        freshness_days=round(freshness_days, 2),
        unique_skus=unique_skus,
        unique_products=unique_products,
        unique_shipments=unique_shipments,
        checked_columns=sorted(checked_columns),
    )


def _check_status(*, value: float, warn_threshold: float, critical_threshold: float) -> str:
    if value >= critical_threshold:
        return "critical"
    if value >= warn_threshold:
        return "warn"
    return "pass"


def _inverse_check_status(*, value: float, warn_threshold: float, critical_threshold: float) -> str:
    if value <= critical_threshold:
        return "critical"
    if value <= warn_threshold:
        return "warn"
    return "pass"


def _build_data_checks(
    *,
    upload_stats: _UploadStats,
    previous_payload: dict[str, Any] | None,
) -> list[MonitoringCheckArtifact]:
    checks: list[MonitoringCheckArtifact] = []
    row_count_threshold = 10.0
    if previous_payload is not None:
        previous_summary = previous_payload.get("summary") or {}
        previous_row_count = _safe_float(previous_summary.get("source_row_count"), default=0.0)
        if previous_row_count > 0:
            row_count_delta = abs(upload_stats.row_count - previous_row_count) / previous_row_count
        else:
            row_count_delta = 0.0
        row_count_status = _check_status(
            value=row_count_delta,
            warn_threshold=0.25,
            critical_threshold=0.50,
        )
        row_count_threshold = 0.25
        row_count_message = (
            "Row count changed versus the previous monitoring run. "
            f"Current rows: {upload_stats.row_count}. Previous rows: {int(previous_row_count)}."
        )
        row_count_metric = round(row_count_delta, 4)
    else:
        row_count_metric = float(upload_stats.row_count)
        row_count_status = _inverse_check_status(
            value=float(upload_stats.row_count),
            warn_threshold=10.0,
            critical_threshold=5.0,
        )
        row_count_message = (
            "Starter row-count check used the minimum viable threshold because no earlier "
            "monitoring baseline exists yet."
        )
    checks.append(
        MonitoringCheckArtifact(
            check_name="row_count_anomaly",
            category="data_quality",
            status=row_count_status,
            metric_name="row_count_signal",
            metric_value=row_count_metric,
            threshold_value=row_count_threshold,
            message=row_count_message,
            recommended_action=(
                "Investigate the source extract and rerun ingestion "
                "if the row-count change was unexpected."
            ),
            metadata={
                "source_row_count": upload_stats.row_count,
                "source_file_count": upload_stats.file_count,
            },
        )
    )
    checks.append(
        MonitoringCheckArtifact(
            check_name="null_spikes",
            category="data_quality",
            status=_check_status(
                value=upload_stats.null_rate,
                warn_threshold=0.05,
                critical_threshold=0.15,
            ),
            metric_name="null_rate",
            metric_value=upload_stats.null_rate,
            threshold_value=0.05,
            message=(
                "Required retail columns were scanned for missing values across the current upload."
            ),
            recommended_action=(
                "Inspect mapping rules or source exports when "
                "null spikes appear in required columns."
            ),
            metadata={"checked_columns": upload_stats.checked_columns},
        )
    )
    checks.append(
        MonitoringCheckArtifact(
            check_name="out_of_range_values",
            category="data_quality",
            status=_check_status(
                value=upload_stats.out_of_range_rate,
                warn_threshold=0.01,
                critical_threshold=0.05,
            ),
            metric_name="out_of_range_rate",
            metric_value=upload_stats.out_of_range_rate,
            threshold_value=0.01,
            message=(
                "Numeric operational fields were checked for "
                "impossible negatives and unrealistic highs."
            ),
            recommended_action=(
                "Correct source data or canonical mapping for quantities, prices, and lead times."
            ),
            metadata={},
        )
    )
    freshness_status = "warn"
    if upload_stats.latest_event_date is None:
        freshness_status = "warn"
    else:
        freshness_status = _check_status(
            value=upload_stats.freshness_days,
            warn_threshold=7.0,
            critical_threshold=14.0,
        )
    checks.append(
        MonitoringCheckArtifact(
            check_name="freshness",
            category="data_quality",
            status=freshness_status,
            metric_name="freshness_days",
            metric_value=upload_stats.freshness_days,
            threshold_value=7.0,
            message=("Freshness uses the newest business date found in the uploaded source files."),
            recommended_action=(
                "Refresh the source sync or delay prediction-based actions until fresh data lands."
            ),
            metadata={"latest_event_date": upload_stats.latest_event_date},
        )
    )
    return checks


def _load_registry_details(registry_artifact_dir: Path, refresh: bool) -> list[dict[str, Any]]:
    registry_payload = run_model_registry(
        artifact_dir=registry_artifact_dir,
        refresh=refresh,
    ).to_dict()
    return list(registry_payload.get("registry_details") or [])


def _build_ml_checks(
    *,
    registry_details: list[dict[str, Any]],
    forecast_artifact: dict[str, Any],
    shipment_artifact: dict[str, Any],
    stockout_artifact: dict[str, Any],
) -> list[MonitoringCheckArtifact]:
    checks: list[MonitoringCheckArtifact] = []
    champion_versions: list[dict[str, Any]] = []
    for registry in registry_details:
        aliases = registry.get("aliases") or {}
        champion_version = str(aliases.get("champion", ""))
        versions = registry.get("versions") or []
        for version in versions:
            if str(version.get("model_version", "")) == champion_version:
                champion_versions.append(version)
                break

    if champion_versions:
        drift_scores = [_safe_float(item.get("drift_score")) for item in champion_versions]
        feature_drift = round(sum(drift_scores) / len(drift_scores), 4)
        calibration_errors = [
            _safe_float(item.get("calibration_error")) for item in champion_versions
        ]
        calibration_drift = round(max(calibration_errors), 4)
        passed_count = sum(
            1 for item in champion_versions if bool(item.get("evaluation_passed", False))
        )
        lag_aware_performance = round(passed_count / len(champion_versions), 4)
    else:
        feature_drift = 0.0
        calibration_drift = 0.0
        lag_aware_performance = 0.0

    shipment_predictions = shipment_artifact.get("open_orders") or []
    stockout_predictions = stockout_artifact.get("skus") or []
    shipment_high_risk_share = 0.0
    stockout_high_risk_share = 0.0
    if shipment_predictions:
        shipment_high_risk_share = sum(
            1
            for item in shipment_predictions
            if str(item.get("risk_band", "")) in {"high", "critical"}
        ) / len(shipment_predictions)
    if stockout_predictions:
        stockout_high_risk_share = sum(
            1
            for item in stockout_predictions
            if str(item.get("risk_band", "")) in {"high", "critical"}
        ) / len(stockout_predictions)
    prediction_drift = round(max(shipment_high_risk_share, stockout_high_risk_share), 4)

    checks.append(
        MonitoringCheckArtifact(
            check_name="feature_drift",
            category="ml_quality",
            status=_check_status(
                value=feature_drift,
                warn_threshold=0.15,
                critical_threshold=0.25,
            ),
            metric_name="average_drift_score",
            metric_value=feature_drift,
            threshold_value=0.15,
            message=(
                "Feature drift was estimated from the active champion models in the model registry."
            ),
            recommended_action=(
                "Review feature freshness and retraining need when the average drift score rises."
            ),
            metadata={"champion_models": len(champion_versions)},
        )
    )
    checks.append(
        MonitoringCheckArtifact(
            check_name="prediction_drift",
            category="ml_quality",
            status=_check_status(
                value=prediction_drift,
                warn_threshold=0.40,
                critical_threshold=0.60,
            ),
            metric_name="high_risk_share",
            metric_value=prediction_drift,
            threshold_value=0.40,
            message=(
                "Prediction drift uses the share of high-risk "
                "shipment and stockout outputs in the current run."
            ),
            recommended_action=(
                "Compare output distributions with recent "
                "business context and retrain if the shift persists."
            ),
            metadata={
                "shipment_high_risk_share": round(shipment_high_risk_share, 4),
                "stockout_high_risk_share": round(stockout_high_risk_share, 4),
            },
        )
    )
    checks.append(
        MonitoringCheckArtifact(
            check_name="calibration_drift",
            category="ml_quality",
            status=_check_status(
                value=calibration_drift,
                warn_threshold=0.08,
                critical_threshold=0.12,
            ),
            metric_name="max_calibration_error",
            metric_value=calibration_drift,
            threshold_value=0.08,
            message=(
                "Calibration drift uses the highest active "
                "champion calibration error recorded by model registry."
            ),
            recommended_action=(
                "Reduce confidence exposure or hold automated "
                "actions when calibration becomes unstable."
            ),
            metadata={},
        )
    )
    checks.append(
        MonitoringCheckArtifact(
            check_name="label_lag_aware_performance",
            category="ml_quality",
            status=_inverse_check_status(
                value=lag_aware_performance,
                warn_threshold=0.75,
                critical_threshold=0.50,
            ),
            metric_name="evaluation_pass_rate",
            metric_value=lag_aware_performance,
            threshold_value=0.75,
            message=(
                "The label-lag-aware performance signal uses the "
                "share of champion models that still pass their "
                "evaluation contract."
            ),
            recommended_action=(
                "Revalidate delayed labels and retrain the "
                "affected model family when the pass rate drops."
            ),
            metadata={
                "forecast_products": len(forecast_artifact.get("products") or []),
                "shipment_predictions": len(shipment_predictions),
                "stockout_predictions": len(stockout_predictions),
            },
        )
    )
    return checks


def _forecast_confidence_scores(forecast_artifact: dict[str, Any]) -> list[float]:
    scores: list[float] = []
    for product in forecast_artifact.get("products") or []:
        horizons = product.get("horizons") or []
        for horizon in horizons:
            p10 = _safe_float(horizon.get("p10"), default=0.0)
            p50 = max(_safe_float(horizon.get("p50"), default=0.0), 1.0)
            p90 = _safe_float(horizon.get("p90"), default=0.0)
            interval_width = max(p90 - p10, 0.0)
            confidence = max(0.0, min(1.0, 1.0 - (interval_width / p50)))
            scores.append(round(confidence, 4))
    return scores


def _probability_confidence_scores(items: list[dict[str, Any]], key: str) -> list[float]:
    scores: list[float] = []
    for item in items:
        probability = _safe_float(item.get(key), default=0.5)
        confidence = max(0.0, min(1.0, abs(probability - 0.5) * 2.0))
        scores.append(round(confidence, 4))
    return scores


def _coverage_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(min(1.0, numerator / denominator), 4)


def _build_dashboard_metrics(
    *,
    upload_stats: _UploadStats,
    forecast_artifact: dict[str, Any],
    shipment_artifact: dict[str, Any],
    stockout_artifact: dict[str, Any],
    serving_artifact: dict[str, Any],
) -> tuple[list[MonitoringDashboardMetricArtifact], int, float, float, float]:
    forecast_predictions = list(forecast_artifact.get("products") or [])
    shipment_predictions = list(shipment_artifact.get("open_orders") or [])
    stockout_predictions = list(stockout_artifact.get("skus") or [])

    forecast_confidences = _forecast_confidence_scores(forecast_artifact)
    shipment_confidences = _probability_confidence_scores(shipment_predictions, "probability")
    stockout_confidences = _probability_confidence_scores(
        stockout_predictions,
        "stockout_probability",
    )
    all_confidences = forecast_confidences + shipment_confidences + stockout_confidences
    model_usage_total = len(all_confidences)
    if model_usage_total:
        low_confidence_count = sum(1 for score in all_confidences if score < 0.45)
        abstention_rate = round(low_confidence_count / model_usage_total, 4)
    else:
        abstention_rate = 1.0

    coverage_values: list[float] = []
    sku_denominator = len(upload_stats.unique_skus)
    product_denominator = len(upload_stats.unique_products)
    shipment_denominator = len(upload_stats.unique_shipments)
    stockout_ratio = _coverage_ratio(len(stockout_predictions), sku_denominator)
    if stockout_ratio is not None:
        coverage_values.append(stockout_ratio)
    forecast_ratio = _coverage_ratio(
        len(forecast_predictions),
        product_denominator or sku_denominator,
    )
    if forecast_ratio is not None:
        coverage_values.append(forecast_ratio)
    shipment_ratio = _coverage_ratio(len(shipment_predictions), shipment_denominator)
    if shipment_ratio is not None:
        coverage_values.append(shipment_ratio)
    model_coverage = (
        round(sum(coverage_values) / len(coverage_values), 4) if coverage_values else 0.0
    )

    jobs = serving_artifact.get("jobs") or []
    api_latency_ms = round(120.0 + (len(jobs) * 18.0) + (abstention_rate * 100.0), 2)
    dashboard_metrics = [
        MonitoringDashboardMetricArtifact(
            metric_name="api_latency_ms",
            value=api_latency_ms,
            unit="ms",
            status="warn" if api_latency_ms > 220.0 else "pass",
            description=(
                "Starter API latency estimate derived from "
                "serving-layer batch footprint and abstention."
            ),
        ),
        MonitoringDashboardMetricArtifact(
            metric_name="model_usage_total",
            value=float(model_usage_total),
            unit="predictions",
            status="pass",
            description=(
                "Total prediction objects reviewed across "
                "forecasting, shipment risk, and stockout risk."
            ),
        ),
        MonitoringDashboardMetricArtifact(
            metric_name="model_coverage",
            value=model_coverage,
            unit="ratio",
            status="warn" if model_coverage < 0.7 else "pass",
            description=(
                "Average entity coverage across the prediction "
                "modules that found source entities to score."
            ),
        ),
        MonitoringDashboardMetricArtifact(
            metric_name="abstention_rate",
            value=abstention_rate,
            unit="ratio",
            status="warn" if abstention_rate > 0.25 else "pass",
            description=(
                "Share of predictions whose derived confidence "
                "falls below the low-confidence threshold."
            ),
        ),
    ]
    return dashboard_metrics, model_usage_total, model_coverage, abstention_rate, api_latency_ms


def _alert_flags(check_name: str, status: str) -> tuple[bool, bool]:
    retrain_recommended = status in {"warn", "critical"} and check_name in {
        "feature_drift",
        "prediction_drift",
        "calibration_drift",
        "label_lag_aware_performance",
    }
    disable_prediction_recommended = status == "critical" and check_name in {
        "feature_drift",
        "prediction_drift",
        "calibration_drift",
        "freshness",
    }
    return retrain_recommended, disable_prediction_recommended


def _build_alerts(
    data_checks: list[MonitoringCheckArtifact],
    ml_checks: list[MonitoringCheckArtifact],
    dashboard_metrics: list[MonitoringDashboardMetricArtifact],
) -> list[MonitoringAlertArtifact]:
    alerts: list[MonitoringAlertArtifact] = []
    for check in data_checks + ml_checks:
        if check.status == "pass":
            continue
        retrain_recommended, disable_prediction_recommended = _alert_flags(
            check.check_name,
            check.status,
        )
        alerts.append(
            MonitoringAlertArtifact(
                alert_id=f"alert-{uuid.uuid4().hex[:10]}",
                severity=check.status,
                category=check.category,
                check_name=check.check_name,
                message=check.message,
                recommended_action=check.recommended_action,
                retrain_recommended=retrain_recommended,
                disable_prediction_recommended=disable_prediction_recommended,
            )
        )
    for metric in dashboard_metrics:
        if metric.metric_name != "abstention_rate" or metric.status == "pass":
            continue
        alerts.append(
            MonitoringAlertArtifact(
                alert_id=f"alert-{uuid.uuid4().hex[:10]}",
                severity="warn",
                category="serving_quality",
                check_name="low_confidence_predictions",
                message=(
                    "Abstention rose above the recommended ceiling "
                    "for automated prediction-based actions."
                ),
                recommended_action=(
                    "Review confidence thresholds and consider "
                    "temporary manual approval for edge cases."
                ),
                retrain_recommended=True,
                disable_prediction_recommended=False,
            )
        )
    return alerts


def _override_path(upload_id: str, override_dir: Path) -> Path:
    return override_dir / f"{upload_id}_{OVERRIDE_FILE_SUFFIX}.json"


def _load_override_entries(upload_id: str, override_dir: Path) -> list[dict[str, Any]]:
    path = _override_path(upload_id, override_dir)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Override log is invalid: {path}")
    return [item for item in payload if isinstance(item, dict)]


def _save_override_entries(
    upload_id: str, override_dir: Path, entries: list[dict[str, Any]]
) -> None:
    override_dir.mkdir(parents=True, exist_ok=True)
    path = _override_path(upload_id, override_dir)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def log_manual_override(
    *,
    upload_id: str,
    prediction_type: str,
    entity_id: str,
    original_decision: dict[str, Any],
    override_decision: dict[str, Any],
    reason: str,
    override_dir: Path = Path("data/artifacts/monitoring/overrides"),
    feedback_label: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    if not upload_id.strip():
        raise ValueError("upload_id is required for manual override logging.")
    if not prediction_type.strip():
        raise ValueError("prediction_type is required for manual override logging.")
    if not entity_id.strip():
        raise ValueError("entity_id is required for manual override logging.")
    if not reason.strip():
        raise ValueError("reason is required for manual override logging.")
    entries = _load_override_entries(upload_id, override_dir)
    entry = MonitoringOverrideEntryArtifact(
        override_id=f"override-{uuid.uuid4().hex[:12]}",
        upload_id=upload_id,
        prediction_type=prediction_type.strip(),
        entity_id=entity_id.strip(),
        original_decision=original_decision,
        override_decision=override_decision,
        reason=reason.strip(),
        feedback_label=feedback_label.strip()
        if isinstance(feedback_label, str) and feedback_label.strip()
        else None,
        user_id=user_id.strip() if isinstance(user_id, str) and user_id.strip() else None,
        retraining_feedback_kept=True,
        created_at=_utc_now_iso(),
    )
    entries.append(asdict(entry))
    _save_override_entries(upload_id, override_dir, entries)
    return asdict(entry)


def get_override_summary(
    *,
    upload_id: str,
    override_dir: Path = Path("data/artifacts/monitoring/overrides"),
) -> dict[str, Any]:
    entries = _load_override_entries(upload_id, override_dir)
    counts = Counter(str(item.get("prediction_type", "unknown")) for item in entries)
    last_override_at: str | None = None
    if entries:
        last_override_at = str(entries[-1].get("created_at"))
    summary = MonitoringOverrideSummaryArtifact(
        upload_id=upload_id,
        total_overrides=len(entries),
        by_prediction_type=dict(counts),
        last_override_at=last_override_at,
        entries=[MonitoringOverrideEntryArtifact(**entry) for entry in entries],
    )
    return asdict(summary)


def run_monitoring(
    *,
    upload_id: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    shipment_artifact_dir: Path,
    stockout_artifact_dir: Path,
    serving_artifact_dir: Path,
    registry_artifact_dir: Path,
    artifact_dir: Path,
    override_dir: Path = Path("data/artifacts/monitoring/overrides"),
    refresh: bool = False,
) -> MonitoringArtifact:
    upload_stats = _collect_upload_stats(upload_id, uploads_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    previous_payload: dict[str, Any] | None = None
    previous_path = _previous_artifact_path(upload_id, artifact_dir)
    if previous_path is not None:
        previous_payload = _load_json(previous_path)

    forecast_artifact = get_or_create_batch_forecast_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=forecast_artifact_dir,
        refresh=refresh,
    )
    shipment_artifact = get_or_create_shipment_risk_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=shipment_artifact_dir,
        refresh=refresh,
    )
    stockout_artifact = get_or_create_stockout_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=stockout_artifact_dir,
        refresh=refresh,
    )
    serving_artifact = get_or_create_batch_serving_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        shipment_artifact_dir=shipment_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        artifact_dir=serving_artifact_dir,
        refresh=refresh,
    )
    registry_details = _load_registry_details(registry_artifact_dir, refresh=refresh)

    data_checks = _build_data_checks(
        upload_stats=upload_stats,
        previous_payload=previous_payload,
    )
    ml_checks = _build_ml_checks(
        registry_details=registry_details,
        forecast_artifact=forecast_artifact,
        shipment_artifact=shipment_artifact,
        stockout_artifact=stockout_artifact,
    )
    dashboard_metrics, model_usage_total, model_coverage, abstention_rate, api_latency_ms = (
        _build_dashboard_metrics(
            upload_stats=upload_stats,
            forecast_artifact=forecast_artifact,
            shipment_artifact=shipment_artifact,
            stockout_artifact=stockout_artifact,
            serving_artifact=serving_artifact,
        )
    )
    alerts = _build_alerts(data_checks, ml_checks, dashboard_metrics)
    warning_alerts = sum(1 for alert in alerts if alert.severity == "warn")
    critical_alerts = sum(1 for alert in alerts if alert.severity == "critical")
    retrain_recommended = any(alert.retrain_recommended for alert in alerts)
    disable_prediction_recommended = any(alert.disable_prediction_recommended for alert in alerts)
    override_summary_payload = get_override_summary(
        upload_id=upload_id,
        override_dir=override_dir,
    )
    override_summary = MonitoringOverrideSummaryArtifact(
        **override_summary_payload,
    )
    summary = MonitoringSummaryArtifact(
        source_row_count=upload_stats.row_count,
        source_file_count=upload_stats.file_count,
        total_alerts=len(alerts),
        warning_alerts=warning_alerts,
        critical_alerts=critical_alerts,
        retrain_recommended=retrain_recommended,
        disable_prediction_recommended=disable_prediction_recommended,
        model_usage_total=model_usage_total,
        model_coverage=model_coverage,
        abstention_rate=abstention_rate,
        api_latency_ms=api_latency_ms,
    )
    generated_at = _utc_now_iso()
    artifact_path = artifact_dir / (
        f"{upload_id}_{MONITORING_ARTIFACT_SUFFIX}_"
        f"{generated_at.replace(':', '').replace('+00:00', 'Z')}.json"
    )
    artifact = MonitoringArtifact(
        monitoring_run_id=f"monitoring-monitoring-{uuid.uuid4().hex[:12]}",
        upload_id=upload_id,
        generated_at=generated_at,
        summary=summary,
        data_checks=data_checks,
        ml_checks=ml_checks,
        alerts=alerts,
        dashboard_metrics=dashboard_metrics,
        override_summary=override_summary,
        artifact_path=str(artifact_path),
    )
    _save_json(artifact.to_dict(), artifact_path)
    return artifact


def get_or_create_monitoring_artifact(
    *,
    upload_id: str,
    uploads_dir: Path,
    forecast_artifact_dir: Path,
    shipment_artifact_dir: Path,
    stockout_artifact_dir: Path,
    serving_artifact_dir: Path,
    registry_artifact_dir: Path,
    artifact_dir: Path,
    override_dir: Path = Path("data/artifacts/monitoring/overrides"),
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if not refresh:
        existing = _latest_artifact_path(upload_id, artifact_dir)
        if existing is not None:
            return _load_json(existing)
    artifact = run_monitoring(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        forecast_artifact_dir=forecast_artifact_dir,
        shipment_artifact_dir=shipment_artifact_dir,
        stockout_artifact_dir=stockout_artifact_dir,
        serving_artifact_dir=serving_artifact_dir,
        registry_artifact_dir=registry_artifact_dir,
        artifact_dir=artifact_dir,
        override_dir=override_dir,
        refresh=refresh,
    )
    return artifact.to_dict()
