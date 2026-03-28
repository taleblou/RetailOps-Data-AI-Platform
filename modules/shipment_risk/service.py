from __future__ import annotations

import csv
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

PHASE11_MODEL_VERSION = "phase11-shipment-risk-v1"
PHASE11_THRESHOLD = 0.55
OPEN_STATUSES = {"processing", "pending", "queued", "in_transit", "ready_to_ship"}
HIGH_SIGNAL_STATUSES = {"delayed", "exception"}
PHASE11_ARTIFACT_SUFFIX = "phase11"


class ShipmentRiskArtifactNotFoundError(FileNotFoundError):
    """Raised when a shipment-risk artifact or shipment row cannot be located."""


@dataclass(slots=True)
class ShipmentRow:
    shipment_id: str
    order_id: str
    store_code: str
    carrier: str
    shipment_status: str
    promised_date: str
    actual_delivery_date: str
    order_date: str
    inventory_lag_days: float


@dataclass(slots=True)
class ShipmentContext:
    feature_timestamp: str
    promised_lead_days: float
    warehouse_backlog_7d: float
    carrier_delay_rate_30d: float
    region_delay_trend_30d: float
    overdue_days: float
    weekend_order: bool
    label_is_delayed: bool


@dataclass(slots=True)
class ShipmentRiskMetricsArtifact:
    roc_auc: float
    pr_auc: float
    calibration_gap: float
    precision_at_threshold: float
    recall_at_threshold: float


@dataclass(slots=True)
class ShipmentRiskPredictionArtifact:
    shipment_id: str
    order_id: str
    store_code: str
    carrier: str
    shipment_status: str
    promised_date: str
    actual_delivery_date: str
    probability: float
    risk_band: str
    top_factors: list[str]
    recommended_action: str
    manual_review_required: bool
    manual_review_reason: str
    feature_timestamp: str
    model_version: str
    overdue_days: float
    explanation_summary: str


@dataclass(slots=True)
class ShipmentRiskSummaryArtifact:
    open_orders: int
    high_risk_orders: int
    manual_review_orders: int
    risk_band_counts: dict[str, int]
    carriers: list[str]
    breach_definition: str


@dataclass(slots=True)
class ShipmentRiskArtifact:
    shipment_risk_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: ShipmentRiskSummaryArtifact
    evaluation_metrics: ShipmentRiskMetricsArtifact
    open_orders: list[ShipmentRiskPredictionArtifact]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ManualReviewDecisionArtifact:
    shipment_id: str
    probability: float
    risk_band: str
    manual_review_required: bool
    reason: str
    suggested_owner: str


@dataclass(slots=True)
class _PreparedShipment:
    row: ShipmentRow
    event_date: date
    promised_date: date | None
    actual_delivery_date: date | None
    order_date: date | None
    context: ShipmentContext


@dataclass(slots=True)
class _HistoryRow:
    event_date: date
    promised_date: date | None
    actual_delivery_date: date | None
    store_code: str
    carrier: str
    is_open: bool
    label_is_delayed: bool


@dataclass(slots=True)
class _ResolvedUpload:
    upload_id: str
    csv_path: Path


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
        raise ValueError("upload_id is required for the shipment-risk module.")
    return text


def _resolve_path(value: Any, *, default: str) -> Path:
    if value is None:
        return Path(default)
    return Path(str(value))


def _is_shipment_csv(csv_path: Path) -> bool:
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            headers = next(reader, [])
    except OSError:
        return False
    normalized_headers = {_normalize_key(header) for header in headers}
    required = {"shipment_id", "order_id", "promised_date"}
    return required.issubset(normalized_headers)


def _resolve_upload(upload_id: str, uploads_dir: Path) -> _ResolvedUpload:
    metadata_path = uploads_dir / f"{upload_id}.json"
    if metadata_path.exists():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        stored_path = _to_text(payload.get("stored_path"))
        if stored_path:
            csv_path = Path(stored_path)
            if csv_path.exists() and _is_shipment_csv(csv_path):
                return _ResolvedUpload(upload_id=upload_id, csv_path=csv_path)

    candidates = sorted(uploads_dir.glob(f"{upload_id}_*.csv"))
    for candidate in candidates:
        if _is_shipment_csv(candidate):
            return _ResolvedUpload(upload_id=upload_id, csv_path=candidate)

    raise FileNotFoundError(
        "No shipment CSV was found for this upload_id. Expected metadata stored_path or an "
        "uploads file such as '<upload_id>_shipments.csv'."
    )


