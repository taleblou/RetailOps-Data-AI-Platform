from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from .models import FeatureContract


@dataclass(slots=True)
class FreshnessResult:
    feature_name: str
    age_hours: float | None
    status: str
    checked_at: datetime
    message: str


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def evaluate_feature_freshness(
    contract: FeatureContract,
    *,
    last_loaded_at: datetime | None,
    checked_at: datetime | None = None,
) -> FreshnessResult:
    check_time = _ensure_aware(checked_at or datetime.now(UTC))
    if last_loaded_at is None:
        return FreshnessResult(
            feature_name=contract.name,
            age_hours=None,
            status="missing",
            checked_at=check_time,
            message="No successful load timestamp is available.",
        )

    observed_at = _ensure_aware(last_loaded_at)
    age_hours = round((check_time - observed_at).total_seconds() / 3600, 2)
    if age_hours <= contract.freshness.warn_after_hours:
        status = "fresh"
    elif age_hours <= contract.freshness.error_after_hours:
        status = "warn"
    else:
        status = "stale"

    return FreshnessResult(
        feature_name=contract.name,
        age_hours=age_hours,
        status=status,
        checked_at=check_time,
        message=(
            f"Feature '{contract.name}' is {status}; age={age_hours}h, "
            f"warn_after={contract.freshness.warn_after_hours}h, "
            f"error_after={contract.freshness.error_after_hours}h."
        ),
    )


def evaluate_feature_freshness_map(
    contracts: list[FeatureContract],
    *,
    last_loaded_at_by_feature: dict[str, datetime | None],
    checked_at: datetime | None = None,
) -> dict[str, FreshnessResult]:
    return {
        contract.name: evaluate_feature_freshness(
            contract,
            last_loaded_at=last_loaded_at_by_feature.get(contract.name),
            checked_at=checked_at,
        )
        for contract in contracts
    }
