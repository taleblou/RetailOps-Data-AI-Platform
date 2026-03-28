from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modules.forecasting.service import PHASE10_MODEL_VERSION
from modules.returns_intelligence.service import PHASE14_MODEL_VERSION
from modules.shipment_risk.service import PHASE11_MODEL_VERSION
from modules.stockout_intelligence.service import PHASE12_MODEL_VERSION

PHASE15_ARTIFACT_NAME = "phase15_model_registry.json"
PHASE15_MODEL_REGISTRY_VERSION = "phase15-model-registry-v1"
PHASE15_ALIAS_POLICY = {
    "champion": "Current production alias. This version serves business decisions.",
    "challenger": (
        "Promotion candidate. It can replace champion only after beating "
        "the baseline and passing gates."
    ),
    "shadow": (
        "Parallel evaluation alias. It receives traffic or offline scoring for observation only."
    ),
}
PHASE15_ROLLBACK_FLOW = [
    "Every promotion stores the full previous alias map.",
    "Rollback restores the last stored alias map or an explicit target version.",
    "Rollback is required when calibration degrades or drift becomes high.",
]


class ModelRegistryNotFoundError(FileNotFoundError):
    """Raised when a requested model registry cannot be located."""


@dataclass(slots=True)
class ModelRegistryVersionArtifact:
    model_version: str
    run_id: str
    created_at: str
    source_module: str
    source_artifact: str
    stage: str
    metrics: dict[str, float]
    baseline_metrics: dict[str, float]
    calibration_error: float
    drift_score: float
    evaluation_passed: bool
    promotion_eligible: bool
    explanation_summary: str
    tags: list[str]


@dataclass(slots=True)
class ModelRegistryDetailsArtifact:
    registry_name: str
    display_name: str
    experiment_name: str
    problem_type: str
    experiment_tracking_enabled: bool
    aliases: dict[str, str]
    evaluation_contract: dict[str, Any]
    threshold_gates: list[dict[str, Any]]
    versions: list[ModelRegistryVersionArtifact]
    promotion_history: list[dict[str, Any]]
    rollback_history: list[dict[str, Any]]
    rollback_flow: list[str]


@dataclass(slots=True)
class ModelRegistrySummaryItemArtifact:
    registry_name: str
    display_name: str
    champion_version: str
    challenger_version: str
    shadow_version: str
    primary_metric: str
    optimization_direction: str
    challenger_primary_metric_value: float
    challenger_primary_metric_baseline: float
    challenger_passed: bool
    challenger_promotion_eligible: bool
    last_promotion_at: str | None


@dataclass(slots=True)
class Phase15ModelRegistryArtifact:
    registry_run_id: str
    generated_at: str
    experiment_tracking_enabled: bool
    alias_policy: dict[str, str]
    rollback_flow: list[str]
    registries: list[ModelRegistrySummaryItemArtifact]
    registry_details: list[ModelRegistryDetailsArtifact]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _make_run_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _metric_passes(
    *, direction: str, candidate: float, baseline: float, min_improvement: float
) -> bool:
    if direction == "min":
        return candidate <= baseline - min_improvement
    return candidate >= baseline + min_improvement


