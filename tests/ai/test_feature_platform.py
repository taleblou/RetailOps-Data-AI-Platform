from __future__ import annotations

from datetime import UTC, date, datetime

from core.ai.dataset_builders import (
    build_backtest_windows,
    build_point_in_time_dataset_sql,
    evaluate_feature_freshness,
    load_feature_contracts,
)


def test_load_feature_contracts_includes_phase_9_assets() -> None:
    contracts = load_feature_contracts()
    names = {contract.name for contract in contracts}
    assert {
        "product_demand_daily",
        "inventory_position_daily",
        "shipment_delay_features",
        "stockout_features",
        "customer_return_features",
    }.issubset(names)


def test_dataset_builder_generates_point_in_time_sql() -> None:
    contracts = [
        contract
        for contract in load_feature_contracts()
        if contract.name in {"product_demand_daily", "inventory_position_daily"}
    ]
    sql = build_point_in_time_dataset_sql(
        label_relation="predictions.forecast_training_labels",
        entity_keys=["store_id", "product_id"],
        prediction_timestamp_column="prediction_timestamp",
        target_columns=["target_units"],
        contracts=contracts,
    )
    assert "left join lateral" in sql
    assert "feat.feature_date <= labels.prediction_timestamp" in sql
    assert "product_demand_daily__units_sold_1d" in sql
    assert "inventory_position_daily__available_qty" in sql


def test_backtest_window_builder_returns_train_and_validation_ranges() -> None:
    window = build_backtest_windows(
        anchor_date=date(2026, 3, 26),
        train_days=90,
        validation_days=14,
        backtest_count=3,
    )
    assert window.train_start < window.train_end < window.validation_start <= window.validation_end
    assert len(window.backtest_anchor_dates) == 3


def test_freshness_checker_reports_stale_contracts() -> None:
    contract = next(
        contract
        for contract in load_feature_contracts()
        if contract.name == "shipment_delay_features"
    )
    result = evaluate_feature_freshness(
        contract,
        last_loaded_at=datetime(2026, 3, 25, 0, 0, tzinfo=UTC),
        checked_at=datetime(2026, 3, 26, 12, 0, tzinfo=UTC),
    )
    assert result.status == "stale"
    assert result.age_hours is not None
    assert result.age_hours > contract.freshness.error_after_hours