def _load_shipment_rows(upload_id: str, uploads_dir: Path) -> list[ShipmentRow]:
    resolved = _resolve_upload(upload_id, uploads_dir)
    rows: list[ShipmentRow] = []
    with resolved.csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for source_row in reader:
            normalized_row = {
                _normalize_key(str(key)): _to_text(value)
                for key, value in source_row.items()
                if key is not None
            }
            shipment_id = _canonical_value(normalized_row, "shipment_id", "shipment id")
            order_id = _canonical_value(normalized_row, "order_id", "order id")
            promised_date = _canonical_value(normalized_row, "promised_date", "promised date")
            if not shipment_id or not order_id or not promised_date:
                continue
            rows.append(
                ShipmentRow(
                    shipment_id=shipment_id,
                    order_id=order_id,
                    store_code=_canonical_value(
                        normalized_row,
                        "store_code",
                        "store code",
                        "store_id",
                    ),
                    carrier=(
                        _canonical_value(normalized_row, "carrier", "carrier_name") or "unknown"
                    ),
                    shipment_status=(
                        _canonical_value(
                            normalized_row,
                            "shipment_status",
                            "shipment status",
                            "status",
                        )
                        or "unknown"
                    ).lower(),
                    promised_date=promised_date,
                    actual_delivery_date=_canonical_value(
                        normalized_row,
                        "actual_delivery_date",
                        "actual delivery date",
                        "delivered_at",
                    ),
                    order_date=_canonical_value(
                        normalized_row,
                        "order_date",
                        "order date",
                        "ordered_at",
                    ),
                    inventory_lag_days=_to_float(
                        _canonical_value(
                            normalized_row,
                            "inventory_lag_days",
                            "inventory lag days",
                        ),
                        default=0.0,
                    ),
                )
            )
    if not rows:
        raise ValueError("Shipment CSV did not contain usable rows.")
    return rows


def _reference_date(rows: list[ShipmentRow]) -> date:
    dates: list[date] = []
    for row in rows:
        for raw_value in (row.actual_delivery_date, row.promised_date, row.order_date):
            parsed = _parse_date(raw_value)
            if parsed is not None:
                dates.append(parsed)
    if not dates:
        return date(2026, 3, 26)
    return max(dates) + timedelta(days=1)


def _build_context(
    row: ShipmentRow,
    *,
    reference_date: date,
    history: list[_HistoryRow],
) -> ShipmentContext:
    promised_date = _parse_date(row.promised_date)
    actual_delivery_date = _parse_date(row.actual_delivery_date)
    order_date = _parse_date(row.order_date)
    event_date = promised_date or order_date or actual_delivery_date or reference_date

    carrier_window = [
        item
        for item in history
        if item.carrier == row.carrier and 0 <= (event_date - item.event_date).days <= 30
    ]
    store_window = [
        item
        for item in history
        if item.store_code == row.store_code and 0 <= (event_date - item.event_date).days <= 30
    ]
    backlog_window = [
        item
        for item in history
        if item.store_code == row.store_code
        and item.is_open
        and 0 <= (event_date - item.event_date).days <= 7
    ]

    carrier_delay_rate = (
        sum(1 for item in carrier_window if item.label_is_delayed) / len(carrier_window)
        if carrier_window
        else 0.0
    )
    region_delay_trend = (
        sum(1 for item in store_window if item.label_is_delayed) / len(store_window)
        if store_window
        else 0.0
    )
    promised_lead_days = 0.0
    if order_date is not None and promised_date is not None:
        promised_lead_days = max((promised_date - order_date).days, 0)

    overdue_days = 0.0
    if promised_date is not None:
        compare_date = actual_delivery_date or reference_date
        overdue_days = max((compare_date - promised_date).days, 0)

    label_is_delayed = False
    if actual_delivery_date is not None and promised_date is not None:
        label_is_delayed = actual_delivery_date > promised_date
    elif row.shipment_status in HIGH_SIGNAL_STATUSES:
        label_is_delayed = True

    feature_timestamp = (order_date or promised_date or reference_date).isoformat()
    return ShipmentContext(
        feature_timestamp=feature_timestamp,
        promised_lead_days=round(promised_lead_days, 2),
        warehouse_backlog_7d=float(len(backlog_window)),
        carrier_delay_rate_30d=round(carrier_delay_rate, 4),
        region_delay_trend_30d=round(region_delay_trend, 4),
        overdue_days=round(overdue_days, 2),
        weekend_order=(order_date is not None and order_date.weekday() >= 5),
        label_is_delayed=label_is_delayed,
    )