def _evaluate_version(
    *,
    contract: dict[str, Any],
    metrics: dict[str, float],
    baseline_metrics: dict[str, float],
    calibration_error: float,
    drift_score: float,
) -> tuple[list[dict[str, Any]], bool]:
    primary_metric = str(contract["primary_metric"])
    optimization_direction = str(contract["optimization_direction"])
    min_improvement = float(contract["min_improvement"])
    max_calibration_error = float(contract["max_calibration_error"])
    max_drift_score = float(contract["max_drift_score"])
    candidate_value = float(metrics[primary_metric])
    baseline_value = float(baseline_metrics[primary_metric])

    primary_passed = _metric_passes(
        direction=optimization_direction,
        candidate=candidate_value,
        baseline=baseline_value,
        min_improvement=min_improvement,
    )
    calibration_passed = calibration_error <= max_calibration_error
    drift_passed = drift_score <= max_drift_score
    gates = [
        {
            "name": "primary_metric_beats_baseline",
            "description": "Promote only if the primary metric beats the baseline.",
            "passed": primary_passed,
            "actual_value": candidate_value,
            "baseline_value": baseline_value,
            "threshold_value": min_improvement,
            "direction": optimization_direction,
        },
        {
            "name": "calibration_guardrail",
            "description": "Reject if calibration error is too high.",
            "passed": calibration_passed,
            "actual_value": calibration_error,
            "baseline_value": None,
            "threshold_value": max_calibration_error,
            "direction": "max",
        },
        {
            "name": "drift_guardrail",
            "description": "Reject if drift score is too high.",
            "passed": drift_passed,
            "actual_value": drift_score,
            "baseline_value": None,
            "threshold_value": max_drift_score,
            "direction": "max",
        },
    ]
    return gates, all(gate["passed"] for gate in gates)


def _find_existing_artifact(artifact_dir: Path) -> str:
    if not artifact_dir.exists():
        return "not-yet-generated"
    candidates = sorted(artifact_dir.glob("*.json"))
    if candidates:
        return str(candidates[0])
    return "not-yet-generated"


