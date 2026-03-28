from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]

from .models import FeatureContract, FreshnessPolicy

DEFAULT_CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "feature_contracts"


def _require_mapping(data: object, *, path: Path) -> dict[str, object]:
    if not isinstance(data, dict):
        raise ValueError(f"Feature contract {path} must be a YAML mapping.")
    return data


def _require_list(data: dict[str, object], key: str, *, path: Path) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Feature contract {path} must define a string list for '{key}'.")
    return [item.strip() for item in value if item.strip()]


def _require_str(data: dict[str, object], key: str, *, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Feature contract {path} must define a non-empty string for '{key}'.")
    return value.strip()


def _require_int(
    data: dict[str, object],
    key: str,
    *,
    path: Path,
    default: int | None = None,
) -> int:
    value = data.get(key)
    if value is None:
        if default is not None:
            return default
        raise ValueError(f"Feature contract {path} must define an integer for '{key}'.")
    if isinstance(value, bool):
        raise ValueError(f"Feature contract {path} must define an integer for '{key}'.")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            try:
                return int(stripped)
            except ValueError as exc:
                raise ValueError(
                    f"Feature contract {path} must define an integer for '{key}'."
                ) from exc
    raise ValueError(f"Feature contract {path} must define an integer for '{key}'.")


def load_feature_contract(path: str | Path) -> FeatureContract:
    contract_path = Path(path)
    raw = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    data = _require_mapping(raw, path=contract_path)
    source = _require_mapping(data.get("source"), path=contract_path)
    freshness = _require_mapping(data.get("freshness"), path=contract_path)
    null_handling_raw = _require_mapping(data.get("null_handling"), path=contract_path)
    labels_raw = data.get("labels")
    labels: dict[str, object] | None = None
    if labels_raw is not None:
        labels = _require_mapping(labels_raw, path=contract_path)

    return FeatureContract(
        name=_require_str(data, "name", path=contract_path),
        description=_require_str(data, "description", path=contract_path),
        entity=_require_list(data, "entity", path=contract_path),
        relation=_require_str(source, "relation", path=contract_path),
        sql_file=_require_str(source, "sql_file", path=contract_path),
        timestamp_column=_require_str(source, "timestamp_column", path=contract_path),
        feature_columns=_require_list(data, "feature_columns", path=contract_path),
        transformation=_require_str(data, "transformation", path=contract_path),
        materialization=_require_str(data, "materialization", path=contract_path),
        freshness=FreshnessPolicy(
            warn_after_hours=_require_int(
                freshness,
                "warn_after_hours",
                path=contract_path,
                default=0,
            ),
            error_after_hours=_require_int(
                freshness,
                "error_after_hours",
                path=contract_path,
                default=0,
            ),
        ),
        null_handling={str(key): value for key, value in null_handling_raw.items()},
        owner=_require_str(data, "owner", path=contract_path),
        training_serving_parity=bool(data.get("training_serving_parity", False)),
        serving_join_keys=_require_list(data, "serving_join_keys", path=contract_path),
        leakage_prevention=_require_list(data, "leakage_prevention", path=contract_path),
        labels_relation=(
            _require_str(labels, "relation", path=contract_path) if labels is not None else None
        ),
        labels_timestamp_column=(
            _require_str(labels, "timestamp_column", path=contract_path)
            if labels is not None
            else None
        ),
        source_path=contract_path,
    )


def load_feature_contracts(directory: str | Path = DEFAULT_CONTRACTS_DIR) -> list[FeatureContract]:
    contracts_dir = Path(directory)
    contracts: list[FeatureContract] = []
    for path in sorted(contracts_dir.glob("*.yaml")):
        contracts.append(load_feature_contract(path))
    return contracts
