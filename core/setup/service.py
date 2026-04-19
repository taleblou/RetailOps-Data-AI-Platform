# Project:      RetailOps Data & AI Platform
# Module:       core.setup
# File:         service.py
# Path:         core/setup/service.py
#
# Summary:      Implements the setup service layer and business logic.
# Purpose:      Encapsulates core processing and artifact generation for setup workflows.
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
#   - Main types: None.
#   - Key APIs: create_setup_session, get_setup_session, update_setup_store, configure_setup_source, test_setup_source_connection, save_setup_mapping, ...
#   - Dependencies: __future__, csv, json, uuid, datetime, pathlib, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.ingestion.base.mapper import ColumnMapper
from core.ingestion.base.models import SourceCreateRequest, SourceStatus, SourceType
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.registry import ConnectorRegistry
from core.ingestion.base.repository import RepositoryProtocol
from core.ingestion.base.state_store import StateStore
from core.transformations.service import run_first_transform
from modules.analytics_kpi.service import publish_first_dashboard
from modules.forecasting.service import get_or_create_batch_forecast_artifact, run_first_forecast
from modules.ml_registry.service import run_model_registry

SETUP_ARTIFACT_DIR = Path("data/artifacts/setup")
SETUP_SESSION_DIR = SETUP_ARTIFACT_DIR / "sessions"
SETUP_UPLOAD_DIR = Path("data/uploads")
SETUP_TRANSFORM_DIR = Path("data/artifacts/transforms")
SETUP_DASHBOARD_DIR = Path("data/artifacts/dashboards")
SETUP_FORECAST_DIR = Path("data/artifacts/forecasts")
SETUP_MODEL_REGISTRY_DIR = Path("data/artifacts/model_registry")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETUP_DEMO_DIR = PROJECT_ROOT / "data/demo_csv"
SETUP_DEMO_SOURCE = SETUP_DEMO_DIR / "sample_orders_easy_csv_150.csv"
SUPPORTED_DELIMITERS = ",;\t|"
REQUIRED_FIELDS = ["order_id", "order_date", "sku", "quantity"]
TYPE_HINTS = {
    "order_id": "string",
    "order_date": "datetime",
    "customer_id": "string",
    "sku": "string",
    "quantity": "integer",
    "unit_price": "float",
    "store_code": "string",
}
DEFAULT_MODULES = ["analytics_kpi", "forecasting", "monitoring"]
STEP_DEFINITIONS = [
    ("create_store", "Create store"),
    ("choose_source", "Choose source"),
    ("test_connection", "Test connection"),
    ("map_fields", "Map fields"),
    ("first_import", "First import"),
    ("first_dbt_run", "First dbt run"),
    ("enable_modules", "Enable modules"),
    ("first_model_training", "First model training"),
    ("publish_dashboards", "Publish dashboards"),
]


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _safe_store_code(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() else "-" for character in value.strip().upper()
    )
    cleaned = cleaned.strip("-")
    return cleaned or "STORE-DEMO"


def _safe_filename(filename: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in ".-_" else "_"
        for character in filename.strip()
    )
    return cleaned or "setup_source.csv"


def _sniff_delimiter(sample_text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=SUPPORTED_DELIMITERS)
    except csv.Error:
        return ","
    return getattr(dialect, "delimiter", ",")


def _step_template(key: str, label: str) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "status": "pending",
        "attempts": 0,
        "message": None,
        "artifact_path": None,
        "last_updated_at": None,
    }


def _initial_steps() -> dict[str, dict[str, Any]]:
    return {key: _step_template(key, label) for key, label in STEP_DEFINITIONS}