def _build_default_state(artifact_dir: Path) -> dict[str, Any]:
    forecasting_artifact = _find_existing_artifact(artifact_dir.parent / "forecasts")
    shipment_artifact = _find_existing_artifact(artifact_dir.parent / "shipment_risk")
    stockout_artifact = _find_existing_artifact(artifact_dir.parent / "stockout_risk")
    returns_artifact = _find_existing_artifact(artifact_dir.parent / "returns_risk")

    registries = {
        "forecasting_model": {
            "display_name": "Demand Forecasting Model",
            "experiment_name": "forecasting_model",
            "problem_type": "forecasting",
            "aliases": {
                "champion": PHASE10_MODEL_VERSION,
                "challenger": "phase15-forecasting-model-v2",
                "shadow": "phase15-forecasting-model-v3-shadow",
            },
            "evaluation_contract": {
                "primary_metric": "mape",
                "optimization_direction": "min",
                "min_improvement": 0.01,
                "max_calibration_error": 0.08,
                "max_drift_score": 0.25,
                "promote_rule": (
                    "Promote only if MAPE improves and interval calibration remains healthy."
                ),
            },
            "versions": [
                {
                    "model_version": PHASE10_MODEL_VERSION,
                    "run_id": "exp_forecast_phase10_001",
                    "created_at": "2026-03-25T18:15:00+00:00",
                    "source_module": "modules.forecasting",
                    "source_artifact": forecasting_artifact,
                    "stage": "production",
                    "metrics": {"mae": 12.4, "rmse": 16.1, "mape": 0.182, "bias": 0.031},
                    "baseline_metrics": {"mae": 13.6, "rmse": 17.2, "mape": 0.194, "bias": 0.041},
                    "calibration_error": 0.043,
                    "drift_score": 0.09,
                    "explanation_summary": (
                        "Stable production forecaster trained on canonical daily demand aggregates."
                    ),
                    "tags": ["phase10", "production", "champion"],
                },
                {
                    "model_version": "phase15-forecasting-model-v2",
                    "run_id": "exp_forecast_phase15_002",
                    "created_at": "2026-03-26T06:15:00+00:00",
                    "source_module": "modules.forecasting",
                    "source_artifact": forecasting_artifact,
                    "stage": "staging",
                    "metrics": {"mae": 11.7, "rmse": 15.4, "mape": 0.167, "bias": 0.019},
                    "baseline_metrics": {"mae": 13.6, "rmse": 17.2, "mape": 0.194, "bias": 0.041},
                    "calibration_error": 0.031,
                    "drift_score": 0.07,
                    "explanation_summary": (
                        "Candidate forecaster improves error and bias while "
                        "keeping interval calibration below the gate."
                    ),
                    "tags": ["phase15", "challenger", "promotable"],
                },
                {
                    "model_version": "phase15-forecasting-model-v3-shadow",
                    "run_id": "exp_forecast_phase15_003",
                    "created_at": "2026-03-26T09:30:00+00:00",
                    "source_module": "modules.forecasting",
                    "source_artifact": forecasting_artifact,
                    "stage": "shadow",
                    "metrics": {"mae": 11.8, "rmse": 15.1, "mape": 0.164, "bias": 0.018},
                    "baseline_metrics": {"mae": 13.6, "rmse": 17.2, "mape": 0.194, "bias": 0.041},
                    "calibration_error": 0.044,
                    "drift_score": 0.33,
                    "explanation_summary": (
                        "Shadow forecaster is more accurate but drift rose "
                        "above the approval limit."
                    ),
                    "tags": ["phase15", "shadow", "drift-watch"],
                },
            ],
            "promotion_history": [],
            "rollback_history": [],
        },
        "shipment_delay_model": {
            "display_name": "Shipment Delay Risk Model",
            "experiment_name": "shipment_delay_model",
            "problem_type": "binary_classification",
            "aliases": {
                "champion": PHASE11_MODEL_VERSION,
                "challenger": "phase15-shipment-delay-model-v2",
                "shadow": "phase15-shipment-delay-model-v3-shadow",
            },
            "evaluation_contract": {
                "primary_metric": "pr_auc",
                "optimization_direction": "max",
                "min_improvement": 0.015,
                "max_calibration_error": 0.05,
                "max_drift_score": 0.20,
                "promote_rule": (
                    "Promote only if PR-AUC beats the baseline and calibration remains healthy."
                ),
            },
            "versions": [
                {
                    "model_version": PHASE11_MODEL_VERSION,
                    "run_id": "exp_shipment_phase11_001",
                    "created_at": "2026-03-25T19:10:00+00:00",
                    "source_module": "modules.shipment_risk",
                    "source_artifact": shipment_artifact,
                    "stage": "production",
                    "metrics": {
                        "roc_auc": 0.79,
                        "pr_auc": 0.51,
                        "precision_at_30": 0.62,
                        "recall_at_30": 0.48,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.74,
                        "pr_auc": 0.45,
                        "precision_at_30": 0.55,
                        "recall_at_30": 0.41,
                    },
                    "calibration_error": 0.039,
                    "drift_score": 0.11,
                    "explanation_summary": (
                        "Production shipment-risk scorer with calibrated "
                        "probabilities and manual-review triggers."
                    ),
                    "tags": ["phase11", "production", "champion"],
                },
                {
                    "model_version": "phase15-shipment-delay-model-v2",
                    "run_id": "exp_shipment_phase15_002",
                    "created_at": "2026-03-26T07:05:00+00:00",
                    "source_module": "modules.shipment_risk",
                    "source_artifact": shipment_artifact,
                    "stage": "staging",
                    "metrics": {
                        "roc_auc": 0.82,
                        "pr_auc": 0.56,
                        "precision_at_30": 0.66,
                        "recall_at_30": 0.52,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.74,
                        "pr_auc": 0.45,
                        "precision_at_30": 0.55,
                        "recall_at_30": 0.41,
                    },
                    "calibration_error": 0.028,
                    "drift_score": 0.08,
                    "explanation_summary": (
                        "Challenger improves ranking quality and stays within "
                        "calibration and drift gates."
                    ),
                    "tags": ["phase15", "challenger", "promotable"],
                },
                {
                    "model_version": "phase15-shipment-delay-model-v3-shadow",
                    "run_id": "exp_shipment_phase15_003",
                    "created_at": "2026-03-26T10:15:00+00:00",
                    "source_module": "modules.shipment_risk",
                    "source_artifact": shipment_artifact,
                    "stage": "shadow",
                    "metrics": {
                        "roc_auc": 0.83,
                        "pr_auc": 0.58,
                        "precision_at_30": 0.67,
                        "recall_at_30": 0.53,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.74,
                        "pr_auc": 0.45,
                        "precision_at_30": 0.55,
                        "recall_at_30": 0.41,
                    },
                    "calibration_error": 0.081,
                    "drift_score": 0.09,
                    "explanation_summary": (
                        "Shadow model ranks better but fails the calibration guardrail."
                    ),
                    "tags": ["phase15", "shadow", "calibration-watch"],
                },
            ],
            "promotion_history": [],
            "rollback_history": [],
        },
        "stockout_model": {
            "display_name": "Stockout Intelligence Model",
            "experiment_name": "stockout_model",
            "problem_type": "binary_classification",
            "aliases": {
                "champion": PHASE12_MODEL_VERSION,
                "challenger": "phase15-stockout-model-v2",
                "shadow": "phase15-stockout-model-v3-shadow",
            },
            "evaluation_contract": {
                "primary_metric": "pr_auc",
                "optimization_direction": "max",
                "min_improvement": 0.02,
                "max_calibration_error": 0.06,
                "max_drift_score": 0.20,
                "promote_rule": (
                    "Promote only if PR-AUC improves and stockout probabilities remain calibrated."
                ),
            },
            "versions": [
                {
                    "model_version": PHASE12_MODEL_VERSION,
                    "run_id": "exp_stockout_phase12_001",
                    "created_at": "2026-03-25T20:10:00+00:00",
                    "source_module": "modules.stockout_intelligence",
                    "source_artifact": stockout_artifact,
                    "stage": "production",
                    "metrics": {
                        "roc_auc": 0.81,
                        "pr_auc": 0.59,
                        "precision_at_20": 0.71,
                        "recall_at_20": 0.49,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.75,
                        "pr_auc": 0.52,
                        "precision_at_20": 0.65,
                        "recall_at_20": 0.42,
                    },
                    "calibration_error": 0.036,
                    "drift_score": 0.10,
                    "explanation_summary": (
                        "Operational stockout model connected to urgency "
                        "scoring and lost-sales estimates."
                    ),
                    "tags": ["phase12", "production", "champion"],
                },
                {
                    "model_version": "phase15-stockout-model-v2",
                    "run_id": "exp_stockout_phase15_002",
                    "created_at": "2026-03-26T07:40:00+00:00",
                    "source_module": "modules.stockout_intelligence",
                    "source_artifact": stockout_artifact,
                    "stage": "staging",
                    "metrics": {
                        "roc_auc": 0.84,
                        "pr_auc": 0.63,
                        "precision_at_20": 0.75,
                        "recall_at_20": 0.54,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.75,
                        "pr_auc": 0.52,
                        "precision_at_20": 0.65,
                        "recall_at_20": 0.42,
                    },
                    "calibration_error": 0.029,
                    "drift_score": 0.07,
                    "explanation_summary": (
                        "Challenger improves recall for risky SKUs and "
                        "remains within threshold gates."
                    ),
                    "tags": ["phase15", "challenger", "promotable"],
                },
                {
                    "model_version": "phase15-stockout-model-v3-shadow",
                    "run_id": "exp_stockout_phase15_003",
                    "created_at": "2026-03-26T10:35:00+00:00",
                    "source_module": "modules.stockout_intelligence",
                    "source_artifact": stockout_artifact,
                    "stage": "shadow",
                    "metrics": {
                        "roc_auc": 0.85,
                        "pr_auc": 0.65,
                        "precision_at_20": 0.76,
                        "recall_at_20": 0.56,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.75,
                        "pr_auc": 0.52,
                        "precision_at_20": 0.65,
                        "recall_at_20": 0.42,
                    },
                    "calibration_error": 0.031,
                    "drift_score": 0.28,
                    "explanation_summary": (
                        "Shadow model is accurate but drift rose after a category-mix shift."
                    ),
                    "tags": ["phase15", "shadow", "drift-watch"],
                },
            ],
            "promotion_history": [],
            "rollback_history": [],
        },
        "return_risk_model": {
            "display_name": "Returns Risk Model",
            "experiment_name": "return_risk_model",
            "problem_type": "binary_classification",
            "aliases": {
                "champion": PHASE14_MODEL_VERSION,
                "challenger": "phase15-return-risk-model-v2",
                "shadow": "phase15-return-risk-model-v3-shadow",
            },
            "evaluation_contract": {
                "primary_metric": "pr_auc",
                "optimization_direction": "max",
                "min_improvement": 0.015,
                "max_calibration_error": 0.05,
                "max_drift_score": 0.20,
                "promote_rule": (
                    "Promote only if PR-AUC improves without breaking "
                    "calibration or drift thresholds."
                ),
            },
            "versions": [
                {
                    "model_version": PHASE14_MODEL_VERSION,
                    "run_id": "exp_returns_phase14_001",
                    "created_at": "2026-03-26T05:55:00+00:00",
                    "source_module": "modules.returns_intelligence",
                    "source_artifact": returns_artifact,
                    "stage": "production",
                    "metrics": {
                        "roc_auc": 0.76,
                        "pr_auc": 0.42,
                        "precision_at_20": 0.58,
                        "recall_at_20": 0.37,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.71,
                        "pr_auc": 0.36,
                        "precision_at_20": 0.53,
                        "recall_at_20": 0.31,
                    },
                    "calibration_error": 0.034,
                    "drift_score": 0.12,
                    "explanation_summary": (
                        "Production returns-risk model linked to expected "
                        "return cost and risky product views."
                    ),
                    "tags": ["phase14", "production", "champion"],
                },
                {
                    "model_version": "phase15-return-risk-model-v2",
                    "run_id": "exp_returns_phase15_002",
                    "created_at": "2026-03-26T08:20:00+00:00",
                    "source_module": "modules.returns_intelligence",
                    "source_artifact": returns_artifact,
                    "stage": "staging",
                    "metrics": {
                        "roc_auc": 0.79,
                        "pr_auc": 0.46,
                        "precision_at_20": 0.61,
                        "recall_at_20": 0.40,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.71,
                        "pr_auc": 0.36,
                        "precision_at_20": 0.53,
                        "recall_at_20": 0.31,
                    },
                    "calibration_error": 0.027,
                    "drift_score": 0.09,
                    "explanation_summary": (
                        "Challenger improves early precision on costly "
                        "return segments and passes all gates."
                    ),
                    "tags": ["phase15", "challenger", "promotable"],
                },
                {
                    "model_version": "phase15-return-risk-model-v3-shadow",
                    "run_id": "exp_returns_phase15_003",
                    "created_at": "2026-03-26T11:05:00+00:00",
                    "source_module": "modules.returns_intelligence",
                    "source_artifact": returns_artifact,
                    "stage": "shadow",
                    "metrics": {
                        "roc_auc": 0.80,
                        "pr_auc": 0.48,
                        "precision_at_20": 0.62,
                        "recall_at_20": 0.41,
                    },
                    "baseline_metrics": {
                        "roc_auc": 0.71,
                        "pr_auc": 0.36,
                        "precision_at_20": 0.53,
                        "recall_at_20": 0.31,
                    },
                    "calibration_error": 0.064,
                    "drift_score": 0.11,
                    "explanation_summary": (
                        "Shadow model improves ranking but calibration drift would block promotion."
                    ),
                    "tags": ["phase15", "shadow", "calibration-watch"],
                },
            ],
            "promotion_history": [],
            "rollback_history": [],
        },
    }

    state: dict[str, Any] = {
        "registry_run_id": _make_run_id("phase15_registry"),
        "generated_at": _utc_now(),
        "experiment_tracking_enabled": True,
        "alias_policy": PHASE15_ALIAS_POLICY,
        "rollback_flow": PHASE15_ROLLBACK_FLOW,
        "registries": registries,
    }

    for registry in state["registries"].values():
        contract = registry["evaluation_contract"]
        for version in registry["versions"]:
            gates, passed = _evaluate_version(
                contract=contract,
                metrics=version["metrics"],
                baseline_metrics=version["baseline_metrics"],
                calibration_error=float(version["calibration_error"]),
                drift_score=float(version["drift_score"]),
            )
            version["evaluation_passed"] = passed
            version["promotion_eligible"] = passed
            version["threshold_gates"] = gates
    return state


