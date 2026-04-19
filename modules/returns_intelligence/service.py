# Project:      RetailOps Data & AI Platform
# Module:       modules.returns_intelligence
# File:         service.py
# Path:         modules/returns_intelligence/service.py
#
# Summary:      Implements the returns intelligence service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for returns intelligence workflows.
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
#   - Main types: ReturnRiskArtifactNotFoundError, ReturnRiskPredictionArtifact, ReturnRiskProductArtifact, ReturnRiskSummaryArtifact, ReturnRiskArtifact, _ResolvedUpload, ...
#   - Key APIs: run_returns_intelligence, load_returns_artifact, get_or_create_returns_artifact, get_return_risk_scores, get_return_risk_order, get_return_risk_products, ...
#   - Dependencies: __future__, csv, json, uuid, collections, dataclasses, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import json
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

RETURNS_MODEL_VERSION = "returns-intelligence-v1"
RETURNS_ARTIFACT_SUFFIX = "returns"
DEFAULT_RETURN_WINDOW_DAYS = 30
BASELINE_RETURN_RATE = 0.08
CATEGORY_RISK_WEIGHTS = {
    "fashion": 0.08,
    "footwear": 0.07,
    "home": 0.03,
    "beauty": 0.06,
    "electronics": 0.02,
    "general": 0.04,
}

RETURN_STATUSES = {"returned", "return", "refunded", "refund", "exchange"}
TRUTHY_VALUES = {"1", "true", "yes", "y", "returned"}


class ReturnRiskArtifactNotFoundError(FileNotFoundError):
    """Raised when a returns intelligence returns artifact or order row cannot be located."""


@dataclass(slots=True)
class ReturnRiskPredictionArtifact:
    order_id: str
    customer_id: str
    sku: str
    store_code: str
    order_date: str
    category: str
    quantity: float
    unit_price: float
    gross_revenue: float
    discount_rate: float
    discount_level: str
    shipment_delay_days: float
    customer_return_rate_180d: float
    sku_return_rate_180d: float
    return_probability: float
    expected_return_cost: float
    return_cost_band: str
    risk_band: str
    top_factors: list[str]
    recommended_action: str
    label_return_within_days: int
    feature_timestamp: str
    model_version: str
    explanation_summary: str


@dataclass(slots=True)
class ReturnRiskProductArtifact:
    sku: str
    store_code: str
    category: str
    orders_scored: int
    average_return_probability: float
    total_expected_return_cost: float
    risk_band: str
    return_cost_band: str


@dataclass(slots=True)
class ReturnRiskSummaryArtifact:
    total_orders: int
    high_risk_orders: int
    risky_products_count: int
    average_return_probability: float
    total_expected_return_cost: float
    output_features_table: str
    output_predictions_table: str


@dataclass(slots=True)
class ReturnRiskArtifact:
    return_risk_run_id: str
    upload_id: str
    generated_at: str
    model_version: str
    summary: ReturnRiskSummaryArtifact
    scores: list[ReturnRiskPredictionArtifact]
    risky_products: list[ReturnRiskProductArtifact]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class _ResolvedUpload:
    upload_id: str
    csv_path: Path


@dataclass(slots=True)
class _OrderRow:
    order_id: str
    customer_id: str
    sku: str
    store_code: str
    order_date: date
    category: str
    quantity: float
    unit_price: float
    discount_rate: float
    shipment_delay_days: float
    returned_within_window: bool
    explicit_return_cost: float | None


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
        raise ValueError("upload_id is required for the returns-intelligence module.")
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
    required = {"order_id", "order_date", "customer_id", "sku"}
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


def _derive_category(normalized_row: dict[str, str], sku: str) -> str:
    explicit_category = _canonical_value(
        normalized_row, "category", "product_category", "department"
    )
    if explicit_category:
        return explicit_category.lower()

    digits = "".join(character for character in sku if character.isdigit())
    numeric_key = int(digits[-2:] or "0") % 5
    lookup = {
        0: "fashion",
        1: "electronics",
        2: "home",
        3: "beauty",
        4: "general",
    }
    return lookup.get(numeric_key, "general")