def _score_probability(row: ShipmentRow, context: ShipmentContext) -> float:
    score = 0.08
    score += min(context.carrier_delay_rate_30d, 1.0) * 0.28
    score += min(context.region_delay_trend_30d, 1.0) * 0.16
    score += min(context.warehouse_backlog_7d / 12.0, 1.0) * 0.12
    score += min(max(row.inventory_lag_days, 0.0) / 7.0, 1.0) * 0.08
    score += min(max(context.overdue_days, 0.0) / 5.0, 1.0) * 0.22
    if row.shipment_status in HIGH_SIGNAL_STATUSES:
        score += 0.25
    elif row.shipment_status == "processing":
        score += 0.08
    elif row.shipment_status == "in_transit":
        score += 0.05
    if context.weekend_order:
        score += 0.04
    if context.promised_lead_days > 6:
        score += 0.05
    return round(min(max(score, 0.01), 0.99), 4)


def _risk_band(probability: float) -> str:
    if probability >= 0.8:
        return "critical"
    if probability >= 0.55:
        return "high"
    if probability >= 0.3:
        return "medium"
    return "low"


def _top_factors(row: ShipmentRow, context: ShipmentContext, probability: float) -> list[str]:
    candidates = [
        (
            context.overdue_days / 5.0 if context.overdue_days else 0.0,
            f"overdue_days={context.overdue_days:g}",
        ),
        (
            context.carrier_delay_rate_30d,
            f"carrier_delay_rate_30d={context.carrier_delay_rate_30d:.2f}",
        ),
        (
            context.region_delay_trend_30d,
            f"region_delay_trend_30d={context.region_delay_trend_30d:.2f}",
        ),
        (
            context.warehouse_backlog_7d / 10.0,
            f"warehouse_backlog_7d={context.warehouse_backlog_7d:g}",
        ),
        (row.inventory_lag_days / 7.0, f"inventory_lag_days={row.inventory_lag_days:g}"),
        (
            1.0 if row.shipment_status in HIGH_SIGNAL_STATUSES else 0.0,
            f"shipment_status={row.shipment_status}",
        ),
        (1.0 if context.weekend_order else 0.0, "weekend_order=true"),
        (probability, f"score={probability:.2f}"),
    ]
    ranked_candidates = sorted(candidates, key=lambda item: item[0], reverse=True)
    factors = [item[1] for item in ranked_candidates if item[0] > 0][:3]
    if not factors:
        return [f"score={probability:.2f}"]
    return factors


def _recommended_action(probability: float, context: ShipmentContext) -> str:
    if probability >= 0.8 or context.overdue_days >= 2:
        return "Escalate to the carrier and notify store operations today."
    if probability >= 0.55:
        return "Queue this order for manual review and prepare a customer update."
    if probability >= 0.3:
        return "Monitor the shipment and confirm dispatch timing with the warehouse."
    return "Keep under normal monitoring. No immediate action is required."


def _manual_review_reason(probability: float, row: ShipmentRow, context: ShipmentContext) -> str:
    reasons: list[str] = []
    if probability >= 0.65:
        reasons.append("predicted risk is above the manual-review threshold")
    if context.overdue_days >= 2:
        reasons.append("shipment is already overdue")
    if row.shipment_status in HIGH_SIGNAL_STATUSES:
        reasons.append("shipment status already signals an issue")
    if context.carrier_delay_rate_30d >= 0.35:
        reasons.append("recent carrier history is weak")
    return "; ".join(reasons)