def _artifact_path(artifact_dir: Path) -> Path:
    return artifact_dir / PHASE15_ARTIFACT_NAME


def _load_or_create_state(artifact_dir: Path, *, refresh: bool = False) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = _artifact_path(artifact_dir)
    if refresh or not artifact_path.exists():
        state = _build_default_state(artifact_dir)
        artifact_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return state
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def _save_state(artifact_dir: Path, state: dict[str, Any]) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    state["generated_at"] = _utc_now()
    _artifact_path(artifact_dir).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _get_registry(state: dict[str, Any], registry_name: str) -> dict[str, Any]:
    registries = state.get("registries")
    if not isinstance(registries, dict) or registry_name not in registries:
        raise ModelRegistryNotFoundError(f"Model registry '{registry_name}' was not found.")
    registry = registries[registry_name]
    if not isinstance(registry, dict):
        raise ModelRegistryNotFoundError(f"Model registry '{registry_name}' is invalid.")
    return registry


def _find_version(registry: dict[str, Any], model_version: str) -> dict[str, Any]:
    versions = registry.get("versions", [])
    for version in versions:
        if isinstance(version, dict) and version.get("model_version") == model_version:
            return version
    raise ModelRegistryNotFoundError(f"Model version '{model_version}' was not found.")


def _aliases_for_version(registry: dict[str, Any], model_version: str) -> list[str]:
    aliases = registry.get("aliases", {})
    results: list[str] = []
    if isinstance(aliases, dict):
        for alias_name, alias_version in aliases.items():
            if alias_version == model_version:
                results.append(str(alias_name))
    return sorted(results)