def _parse_discount_rate(normalized_row: dict[str, str]) -> float:
    direct_rate = _to_float(
        _canonical_value(
            normalized_row,
            "discount_rate",
            "discount_percent",
            "discount_pct",
        ),
        default=-1.0,
    )
    if direct_rate >= 0.0:
        if direct_rate > 1.0:
            direct_rate = direct_rate / 100.0
        return min(max(direct_rate, 0.0), 0.9)

    discount_amount = _to_float(
        _canonical_value(normalized_row, "discount_amount", "line_discount", "discount"),
        default=0.0,
    )
    quantity = max(
        _to_float(_canonical_value(normalized_row, "quantity", "qty"), default=1.0),
        1.0,
    )
    unit_price = _to_float(_canonical_value(normalized_row, "unit_price", "price"), default=0.0)
    gross_revenue = quantity * unit_price
    if discount_amount > 0.0 and gross_revenue > 0.0:
        return min(max(discount_amount / gross_revenue, 0.0), 0.9)

    discount_level = _canonical_value(normalized_row, "discount_level")
    normalized_level = discount_level.lower()
    if normalized_level == "high":
        return 0.35
    if normalized_level == "medium":
        return 0.18
    if normalized_level == "low":
        return 0.08
    return 0.0


def _parse_return_flag(normalized_row: dict[str, str]) -> bool:
    order_status = _canonical_value(normalized_row, "order_status", "status").lower()
    if order_status in RETURN_STATUSES:
        return True
    return_flag = _canonical_value(
        normalized_row,
        "returned",
        "return_flag",
        "is_returned",
        "returned_within_30_days",
    ).lower()
    if return_flag in TRUTHY_VALUES:
        return True
    returned_qty = _to_float(
        _canonical_value(normalized_row, "returned_qty", "return_quantity"), default=0.0
    )
    return returned_qty > 0.0


def _parse_shipment_delay_days(normalized_row: dict[str, str]) -> float:
    delay_days = _to_float(
        _canonical_value(
            normalized_row, "shipment_delay_days", "delay_days", "shipping_delay_days"
        ),
        default=-1.0,
    )
    if delay_days >= 0.0:
        return delay_days

    promised_date = _parse_date(
        _canonical_value(normalized_row, "promised_date", "promised_delivery_date")
    )
    delivered_date = _parse_date(
        _canonical_value(normalized_row, "actual_delivery_date", "delivered_date", "shipment_date")
    )
    if promised_date is not None and delivered_date is not None:
        return max(float((delivered_date - promised_date).days), 0.0)
    return 0.0


def _load_order_rows(upload_id: str, uploads_dir: Path) -> list[_OrderRow]:
    resolved = _resolve_upload(upload_id, uploads_dir)
    rows: list[_OrderRow] = []
    with resolved.csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for source_row in reader:
            normalized_row = {
                _normalize_key(str(key)): _to_text(value)
                for key, value in source_row.items()
                if key is not None
            }
            order_date = _parse_date(_canonical_value(normalized_row, "order_date", "ordered_at"))
            order_id = _canonical_value(normalized_row, "order_id", "id")
            customer_id = _canonical_value(normalized_row, "customer_id", "customer")
            sku = _canonical_value(normalized_row, "sku", "product_sku", "product_id")
            if order_date is None or not order_id or not customer_id or not sku:
                continue
            store_code = _canonical_value(normalized_row, "store_code", "store") or "unknown"
            quantity = max(
                _to_float(_canonical_value(normalized_row, "quantity", "qty"), default=1.0), 1.0
            )
            unit_price = max(
                _to_float(_canonical_value(normalized_row, "unit_price", "price"), default=0.0), 0.0
            )
            explicit_return_cost = _to_float(
                _canonical_value(normalized_row, "return_cost", "expected_return_cost"),
                default=-1.0,
            )
            rows.append(
                _OrderRow(
                    order_id=order_id,
                    customer_id=customer_id,
                    sku=sku,
                    store_code=store_code,
                    order_date=order_date,
                    category=_derive_category(normalized_row, sku),
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_rate=_parse_discount_rate(normalized_row),
                    shipment_delay_days=_parse_shipment_delay_days(normalized_row),
                    returned_within_window=_parse_return_flag(normalized_row),
                    explicit_return_cost=None
                    if explicit_return_cost < 0.0
                    else explicit_return_cost,
                )
            )
    if not rows:
        raise ValueError(
            "The returns-intelligence module could not build any usable rows from the uploaded CSV."
        )
    rows.sort(key=lambda item: (item.order_date, item.order_id))
    return rows