def _ensure_dirs(
    *,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
    transform_dir: Path = SETUP_TRANSFORM_DIR,
    dashboard_dir: Path = SETUP_DASHBOARD_DIR,
    forecast_dir: Path = SETUP_FORECAST_DIR,
    model_registry_dir: Path = SETUP_MODEL_REGISTRY_DIR,
) -> None:
    (setup_dir / "sessions").mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    transform_dir.mkdir(parents=True, exist_ok=True)
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    forecast_dir.mkdir(parents=True, exist_ok=True)
    model_registry_dir.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str, setup_dir: Path) -> Path:
    return setup_dir / "sessions" / f"{session_id}.json"


def _metadata_path(session_id: str, uploads_dir: Path) -> Path:
    return uploads_dir / f"{session_id}.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON payload at {path}")
    return payload


def _append_log(session: dict[str, Any], *, step: str, message: str, level: str = "info") -> None:
    session.setdefault("logs", []).append(
        {
            "timestamp": _utc_now(),
            "step": step,
            "level": level,
            "message": message,
        }
    )


def _mark_step(
    session: dict[str, Any],
    *,
    step_key: str,
    status: str,
    message: str,
    artifact_path: str | None = None,
) -> None:
    step = session["steps"][step_key]
    step["attempts"] = int(step.get("attempts", 0)) + 1
    step["status"] = status
    step["message"] = message
    step["artifact_path"] = artifact_path
    step["last_updated_at"] = _utc_now()
    session["updated_at"] = _utc_now()
    _append_log(
        session,
        step=step_key,
        message=f"{message} (attempt {step['attempts']}).",
        level="error" if status == "failed" else "info",
    )


def _progress_percent(session: dict[str, Any]) -> int:
    total = len(STEP_DEFINITIONS)
    completed = sum(1 for step in session["steps"].values() if step["status"] == "done")
    return int(round((completed / total) * 100)) if total else 0


def _next_step(session: dict[str, Any]) -> str | None:
    for key, _label in STEP_DEFINITIONS:
        if session["steps"][key]["status"] != "done":
            return key
    return None