def _details_from_registry(
    *,
    registry_name: str,
    registry: dict[str, Any],
    experiment_tracking_enabled: bool,
    rollback_flow: list[str],
) -> ModelRegistryDetailsArtifact:
    aliases = registry.get("aliases", {})
    challenger_version = str(aliases.get("challenger", ""))
    challenger = _find_version(registry, challenger_version)
    versions = [
        ModelRegistryVersionArtifact(
            model_version=str(version["model_version"]),
            run_id=str(version["run_id"]),
            created_at=str(version["created_at"]),
            source_module=str(version["source_module"]),
            source_artifact=str(version["source_artifact"]),
            stage=str(version["stage"]),
            metrics={str(key): float(value) for key, value in dict(version["metrics"]).items()},
            baseline_metrics={
                str(key): float(value) for key, value in dict(version["baseline_metrics"]).items()
            },
            calibration_error=float(version["calibration_error"]),
            drift_score=float(version["drift_score"]),
            evaluation_passed=bool(version["evaluation_passed"]),
            promotion_eligible=bool(version["promotion_eligible"]),
            explanation_summary=str(version["explanation_summary"]),
            tags=[str(tag) for tag in version.get("tags", [])]
            + _aliases_for_version(registry, str(version["model_version"])),
        )
        for version in registry.get("versions", [])
        if isinstance(version, dict)
    ]
    return ModelRegistryDetailsArtifact(
        registry_name=registry_name,
        display_name=str(registry["display_name"]),
        experiment_name=str(registry["experiment_name"]),
        problem_type=str(registry["problem_type"]),
        experiment_tracking_enabled=experiment_tracking_enabled,
        aliases={str(key): str(value) for key, value in dict(aliases).items()},
        evaluation_contract=dict(registry["evaluation_contract"]),
        threshold_gates=[dict(gate) for gate in challenger.get("threshold_gates", [])],
        versions=versions,
        promotion_history=[dict(item) for item in registry.get("promotion_history", [])],
        rollback_history=[dict(item) for item in registry.get("rollback_history", [])],
        rollback_flow=rollback_flow,
    )