def _probability_band(probability: float) -> str:
    if probability >= 0.7:
        return "critical"
    if probability >= 0.45:
        return "high"
    if probability >= 0.22:
        return "medium"
    return "low"


def _cost_band(expected_cost: float) -> str:
    if expected_cost >= 160.0:
        return "critical"
    if expected_cost >= 90.0:
        return "high"
    if expected_cost >= 35.0:
        return "medium"
    return "low"


def _discount_level(discount_rate: float) -> str:
    if discount_rate >= 0.3:
        return "high"
    if discount_rate >= 0.12:
        return "medium"
    if discount_rate > 0.0:
        return "low"
    return "none"


def _recommended_action(risk_band: str, cost_band: str) -> str:
    if risk_band == "critical":
        return "Route to manual return review and tighten promotion exposure."
    if risk_band == "high" or cost_band in {"high", "critical"}:
        return "Review product page, sizing, and discount policy before the next campaign."
    if risk_band == "medium":
        return "Monitor the SKU and notify customer support about elevated return risk."
    return "No immediate action. Keep standard post-purchase follow-up."


def _explanation_summary(
    *,
    probability: float,
    customer_rate: float,
    sku_rate: float,
    discount_rate: float,
    shipment_delay_days: float,
) -> tuple[list[str], str]:
    weighted_factors = [
        (customer_rate * 100.0, f"customer return rate {customer_rate:.0%}"),
        (sku_rate * 100.0, f"SKU return rate {sku_rate:.0%}"),
        (discount_rate * 100.0, f"discount level {discount_rate:.0%}"),
        (shipment_delay_days * 8.0, f"shipment delay {shipment_delay_days:.0f} days"),
    ]
    top_factors = [label for _, label in sorted(weighted_factors, reverse=True)[:3] if _ > 0.0]
    if not top_factors:
        top_factors = ["baseline retail return behaviour"]
    summary = (
        f"Estimated return probability is {probability:.0%}. "
        f"Main factors: {', '.join(top_factors)}."
    )
    return top_factors, summary


def _build_product_rollup(
    scores: list[ReturnRiskPredictionArtifact],
) -> list[ReturnRiskProductArtifact]:
    grouped: dict[tuple[str, str], list[ReturnRiskPredictionArtifact]] = defaultdict(list)
    for score in scores:
        grouped[(score.sku, score.store_code)].append(score)

    risky_products: list[ReturnRiskProductArtifact] = []
    for group_scores in grouped.values():
        first = group_scores[0]
        orders_scored = len(group_scores)
        average_probability = sum(item.return_probability for item in group_scores) / orders_scored
        total_expected_cost = sum(item.expected_return_cost for item in group_scores)
        risky_products.append(
            ReturnRiskProductArtifact(
                sku=first.sku,
                store_code=first.store_code,
                category=first.category,
                orders_scored=orders_scored,
                average_return_probability=round(average_probability, 4),
                total_expected_return_cost=round(total_expected_cost, 2),
                risk_band=_probability_band(average_probability),
                return_cost_band=_cost_band(total_expected_cost),
            )
        )

    risky_products.sort(
        key=lambda item: (item.total_expected_return_cost, item.average_return_probability),
        reverse=True,
    )
    return risky_products