def _session_response(session: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(json.dumps(session))
    payload["progress_percent"] = _progress_percent(session)
    payload["next_step"] = _next_step(session)
    payload["steps"] = list(payload["steps"].values())
    return payload


def _load_session(session_id: str, setup_dir: Path = SETUP_ARTIFACT_DIR) -> dict[str, Any]:
    path = _session_path(session_id, setup_dir)
    if not path.exists():
        raise FileNotFoundError(f"Setup session was not found: {session_id}")
    return _read_json(path)


def _save_session(session: dict[str, Any], setup_dir: Path = SETUP_ARTIFACT_DIR) -> dict[str, Any]:
    _ensure_dirs(setup_dir=setup_dir)
    _write_json(_session_path(str(session["session_id"]), setup_dir), session)
    return session


def _build_sample_orders_csv(target_path: Path) -> None:
    if not SETUP_DEMO_SOURCE.exists():
        raise FileNotFoundError(
            "The sample data mode needs data/demo_csv/sample_orders_easy_csv_150.csv."
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with SETUP_DEMO_SOURCE.open("r", encoding="utf-8", newline="") as source_handle:
        reader = csv.DictReader(source_handle)
        fieldnames = [
            "Order ID",
            "Order Date",
            "Customer ID",
            "Product ID",
            "SKU",
            "Quantity",
            "Unit Price",
            "Store Code",
            "Category",
            "Product Group",
            "Available Qty",
        ]
        with target_path.open("w", encoding="utf-8", newline="") as target_handle:
            writer = csv.DictWriter(target_handle, fieldnames=fieldnames)
            writer.writeheader()
            for index, row in enumerate(reader, start=1):
                sku = str(row.get("SKU") or "SKU-0000")
                suffix = sku.split("-")[-1]
                category_number = (int(suffix) if suffix.isdigit() else index) % 5 + 1
                available_qty = 20 + ((int(row.get("Quantity") or 0) + index) % 40)
                writer.writerow(
                    {
                        "Order ID": row.get("Order ID", ""),
                        "Order Date": row.get("Order Date", ""),
                        "Customer ID": row.get("Customer ID", ""),
                        "Product ID": f"PROD-{suffix}",
                        "SKU": sku,
                        "Quantity": row.get("Quantity", ""),
                        "Unit Price": row.get("Unit Price", ""),
                        "Store Code": row.get("Store Code", "ST-01"),
                        "Category": f"Category-{category_number}",
                        "Product Group": f"Group-{category_number}",
                        "Available Qty": available_qty,
                    }
                )


def _read_csv_preview(file_path: Path, *, encoding: str = "utf-8") -> tuple[str, list[str]]:
    sample_text = file_path.read_text(encoding=encoding)[:4096]
    delimiter = _sniff_delimiter(sample_text)
    with file_path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        columns = [str(column) for column in (reader.fieldnames or [])]
    return delimiter, columns


def _ensure_upload_metadata(
    session: dict[str, Any],
    *,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
) -> dict[str, Any]:
    _ensure_dirs(setup_dir=setup_dir, uploads_dir=uploads_dir)
    session_id = str(session["session_id"])
    metadata_file = _metadata_path(session_id, uploads_dir)
    source = session.get("source") or {}
    config = dict(source.get("config") or {})

    if bool(session.get("sample_mode")) and source.get("type") == SourceType.CSV.value:
        sample_name = _safe_filename(f"{session_id}_sample_orders_setup.csv")
        sample_path = uploads_dir / sample_name
        if not sample_path.exists():
            _build_sample_orders_csv(sample_path)
        config["file_path"] = str(sample_path)
        config.setdefault("delimiter", ",")
        config.setdefault("encoding", "utf-8")
        session.setdefault("source", {})["config"] = config

    file_path_value = str(config.get("file_path") or "").strip()
    if not file_path_value:
        raise ValueError(
            "CSV source configuration must include file_path before mapping can start."
        )

    file_path = Path(file_path_value)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file does not exist: {file_path}")

    encoding = str(config.get("encoding") or "utf-8")
    delimiter, columns = _read_csv_preview(file_path, encoding=encoding)
    metadata = {
        "upload_id": session_id,
        "filename": file_path.name,
        "stored_path": str(file_path),
        "delimiter": str(config.get("delimiter") or delimiter),
        "encoding": encoding,
        "columns": columns,
        "mapping": dict(session.get("mapping") or {}),
    }
    if isinstance(session.get("transform_summary"), dict):
        metadata["transform_summary"] = dict(session["transform_summary"])
    if isinstance(session.get("dashboard_summary"), dict):
        metadata["dashboard_summary"] = dict(session["dashboard_summary"])
    if isinstance(session.get("forecast_summary"), dict):
        metadata["forecast_summary"] = dict(session["forecast_summary"])

    _write_json(metadata_file, metadata)
    session.setdefault("artifacts", {})["upload_metadata_path"] = str(metadata_file)
    _save_session(session, setup_dir)
    return metadata


def _create_or_get_source(
    session: dict[str, Any],
    *,
    repository: RepositoryProtocol,
) -> Any:
    source = session.get("source") or {}
    source_id = source.get("source_id")
    if isinstance(source_id, int):
        existing = repository.get_source(source_id)
        if existing is not None:
            return existing

    source_type_text = str(source.get("type") or "").strip().lower()
    if not source_type_text:
        raise ValueError("Choose a source before testing the connection.")

    request = SourceCreateRequest(
        name=str(source.get("name") or f"{session['session_id']}-source"),
        type=SourceType(source_type_text),
        config=dict(source.get("config") or {}),
    )
    created = repository.create_source(request)
    session.setdefault("source", {})["source_id"] = created.source_id
    return created


def create_setup_session(
    *,
    store_name: str | None = None,
    store_code: str | None = None,
    sample_mode: bool = False,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
) -> dict[str, Any]:
    _ensure_dirs(setup_dir=setup_dir)
    session_id = f"setup_{uuid.uuid4().hex[:12]}"
    session = {
        "session_id": session_id,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "sample_mode": sample_mode,
        "store": {
            "name": str(store_name or "").strip(),
            "code": _safe_store_code(store_code or ""),
            "currency": "EUR",
            "timezone": "Europe/Helsinki",
        },
        "source": {
            "type": "",
            "name": "",
            "config": {},
            "source_id": None,
            "discovered_columns": [],
        },
        "mapping": {},
        "enabled_modules": [],
        "artifacts": {},
        "transform_summary": None,
        "dashboard_summary": None,
        "forecast_summary": None,
        "training_summary": None,
        "steps": _initial_steps(),
        "logs": [],
    }
    if store_name and store_code:
        _mark_step(
            session,
            step_key="create_store",
            status="done",
            message=f"Store '{store_name}' was created.",
        )
    else:
        _append_log(
            session,
            step="session",
            message="Setup session created and waiting for the store details.",
        )
    _save_session(session, setup_dir)
    return _session_response(session)


def get_setup_session(
    *,
    session_id: str,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
) -> dict[str, Any]:
    return _session_response(_load_session(session_id, setup_dir))


def update_setup_store(
    *,
    session_id: str,
    store_name: str,
    store_code: str,
    currency: str = "EUR",
    timezone: str = "Europe/Helsinki",
    setup_dir: Path = SETUP_ARTIFACT_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    session["store"] = {
        "name": store_name.strip(),
        "code": _safe_store_code(store_code),
        "currency": currency.strip() or "EUR",
        "timezone": timezone.strip() or "Europe/Helsinki",
    }
    _mark_step(
        session,
        step_key="create_store",
        status="done",
        message=f"Store '{store_name.strip()}' was saved.",
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def configure_setup_source(
    *,
    session_id: str,
    source_type: str,
    source_name: str | None = None,
    config: dict[str, Any] | None = None,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    normalized_type = SourceType(str(source_type).strip().lower()).value
    normalized_config = dict(config or {})
    if bool(session.get("sample_mode")) and normalized_type == SourceType.CSV.value:
        normalized_config.setdefault("delimiter", ",")
        normalized_config.setdefault("encoding", "utf-8")
    session["source"] = {
        "type": normalized_type,
        "name": str(source_name or f"{session_id}-{normalized_type}").strip(),
        "config": normalized_config,
        "source_id": None,
        "discovered_columns": [],
    }
    session["mapping"] = {}
    session["transform_summary"] = None
    session["dashboard_summary"] = None
    session["forecast_summary"] = None
    session["training_summary"] = None
    _mark_step(
        session,
        step_key="choose_source",
        status="done",
        message=(
            f"Source '{session['source']['name']}' using type '{normalized_type}' was selected."
        ),
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def test_setup_source_connection(
    *,
    session_id: str,
    repository: RepositoryProtocol,
    state_store: StateStore,
    raw_loader: RawLoader,
    registry: ConnectorRegistry,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    if (session.get("source") or {}).get("type") == SourceType.CSV.value:
        _ensure_upload_metadata(session, uploads_dir=uploads_dir, setup_dir=setup_dir)
    source = _create_or_get_source(session, repository=repository)
    connector = registry.create(source, state_store, raw_loader)
    result = connector.test_connection()
    if not result.ok:
        repository.update_source_status(source.source_id, SourceStatus.FAILED)
        repository.record_error(source.source_id, "setup_test_connection", result.message)
        _mark_step(
            session,
            step_key="test_connection",
            status="failed",
            message=result.message,
        )
        _save_session(session, setup_dir)
        raise ValueError(result.message)

    repository.update_source_status(source.source_id, SourceStatus.TESTED)
    discovery = connector.discover_schema()
    session.setdefault("source", {})["discovered_columns"] = [
        item.name for item in discovery.columns
    ]
    metadata = None
    if (session.get("source") or {}).get("type") == SourceType.CSV.value:
        metadata = _ensure_upload_metadata(session, uploads_dir=uploads_dir, setup_dir=setup_dir)
        metadata["columns"] = [item.name for item in discovery.columns]
        _write_json(_metadata_path(session_id, uploads_dir), metadata)
    _mark_step(
        session,
        step_key="test_connection",
        status="done",
        message=result.message,
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def save_setup_mapping(
    *,
    session_id: str,
    mappings: dict[str, str] | None = None,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    metadata = _ensure_upload_metadata(session, uploads_dir=uploads_dir, setup_dir=setup_dir)
    columns = [str(column) for column in metadata.get("columns") or []]
    mapper = ColumnMapper()
    mapping_result = mapper.build_mapping(
        columns,
        explicit_mapping=mappings or None,
        required_columns=REQUIRED_FIELDS,
    )
    if mapping_result.missing_required:
        missing = ", ".join(mapping_result.missing_required)
        _mark_step(
            session,
            step_key="map_fields",
            status="failed",
            message=f"Required fields are still unmapped: {missing}.",
        )
        _save_session(session, setup_dir)
        raise ValueError(f"Required fields are still unmapped: {missing}.")

    resolved_mapping = {item.target: item.source for item in mapping_result.mappings}
    session["mapping"] = resolved_mapping
    metadata["mapping"] = resolved_mapping
    _write_json(_metadata_path(session_id, uploads_dir), metadata)
    _mark_step(
        session,
        step_key="map_fields",
        status="done",
        message=f"{len(resolved_mapping)} fields were mapped to the canonical model.",
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def run_setup_first_import(
    *,
    session_id: str,
    repository: RepositoryProtocol,
    state_store: StateStore,
    raw_loader: RawLoader,
    registry: ConnectorRegistry,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    metadata = _ensure_upload_metadata(session, uploads_dir=uploads_dir, setup_dir=setup_dir)
    mapping = dict(session.get("mapping") or metadata.get("mapping") or {})
    if not mapping:
        raise ValueError("Save the field mapping before importing the first dataset.")

    source = _create_or_get_source(session, repository=repository)
    connector = registry.create(source, state_store, raw_loader)
    repository.update_source_status(source.source_id, SourceStatus.RUNNING)
    import_job_id = repository.create_import_job(source.source_id, source.name, source.type)
    sync_run_id = repository.create_sync_run(source.name, None, "full")
    try:
        result = connector.run_import(
            import_job_id=import_job_id,
            sync_run_id=sync_run_id,
            explicit_mapping=mapping,
            required_columns=REQUIRED_FIELDS,
            type_hints=TYPE_HINTS,
            unique_key_columns=["order_id"],
        )
    except Exception as exc:
        repository.update_source_status(source.source_id, SourceStatus.FAILED)
        repository.finish_import_job(import_job_id, "failed", 0, 0, str(exc))
        repository.finish_sync_run(sync_run_id, "failed", 0, None, str(exc))
        repository.record_error(source.source_id, "setup_import", str(exc))
        _mark_step(
            session,
            step_key="first_import",
            status="failed",
            message=str(exc),
        )
        _save_session(session, setup_dir)
        raise

    repository.update_source_status(source.source_id, SourceStatus.READY)
    repository.finish_import_job(
        import_job_id,
        "success",
        result.rows_extracted,
        result.rows_loaded,
    )
    repository.finish_sync_run(
        sync_run_id,
        "success",
        result.rows_loaded,
        result.state.cursor_value,
    )
    summary = {
        "source_id": result.source_id,
        "import_job_id": result.import_job_id,
        "sync_run_id": result.sync_run_id,
        "rows_extracted": result.rows_extracted,
        "rows_loaded": result.rows_loaded,
        "source_status": SourceStatus.READY.value,
    }
    session.setdefault("artifacts", {})["import_summary"] = json.dumps(summary, ensure_ascii=False)
    session["import_summary"] = summary
    metadata["import_summary"] = summary
    _write_json(_metadata_path(session_id, uploads_dir), metadata)
    _mark_step(
        session,
        step_key="first_import",
        status="done",
        message=f"Imported {result.rows_loaded} rows into the raw layer.",
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def run_setup_first_transform(
    *,
    session_id: str,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
    transform_dir: Path = SETUP_TRANSFORM_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    metadata = _ensure_upload_metadata(session, uploads_dir=uploads_dir, setup_dir=setup_dir)
    if not session.get("mapping") and not metadata.get("mapping"):
        raise ValueError("The first dbt run needs a saved mapping.")
    artifact = run_first_transform(
        upload_id=session_id,
        artifact_dir=transform_dir,
        metadata=metadata,
    )
    transform_summary = artifact.to_dict()
    session["transform_summary"] = transform_summary
    session.setdefault("artifacts", {})["transform_artifact_path"] = artifact.artifact_path
    metadata["transform_summary"] = transform_summary
    _write_json(_metadata_path(session_id, uploads_dir), metadata)
    _mark_step(
        session,
        step_key="first_dbt_run",
        status="done",
        message=f"First transform completed with {artifact.output_row_count} output rows.",
        artifact_path=artifact.artifact_path,
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def enable_setup_modules(
    *,
    session_id: str,
    modules: list[str] | None = None,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    selected_modules = [item.strip() for item in (modules or DEFAULT_MODULES) if item.strip()]
    session["enabled_modules"] = selected_modules
    _mark_step(
        session,
        step_key="enable_modules",
        status="done",
        message=f"Enabled modules: {', '.join(selected_modules)}.",
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def run_setup_first_training(
    *,
    session_id: str,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
    forecast_dir: Path = SETUP_FORECAST_DIR,
    model_registry_dir: Path = SETUP_MODEL_REGISTRY_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    metadata = _ensure_upload_metadata(session, uploads_dir=uploads_dir, setup_dir=setup_dir)
    transform_summary = session.get("transform_summary") or metadata.get("transform_summary")
    if not isinstance(transform_summary, dict):
        raise ValueError("Run the first dbt transform before starting the first model training.")

    training_summary: dict[str, Any]
    try:
        batch_artifact = get_or_create_batch_forecast_artifact(
            upload_id=session_id,
            uploads_dir=uploads_dir,
            artifact_dir=forecast_dir,
            refresh=True,
        )
        training_summary = {
            "training_mode": "forecasting_batch_forecast",
            "artifact_path": str(batch_artifact.get("artifact_path") or ""),
            "model_version": str(batch_artifact.get("model_version") or "forecasting-baseline-v1"),
            "active_products": int(
                (batch_artifact.get("summary") or {}).get("active_products") or 0
            ),
        }
        artifact_path = training_summary["artifact_path"]
    except Exception:
        starter = run_first_forecast(
            upload_id=session_id,
            transform_summary=transform_summary,
            artifact_dir=forecast_dir,
        )
        training_summary = {
            "training_mode": "starter_forecast",
            "artifact_path": starter.artifact_path,
            "model_version": "daily_average_baseline",
            "active_products": 0,
        }
        artifact_path = starter.artifact_path

    registry_summary = run_model_registry(
        artifact_dir=model_registry_dir,
        refresh=False,
    ).to_dict()
    training_summary["registry_artifact_path"] = str(registry_summary.get("artifact_path") or "")
    session["training_summary"] = training_summary
    session.setdefault("artifacts", {})["training_artifact_path"] = artifact_path
    session.setdefault("artifacts", {})["model_registry_artifact_path"] = str(
        registry_summary.get("artifact_path") or ""
    )
    metadata["forecast_summary"] = training_summary
    _write_json(_metadata_path(session_id, uploads_dir), metadata)
    _mark_step(
        session,
        step_key="first_model_training",
        status="done",
        message=f"First model training completed using {training_summary['training_mode']}.",
        artifact_path=artifact_path,
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def publish_setup_dashboards(
    *,
    session_id: str,
    setup_dir: Path = SETUP_ARTIFACT_DIR,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
    dashboard_dir: Path = SETUP_DASHBOARD_DIR,
) -> dict[str, Any]:
    session = _load_session(session_id, setup_dir)
    metadata = _ensure_upload_metadata(session, uploads_dir=uploads_dir, setup_dir=setup_dir)
    transform_summary = session.get("transform_summary") or metadata.get("transform_summary")
    if not isinstance(transform_summary, dict):
        raise ValueError("Run the first dbt transform before publishing dashboards.")
    artifact = publish_first_dashboard(
        upload_id=session_id,
        filename=str(metadata.get("filename") or f"{session_id}.csv"),
        transform_summary=transform_summary,
        artifact_dir=dashboard_dir,
    )
    dashboard_summary = artifact.to_dict()
    session["dashboard_summary"] = dashboard_summary
    session.setdefault("artifacts", {})["dashboard_artifact_path"] = artifact.artifact_path
    metadata["dashboard_summary"] = dashboard_summary
    _write_json(_metadata_path(session_id, uploads_dir), metadata)
    _mark_step(
        session,
        step_key="publish_dashboards",
        status="done",
        message=f"Dashboard '{artifact.dashboard_title}' was published.",
        artifact_path=artifact.artifact_path,
    )
    _save_session(session, setup_dir)
    return _session_response(session)


def run_sample_setup(
    *,
    repository: RepositoryProtocol,
    state_store: StateStore,
    raw_loader: RawLoader,
    registry: ConnectorRegistry,
    store_name: str = "RetailOps Demo Store",
    store_code: str = "DEMO-01",
    setup_dir: Path = SETUP_ARTIFACT_DIR,
    uploads_dir: Path = SETUP_UPLOAD_DIR,
    transform_dir: Path = SETUP_TRANSFORM_DIR,
    forecast_dir: Path = SETUP_FORECAST_DIR,
    dashboard_dir: Path = SETUP_DASHBOARD_DIR,
    model_registry_dir: Path = SETUP_MODEL_REGISTRY_DIR,
) -> dict[str, Any]:
    session = create_setup_session(
        store_name=store_name,
        store_code=store_code,
        sample_mode=True,
        setup_dir=setup_dir,
    )
    session_id = str(session["session_id"])
    configure_setup_source(
        session_id=session_id,
        source_type=SourceType.CSV.value,
        source_name="Setup wizard sample CSV",
        config={},
        setup_dir=setup_dir,
    )
    test_setup_source_connection(
        session_id=session_id,
        repository=repository,
        state_store=state_store,
        raw_loader=raw_loader,
        registry=registry,
        setup_dir=setup_dir,
        uploads_dir=uploads_dir,
    )
    save_setup_mapping(
        session_id=session_id,
        mappings=None,
        setup_dir=setup_dir,
        uploads_dir=uploads_dir,
    )
    run_setup_first_import(
        session_id=session_id,
        repository=repository,
        state_store=state_store,
        raw_loader=raw_loader,
        registry=registry,
        setup_dir=setup_dir,
        uploads_dir=uploads_dir,
    )
    run_setup_first_transform(
        session_id=session_id,
        setup_dir=setup_dir,
        uploads_dir=uploads_dir,
        transform_dir=transform_dir,
    )
    enable_setup_modules(
        session_id=session_id,
        modules=DEFAULT_MODULES,
        setup_dir=setup_dir,
    )
    run_setup_first_training(
        session_id=session_id,
        setup_dir=setup_dir,
        uploads_dir=uploads_dir,
        forecast_dir=forecast_dir,
        model_registry_dir=model_registry_dir,
    )
    final_session = publish_setup_dashboards(
        session_id=session_id,
        setup_dir=setup_dir,
        uploads_dir=uploads_dir,
        dashboard_dir=dashboard_dir,
    )
    return final_session