def _summary_item_from_registry(
    registry_name: str, registry: dict[str, Any]
) -> ModelRegistrySummaryItemArtifact:
    aliases = registry.get("aliases", {})
    challenger = _find_version(registry, str(aliases.get("challenger", "")))
    contract = registry.get("evaluation_contract", {})
    primary_metric = str(contract.get("primary_metric", ""))
    baseline_value = float(dict(challenger["baseline_metrics"])[primary_metric])
    metric_value = float(dict(challenger["metrics"])[primary_metric])
    promotion_history = registry.get("promotion_history", [])
    last_promotion_at: str | None = None
    if promotion_history:
        last_item = promotion_history[-1]
        if isinstance(last_item, dict):
            last_promotion_at = str(last_item.get("triggered_at"))
    return ModelRegistrySummaryItemArtifact(
        registry_name=registry_name,
        display_name=str(registry["display_name"]),
        champion_version=str(aliases.get("champion", "")),
        challenger_version=str(aliases.get("challenger", "")),
        shadow_version=str(aliases.get("shadow", "")),
        primary_metric=primary_metric,
        optimization_direction=str(contract.get("optimization_direction", "max")),
        challenger_primary_metric_value=metric_value,
        challenger_primary_metric_baseline=baseline_value,
        challenger_passed=bool(challenger.get("evaluation_passed", False)),
        challenger_promotion_eligible=bool(challenger.get("promotion_eligible", False)),
        last_promotion_at=last_promotion_at,
    )