def run_returns_intelligence(
    *, upload_id: str, uploads_dir: Path, artifact_dir: Path
) -> ReturnRiskArtifact:
    order_rows = _load_order_rows(upload_id, uploads_dir)
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    feature_timestamp = generated_at
    cutoff_days = timedelta(days=180)

    customer_history: dict[str, list[tuple[date, bool]]] = defaultdict(list)
    sku_history: dict[str, list[tuple[date, bool]]] = defaultdict(list)
    scores: list[ReturnRiskPredictionArtifact] = []

    for row in order_rows:
        customer_events = [
            event
            for event in customer_history[row.customer_id]
            if row.order_date - event[0] <= cutoff_days
        ]
        sku_events = [
            event for event in sku_history[row.sku] if row.order_date - event[0] <= cutoff_days
        ]
        customer_history[row.customer_id] = customer_events
        sku_history[row.sku] = sku_events

        customer_rate = (
            sum(1 for _, returned in customer_events if returned) / len(customer_events)
            if customer_events
            else BASELINE_RETURN_RATE
        )
        sku_rate = (
            sum(1 for _, returned in sku_events if returned) / len(sku_events)
            if sku_events
            else BASELINE_RETURN_RATE
        )
        category_weight = CATEGORY_RISK_WEIGHTS.get(row.category, CATEGORY_RISK_WEIGHTS["general"])
        gross_revenue = row.quantity * row.unit_price
        price_signal = min(row.unit_price / 150.0, 0.12)
        quantity_signal = min(max(row.quantity - 1.0, 0.0) * 0.02, 0.08)
        delay_signal = min(row.shipment_delay_days * 0.03, 0.18)
        discount_signal = row.discount_rate * 0.30
        customer_signal = customer_rate * 0.34
        sku_signal = sku_rate * 0.24
        probability = min(
            max(
                0.04
                + category_weight
                + customer_signal
                + sku_signal
                + discount_signal
                + delay_signal
                + price_signal
                + quantity_signal,
                0.02,
            ),
            0.95,
        )
        cost_multiplier = (
            0.30 + (row.discount_rate * 0.45) + min(row.shipment_delay_days * 0.04, 0.2)
        )
        expected_return_cost = row.explicit_return_cost
        if expected_return_cost is None:
            expected_return_cost = gross_revenue * probability * max(cost_multiplier, 0.22)
        risk_band = _probability_band(probability)
        return_cost_band = _cost_band(expected_return_cost)
        discount_level = _discount_level(row.discount_rate)
        top_factors, explanation_summary = _explanation_summary(
            probability=probability,
            customer_rate=customer_rate,
            sku_rate=sku_rate,
            discount_rate=row.discount_rate,
            shipment_delay_days=row.shipment_delay_days,
        )
        scores.append(
            ReturnRiskPredictionArtifact(
                order_id=row.order_id,
                customer_id=row.customer_id,
                sku=row.sku,
                store_code=row.store_code,
                order_date=row.order_date.isoformat(),
                category=row.category,
                quantity=round(row.quantity, 2),
                unit_price=round(row.unit_price, 2),
                gross_revenue=round(gross_revenue, 2),
                discount_rate=round(row.discount_rate, 4),
                discount_level=discount_level,
                shipment_delay_days=round(row.shipment_delay_days, 2),
                customer_return_rate_180d=round(customer_rate, 4),
                sku_return_rate_180d=round(sku_rate, 4),
                return_probability=round(probability, 4),
                expected_return_cost=round(expected_return_cost, 2),
                return_cost_band=return_cost_band,
                risk_band=risk_band,
                top_factors=top_factors,
                recommended_action=_recommended_action(risk_band, return_cost_band),
                label_return_within_days=DEFAULT_RETURN_WINDOW_DAYS,
                feature_timestamp=feature_timestamp,
                model_version=RETURNS_MODEL_VERSION,
                explanation_summary=explanation_summary,
            )
        )
        customer_history[row.customer_id].append((row.order_date, row.returned_within_window))
        sku_history[row.sku].append((row.order_date, row.returned_within_window))

    scores.sort(
        key=lambda item: (item.return_probability, item.expected_return_cost, item.order_date),
        reverse=True,
    )
    risky_products = _build_product_rollup(scores)
    summary = ReturnRiskSummaryArtifact(
        total_orders=len(scores),
        high_risk_orders=sum(1 for item in scores if item.risk_band in {"high", "critical"}),
        risky_products_count=sum(
            1 for item in risky_products if item.risk_band in {"high", "critical"}
        ),
        average_return_probability=round(
            sum(item.return_probability for item in scores) / len(scores),
            4,
        ),
        total_expected_return_cost=round(sum(item.expected_return_cost for item in scores), 2),
        output_features_table="features.return_risk_features",
        output_predictions_table="predictions.return_risk_scores",
    )

    artifact = ReturnRiskArtifact(
        return_risk_run_id=f"rr_{uuid.uuid4().hex[:12]}",
        upload_id=upload_id,
        generated_at=generated_at,
        model_version=RETURNS_MODEL_VERSION,
        summary=summary,
        scores=scores,
        risky_products=risky_products,
        artifact_path=str(artifact_dir / f"{upload_id}_{RETURNS_ARTIFACT_SUFFIX}.json"),
    )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = Path(artifact.artifact_path)
    artifact_path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return artifact