def _build_prediction(row: ShipmentRow, context: ShipmentContext) -> ShipmentRiskPredictionArtifact:
    probability = _score_probability(row, context)
    risk_band = _risk_band(probability)
    top_factors = _top_factors(row, context, probability)
    manual_review_reason = _manual_review_reason(probability, row, context)
    manual_review_required = bool(manual_review_reason)
    explanation_summary = (
        f"Shipment {row.shipment_id or row.order_id} is in the {risk_band} band with a delay "
        f"probability of {probability:.2f}. Top factors: {', '.join(top_factors)}."
    )
    return ShipmentRiskPredictionArtifact(
        shipment_id=row.shipment_id,
        order_id=row.order_id,
        store_code=row.store_code,
        carrier=row.carrier,
        shipment_status=row.shipment_status,
        promised_date=row.promised_date,
        actual_delivery_date=row.actual_delivery_date,
        probability=probability,
        risk_band=risk_band,
        top_factors=top_factors,
        recommended_action=_recommended_action(probability, context),
        manual_review_required=manual_review_required,
        manual_review_reason=manual_review_reason,
        feature_timestamp=context.feature_timestamp,
        model_version=PHASE11_MODEL_VERSION,
        overdue_days=context.overdue_days,
        explanation_summary=explanation_summary,
    )


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _roc_auc(scores: list[float], labels: list[int]) -> float:
    positives = [score for score, label in zip(scores, labels, strict=False) if label == 1]
    negatives = [score for score, label in zip(scores, labels, strict=False) if label == 0]
    if not positives or not negatives:
        return 0.0
    wins = 0.0
    total = len(positives) * len(negatives)
    for pos_score in positives:
        for neg_score in negatives:
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
    return round(wins / total, 4)


def _precision_recall(
    scores: list[float],
    labels: list[int],
    threshold: float,
) -> tuple[float, float]:
    true_positive = 0
    false_positive = 0
    false_negative = 0
    for score, label in zip(scores, labels, strict=False):
        predicted_positive = score >= threshold
        if predicted_positive and label == 1:
            true_positive += 1
        elif predicted_positive and label == 0:
            false_positive += 1
        elif not predicted_positive and label == 1:
            false_negative += 1
    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive)
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative)
        else 0.0
    )
    return round(precision, 4), round(recall, 4)


def _pr_auc(scores: list[float], labels: list[int]) -> float:
    if not scores or not any(label == 1 for label in labels):
        return 0.0
    thresholds = sorted({0.0, 1.0, *scores}, reverse=True)
    points: list[tuple[float, float]] = []
    for threshold in thresholds:
        precision, recall = _precision_recall(scores, labels, threshold)
        points.append((recall, precision))
    points = sorted(points, key=lambda item: item[0])
    area = 0.0
    for (recall_a, precision_a), (recall_b, precision_b) in zip(points, points[1:], strict=False):
        width = recall_b - recall_a
        height = (precision_a + precision_b) / 2.0
        area += width * height
    return round(max(area, 0.0), 4)


def _calibration_gap(scores: list[float], labels: list[int]) -> float:
    if not scores or not labels:
        return 0.0
    return round(abs(_mean(scores) - _mean([float(label) for label in labels])), 4)


def _evaluation_metrics(
    predictions: list[ShipmentRiskPredictionArtifact],
    contexts: list[ShipmentContext],
) -> ShipmentRiskMetricsArtifact:
    scored_items = [
        (prediction.probability, 1 if context.label_is_delayed else 0)
        for prediction, context in zip(predictions, contexts, strict=False)
        if prediction.actual_delivery_date
    ]
    if not scored_items:
        return ShipmentRiskMetricsArtifact(
            roc_auc=0.0,
            pr_auc=0.0,
            calibration_gap=0.0,
            precision_at_threshold=0.0,
            recall_at_threshold=0.0,
        )
    scores = [item[0] for item in scored_items]
    labels = [item[1] for item in scored_items]
    precision, recall = _precision_recall(scores, labels, PHASE11_THRESHOLD)
    return ShipmentRiskMetricsArtifact(
        roc_auc=_roc_auc(scores, labels),
        pr_auc=_pr_auc(scores, labels),
        calibration_gap=_calibration_gap(scores, labels),
        precision_at_threshold=precision,
        recall_at_threshold=recall,
    )