def run_phase15_model_registry(
    *,
    artifact_dir: Path = Path("data/artifacts/model_registry"),
    refresh: bool = False,
) -> Phase15ModelRegistryArtifact:
    state = _load_or_create_state(artifact_dir, refresh=refresh)
    registries = state.get("registries", {})
    summary_items = [
        _summary_item_from_registry(name, registry)
        for name, registry in registries.items()
        if isinstance(registry, dict)
    ]
    details = [
        _details_from_registry(
            registry_name=name,
            registry=registry,
            experiment_tracking_enabled=bool(state.get("experiment_tracking_enabled", False)),
            rollback_flow=[str(item) for item in state.get("rollback_flow", [])],
        )
        for name, registry in registries.items()
        if isinstance(registry, dict)
    ]
    return Phase15ModelRegistryArtifact(
        registry_run_id=str(state["registry_run_id"]),
        generated_at=str(state["generated_at"]),
        experiment_tracking_enabled=bool(state.get("experiment_tracking_enabled", False)),
        alias_policy={
            str(key): str(value) for key, value in dict(state.get("alias_policy", {})).items()
        },
        rollback_flow=[str(item) for item in state.get("rollback_flow", [])],
        registries=summary_items,
        registry_details=details,
        artifact_path=str(_artifact_path(artifact_dir)),
    )


def get_phase15_registry_summary(
    *,
    artifact_dir: Path = Path("data/artifacts/model_registry"),
    refresh: bool = False,
) -> dict[str, Any]:
    artifact = run_phase15_model_registry(artifact_dir=artifact_dir, refresh=refresh)
    payload = artifact.to_dict()
    payload.pop("registry_details", None)
    return payload


def get_phase15_registry_details(
    *,
    registry_name: str,
    artifact_dir: Path = Path("data/artifacts/model_registry"),
    refresh: bool = False,
) -> dict[str, Any]:
    state = _load_or_create_state(artifact_dir, refresh=refresh)
    registry = _get_registry(state, registry_name)
    details = _details_from_registry(
        registry_name=registry_name,
        registry=registry,
        experiment_tracking_enabled=bool(state.get("experiment_tracking_enabled", False)),
        rollback_flow=[str(item) for item in state.get("rollback_flow", [])],
    )
    payload = asdict(details)
    payload["artifact_path"] = str(_artifact_path(artifact_dir))
    return payload