def load_returns_artifact(*, upload_id: str, artifact_dir: Path) -> dict[str, Any]:
    artifact_path = artifact_dir / f"{upload_id}_{RETURNS_ARTIFACT_SUFFIX}.json"
    if not artifact_path.exists():
        raise ReturnRiskArtifactNotFoundError(
            f"No returns intelligence returns artifact exists for upload_id={upload_id}."
        )
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def get_or_create_returns_artifact(*, refresh: bool = False, **kwargs: Any) -> dict[str, Any]:
    upload_id = _resolve_upload_id((), kwargs)
    artifact_dir = _resolve_path(kwargs.get("artifact_dir"), default="data/artifacts/returns_risk")
    uploads_dir = _resolve_path(kwargs.get("uploads_dir"), default="data/uploads")

    if not refresh:
        try:
            return load_returns_artifact(upload_id=upload_id, artifact_dir=artifact_dir)
        except ReturnRiskArtifactNotFoundError:
            pass

    artifact = run_returns_intelligence(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
    )
    return artifact.to_dict()


def get_return_risk_scores(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 100,
    store_code: str | None = None,
    risk_band: str | None = None,
) -> dict[str, Any]:
    artifact = get_or_create_returns_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    scores = artifact.get("scores")
    risky_products = artifact.get("risky_products")
    if not isinstance(scores, list) or not isinstance(risky_products, list):
        raise ValueError(
            "Returns intelligence returns artifact is missing scores or risky_products."
        )

    filtered_scores = [item for item in scores if isinstance(item, dict)]
    filtered_products = [item for item in risky_products if isinstance(item, dict)]
    if store_code:
        filtered_scores = [
            item for item in filtered_scores if _to_text(item.get("store_code")) == store_code
        ]
        filtered_products = [
            item for item in filtered_products if _to_text(item.get("store_code")) == store_code
        ]
    if risk_band:
        filtered_scores = [
            item for item in filtered_scores if _to_text(item.get("risk_band")) == risk_band
        ]
        filtered_products = [
            item for item in filtered_products if _to_text(item.get("risk_band")) == risk_band
        ]

    result = dict(artifact)
    result["scores"] = filtered_scores[:limit]
    result["risky_products"] = filtered_products[:limit]
    return result


def get_return_risk_order(
    *,
    upload_id: str,
    order_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
) -> dict[str, Any]:
    artifact = get_or_create_returns_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    scores = artifact.get("scores")
    if not isinstance(scores, list):
        raise ValueError("Returns intelligence returns artifact is missing the scores list.")
    for item in scores:
        if isinstance(item, dict) and _to_text(item.get("order_id")) == order_id:
            return item
    raise ReturnRiskArtifactNotFoundError(
        f"No returns intelligence return-risk score exists for order_id={order_id}."
    )


def get_return_risk_products(
    *,
    upload_id: str,
    uploads_dir: Path,
    artifact_dir: Path,
    refresh: bool = False,
    limit: int = 100,
    store_code: str | None = None,
    min_probability: float = 0.0,
) -> dict[str, Any]:
    artifact = get_or_create_returns_artifact(
        upload_id=upload_id,
        uploads_dir=uploads_dir,
        artifact_dir=artifact_dir,
        refresh=refresh,
    )
    risky_products = artifact.get("risky_products")
    if not isinstance(risky_products, list):
        raise ValueError(
            "Returns intelligence returns artifact is missing the risky_products list."
        )

    filtered_products = [item for item in risky_products if isinstance(item, dict)]
    if store_code:
        filtered_products = [
            item for item in filtered_products if _to_text(item.get("store_code")) == store_code
        ]
    filtered_products = [
        item
        for item in filtered_products
        if _to_float(item.get("average_return_probability"), default=0.0) >= min_probability
    ]

    result = dict(artifact)
    result["risky_products"] = filtered_products[:limit]
    result["scores"] = []
    return result