def _prepare_shipments(rows: list[ShipmentRow]) -> list[_PreparedShipment]:
    reference_date = _reference_date(rows)
    history: list[_HistoryRow] = []
    prepared: list[_PreparedShipment] = []
    sortable: list[tuple[date, ShipmentRow]] = []
    for row in rows:
        promised_date = _parse_date(row.promised_date)
        actual_delivery_date = _parse_date(row.actual_delivery_date)
        order_date = _parse_date(row.order_date)
        event_date = promised_date or order_date or actual_delivery_date or reference_date
        sortable.append((event_date, row))

    for event_date, row in sorted(sortable, key=lambda item: (item[0], item[1].shipment_id)):
        promised_date = _parse_date(row.promised_date)
        actual_delivery_date = _parse_date(row.actual_delivery_date)
        order_date = _parse_date(row.order_date)
        context = _build_context(row, reference_date=reference_date, history=history)
        prepared.append(
            _PreparedShipment(
                row=row,
                event_date=event_date,
                promised_date=promised_date,
                actual_delivery_date=actual_delivery_date,
                order_date=order_date,
                context=context,
            )
        )
        history.append(
            _HistoryRow(
                event_date=event_date,
                promised_date=promised_date,
                actual_delivery_date=actual_delivery_date,
                store_code=row.store_code,
                carrier=row.carrier,
                is_open=(
                    actual_delivery_date is None
                    and row.shipment_status in OPEN_STATUSES | HIGH_SIGNAL_STATUSES
                ),
                label_is_delayed=context.label_is_delayed,
            )
        )
    return prepared


def run_phase11_shipment_risk(*args: Any, **kwargs: Any) -> ShipmentRiskArtifact:
    upload_id = _resolve_upload_id(args, kwargs)
    uploads_dir = _resolve_path(kwargs.get("uploads_dir"), default="data/uploads")
    artifact_dir = _resolve_path(kwargs.get("artifact_dir"), default="data/artifacts/shipment_risk")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_shipment_rows(upload_id, uploads_dir)
    prepared = _prepare_shipments(rows)
    all_predictions = [_build_prediction(item.row, item.context) for item in prepared]
    evaluation_metrics = _evaluation_metrics(all_predictions, [item.context for item in prepared])

    open_order_predictions = [
        prediction
        for item, prediction in zip(prepared, all_predictions, strict=False)
        if item.actual_delivery_date is None
        and item.row.shipment_status in OPEN_STATUSES | HIGH_SIGNAL_STATUSES
    ]
    open_order_predictions.sort(key=lambda item: item.probability, reverse=True)

    risk_band_counts = {
        "critical": sum(1 for item in open_order_predictions if item.risk_band == "critical"),
        "high": sum(1 for item in open_order_predictions if item.risk_band == "high"),
        "medium": sum(1 for item in open_order_predictions if item.risk_band == "medium"),
        "low": sum(1 for item in open_order_predictions if item.risk_band == "low"),
    }
    summary = ShipmentRiskSummaryArtifact(
        open_orders=len(open_order_predictions),
        high_risk_orders=sum(
            1 for item in open_order_predictions if item.probability >= PHASE11_THRESHOLD
        ),
        manual_review_orders=sum(
            1 for item in open_order_predictions if item.manual_review_required
        ),
        risk_band_counts=risk_band_counts,
        carriers=sorted({item.carrier for item in open_order_predictions}),
        breach_definition="delay if actual_delivery_date > promised_date",
    )

    shipment_risk_run_id = f"sr_{uuid.uuid4().hex[:12]}"
    artifact_path = (
        artifact_dir / f"{upload_id}_{shipment_risk_run_id}_{PHASE11_ARTIFACT_SUFFIX}.json"
    )
    artifact = ShipmentRiskArtifact(
        shipment_risk_run_id=shipment_risk_run_id,
        upload_id=upload_id,
        generated_at=datetime.now(UTC).isoformat(),
        model_version=PHASE11_MODEL_VERSION,
        summary=summary,
        evaluation_metrics=evaluation_metrics,
        open_orders=open_order_predictions,
        artifact_path=str(artifact_path),
    )
    artifact_path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return artifact