def promote_phase15_registry_model(
    *,
    registry_name: str,
    candidate_alias: str = "challenger",
    artifact_dir: Path = Path("data/artifacts/model_registry"),
) -> dict[str, Any]:
    state = _load_or_create_state(artifact_dir, refresh=False)
    registry = _get_registry(state, registry_name)
    aliases = registry.get("aliases", {})
    if not isinstance(aliases, dict) or candidate_alias not in aliases:
        raise ValueError(
            f"Alias '{candidate_alias}' is not configured for registry '{registry_name}'."
        )
    candidate_version = str(aliases[candidate_alias])
    candidate = _find_version(registry, candidate_version)
    if not bool(candidate.get("promotion_eligible", False)):
        raise ValueError(
            "Model version "
            f"'{candidate_version}' did not pass the evaluation contract "
            "and cannot be promoted."
        )

    previous_aliases = {str(key): str(value) for key, value in aliases.items()}
    previous_champion = previous_aliases.get("champion", "")
    updated_aliases = dict(previous_aliases)
    updated_aliases["champion"] = candidate_version
    if previous_champion and previous_champion != candidate_version:
        updated_aliases["challenger"] = previous_champion
    registry["aliases"] = updated_aliases

    event = {
        "event_id": _make_run_id("promotion"),
        "triggered_at": _utc_now(),
        "candidate_alias": candidate_alias,
        "promoted_version": candidate_version,
        "from_aliases": previous_aliases,
        "to_aliases": updated_aliases,
        "reason": (
            "Promotion approved because the model beat the baseline and passed all threshold gates."
        ),
    }
    registry.setdefault("promotion_history", []).append(event)
    _save_state(artifact_dir, state)
    return get_phase15_registry_details(
        registry_name=registry_name, artifact_dir=artifact_dir, refresh=False
    )


def rollback_phase15_registry_model(
    *,
    registry_name: str,
    artifact_dir: Path = Path("data/artifacts/model_registry"),
    target_version: str | None = None,
) -> dict[str, Any]:
    state = _load_or_create_state(artifact_dir, refresh=False)
    registry = _get_registry(state, registry_name)
    aliases = registry.get("aliases", {})
    if not isinstance(aliases, dict):
        raise ValueError(f"Registry '{registry_name}' has invalid aliases.")

    previous_aliases = {str(key): str(value) for key, value in aliases.items()}
    if target_version is None:
        promotion_history = registry.get("promotion_history", [])
        if not promotion_history:
            raise ValueError(
                f"Registry '{registry_name}' has no stored promotion event to roll back."
            )
        last_promotion = promotion_history[-1]
        if not isinstance(last_promotion, dict):
            raise ValueError(f"Registry '{registry_name}' has invalid promotion history.")
        restored_aliases = {
            str(key): str(value)
            for key, value in dict(last_promotion.get("from_aliases", {})).items()
        }
        restored_from_event_id = str(last_promotion.get("event_id", ""))
        reason = "Rollback restored the alias map saved before the last promotion."
    else:
        _find_version(registry, target_version)
        restored_aliases = dict(previous_aliases)
        restored_aliases["champion"] = target_version
        current_champion = previous_aliases.get("champion", "")
        if current_champion and current_champion != target_version:
            restored_aliases["challenger"] = current_champion
        restored_from_event_id = "manual-target-version"
        reason = f"Rollback moved champion to explicit version '{target_version}'."

    registry["aliases"] = restored_aliases
    rollback_event = {
        "event_id": _make_run_id("rollback"),
        "triggered_at": _utc_now(),
        "from_aliases": previous_aliases,
        "to_aliases": restored_aliases,
        "restored_from_event_id": restored_from_event_id,
        "reason": reason,
    }
    registry.setdefault("rollback_history", []).append(rollback_event)
    _save_state(artifact_dir, state)
    return get_phase15_registry_details(
        registry_name=registry_name, artifact_dir=artifact_dir, refresh=False
    )
