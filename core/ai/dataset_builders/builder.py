from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .models import FeatureContract


@dataclass(slots=True)
class DatasetWindow:
    train_start: date
    train_end: date
    validation_start: date
    validation_end: date
    backtest_anchor_dates: list[date]


def build_backtest_windows(
    *,
    anchor_date: date,
    train_days: int,
    validation_days: int,
    backtest_count: int,
    step_days: int = 7,
) -> DatasetWindow:
    if train_days <= 0 or validation_days <= 0:
        raise ValueError("train_days and validation_days must be positive integers.")
    if backtest_count <= 0:
        raise ValueError("backtest_count must be positive.")

    validation_end = anchor_date
    validation_start = validation_end - timedelta(days=validation_days - 1)
    train_end = validation_start - timedelta(days=1)
    train_start = train_end - timedelta(days=train_days - 1)
    anchors = [anchor_date - timedelta(days=step_days * offset) for offset in range(backtest_count)]
    return DatasetWindow(
        train_start=train_start,
        train_end=train_end,
        validation_start=validation_start,
        validation_end=validation_end,
        backtest_anchor_dates=anchors,
    )


def build_point_in_time_dataset_sql(
    *,
    label_relation: str,
    entity_keys: list[str],
    prediction_timestamp_column: str,
    target_columns: list[str],
    contracts: list[FeatureContract],
) -> str:
    if not entity_keys:
        raise ValueError("entity_keys cannot be empty.")
    if not contracts:
        raise ValueError("At least one feature contract is required.")

    label_select_columns = entity_keys + [prediction_timestamp_column] + target_columns
    label_select = ",\n        ".join(label_select_columns)
    base_lines = [
        "with labels as (",
        "    select",
        f"        {label_select}",
        f"    from {label_relation}",
        ")",
        "select",
        "    labels.*,",
    ]

    feature_selects: list[str] = []
    join_blocks: list[str] = []
    for contract in contracts:
        alias = contract.name
        for column_name in contract.feature_columns:
            feature_selects.append(f"    {alias}.{column_name} as {alias}__{column_name}")

        join_conditions = "\n          and ".join(
            [f"feat.{key} = labels.{key}" for key in contract.serving_join_keys]
            + [f"feat.{contract.timestamp_column} <= labels.{prediction_timestamp_column}"]
        )
        join_blocks.append(
            "\n".join(
                [
                    "left join lateral (",
                    "    select",
                    f"        {', '.join(contract.feature_columns)}",
                    f"    from {contract.relation} feat",
                    f"    where {join_conditions}",
                    f"    order by feat.{contract.timestamp_column} desc",
                    "    limit 1",
                    f") as {alias} on true",
                ]
            )
        )

    base_lines.append(",\n".join(feature_selects))
    base_lines.append("from labels")
    base_lines.extend(join_blocks)
    return "\n".join(base_lines) + "\n"