def get_or_create_phase11_artifact(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    pattern = f"{upload_id}_*_phase11.json"
    if not refresh:
        existing = sorted(
            artifact_dir.glob(pattern),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if existing:
            return json.loads(existing[0].read_text(encoding="utf-8"))
    artifact = run_phase11_shipment_risk(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )
    return artifact.to_dict()


def get_open_order_predictions(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    artifact = get_or_create_phase11_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    items = artifact.get("open_orders")
    if not isinstance(items, list):
        raise ShipmentRiskArtifactNotFoundError(
            "Shipment-risk artifact is missing open-order predictions."
        )
    if limit is not None and limit > 0:
        items = items[:limit]
    return {
        "shipment_risk_run_id": artifact.get("shipment_risk_run_id"),
        "upload_id": artifact.get("upload_id"),
        "generated_at": artifact.get("generated_at"),
        "model_version": artifact.get("model_version"),
        "summary": artifact.get("summary") or {},
        "evaluation_metrics": artifact.get("evaluation_metrics") or {},
        "open_orders": items,
        "artifact_path": artifact.get("artifact_path", ""),
    }


def get_open_order_prediction(
    *,
    upload_id: str,
    shipment_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact = get_or_create_phase11_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    for item in artifact.get("open_orders") or []:
        if _to_text(item.get("shipment_id")) == shipment_id:
            return item
    raise ShipmentRiskArtifactNotFoundError(
        f"Shipment '{shipment_id}' was not found in the open-order shipment-risk artifact."
    )


def predict_shipment_delay(payload: dict[str, Any]) -> dict[str, Any]:
    row = ShipmentRow(
        shipment_id=_to_text(payload.get("shipment_id")) or "manual-input",
        order_id=_to_text(payload.get("order_id")),
        store_code=_to_text(payload.get("store_code")) or "unknown",
        carrier=_to_text(payload.get("carrier")) or "unknown",
        shipment_status=_to_text(payload.get("shipment_status") or "processing").lower(),
        promised_date=_to_text(payload.get("promised_date")),
        actual_delivery_date=_to_text(payload.get("actual_delivery_date")),
        order_date=_to_text(payload.get("order_date")),
        inventory_lag_days=_to_float(payload.get("inventory_lag_days"), default=0.0),
    )
    reference_date = (
        _parse_date(_to_text(payload.get("reference_date")))
        or _parse_date(row.promised_date)
        or date(2026, 3, 26)
    )
    context = ShipmentContext(
        feature_timestamp=(
            _parse_date(row.order_date) or _parse_date(row.promised_date) or reference_date
        ).isoformat(),
        promised_lead_days=max(
            (
                (_parse_date(row.promised_date) or reference_date)
                - (_parse_date(row.order_date) or reference_date)
            ).days,
            0,
        ),
        warehouse_backlog_7d=_to_float(payload.get("warehouse_backlog_7d"), default=0.0),
        carrier_delay_rate_30d=_to_float(payload.get("carrier_delay_rate_30d"), default=0.0),
        region_delay_trend_30d=_to_float(payload.get("region_delay_trend_30d"), default=0.0),
        overdue_days=max(
            (reference_date - (_parse_date(row.promised_date) or reference_date)).days,
            0,
        ),
        weekend_order=(_parse_date(row.order_date) or reference_date).weekday() >= 5,
        label_is_delayed=False,
    )
    return asdict(_build_prediction(row, context))


def build_manual_review_decision(payload: dict[str, Any]) -> ManualReviewDecisionArtifact:
    prediction = predict_shipment_delay(payload)
    return ManualReviewDecisionArtifact(
        shipment_id=_to_text(prediction.get("shipment_id")),
        probability=_to_float(prediction.get("probability")),
        risk_band=_to_text(prediction.get("risk_band")),
        manual_review_required=bool(prediction.get("manual_review_required")),
        reason=_to_text(prediction.get("manual_review_reason")),
        suggested_owner=(
            "store-ops" if bool(prediction.get("manual_review_required")) else "automation"
        ),
    )
