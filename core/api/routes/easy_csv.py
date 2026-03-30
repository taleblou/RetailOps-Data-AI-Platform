# Project:      RetailOps Data & AI Platform
# Module:       core.api.routes
# File:         easy_csv.py
# Path:         core/api/routes/easy_csv.py
#
# Summary:      Defines public API routes and request handling for the API routes surface.
# Purpose:      Exposes HTTP entry points for API routes workflows.
# Scope:        public API
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
#   - Key APIs: router, run_first_transform, run_first_forecast,
#     wizard_home, wizard_detail, wizard_upload, ...
#   - Dependencies: __future__, csv, html, json, re, uuid, ...
#   - Constraints: Public request and response behavior should remain
#     backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import html
import json
import re
import uuid
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse

from core.api.schemas.easy_csv import (
    EasyCsvDashboardCard,
    EasyCsvDashboardResponse,
    EasyCsvForecastDailyPoint,
    EasyCsvForecastHorizon,
    EasyCsvForecastResponse,
    EasyCsvImportResponse,
    EasyCsvMappingRequest,
    EasyCsvMappingResponse,
    EasyCsvPreviewResponse,
    EasyCsvTransformDailyMetric,
    EasyCsvTransformResponse,
    EasyCsvValidationIssue,
    EasyCsvValidationResponse,
)
from core.ingestion.base.mapper import ColumnMapper
from core.ingestion.base.models import SourceCreateRequest, SourceStatus, SourceType
from modules.analytics_kpi.service import publish_first_dashboard

router = APIRouter(prefix="/easy-csv", tags=["easy-csv"])

UPLOAD_DIR = Path("data/uploads")
PREVIEW_LIMIT = 10
SUPPORTED_DELIMITERS = ",;\t|"
CANONICAL_FIELDS = [
    "order_id",
    "order_date",
    "customer_id",
    "sku",
    "quantity",
    "unit_price",
    "store_code",
]
REQUIRED_FIELDS = ["order_id", "order_date", "sku", "quantity"]
TYPE_HINTS = {
    "order_id": "string",
    "order_date": "datetime",
    "sku": "string",
    "quantity": "integer",
    "unit_price": "float",
}
UNIQUE_KEY_COLUMNS = ["order_id"]
TRANSFORM_ARTIFACT_DIR = Path("data/artifacts/transforms")
DASHBOARD_ARTIFACT_DIR = Path("data/artifacts/dashboards")
FORECAST_ARTIFACT_DIR = Path("data/artifacts/forecasts")


def _load_service_callable(module_path: str, attribute_name: str) -> Callable[..., Any]:
    module = import_module(module_path)
    candidate = getattr(module, attribute_name, None)
    if not callable(candidate):
        raise RuntimeError(f"Expected callable '{attribute_name}' in module '{module_path}'.")
    return candidate


def run_first_transform(*args: Any, **kwargs: Any) -> Any:
    return _load_service_callable(
        "core.transformations.service",
        "run_first_transform",
    )(*args, **kwargs)


def run_first_forecast(*args: Any, **kwargs: Any) -> Any:
    return _load_service_callable(
        "modules.forecasting.service",
        "run_first_forecast",
    )(*args, **kwargs)


WIZARD_CSS = "\n".join(
    [
        "body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 1100px; ",
        "color: #1f2937; }",
        "h1, h2, h3 { color: #0f172a; }",
        ".muted { color: #475569; }",
        ".panel { border: 1px solid #dbe4ee; border-radius: 14px; ",
        "padding: 1rem 1.25rem; margin-bottom: 1rem; }",
        ".grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }",
        ".badge { border-radius: 999px; padding: 0.2rem 0.6rem; font-size: 0.85rem; }",
        ".done { background: #dcfce7; color: #166534; }",
        ".pending { background: #e2e8f0; color: #334155; }",
        ".flash { background: #fef3c7; border: 1px solid #f59e0b; ",
        "border-radius: 12px; padding: 0.75rem 1rem; }",
        "table { width: 100%; border-collapse: collapse; margin-top: 0.75rem; }",
        "th, td { border: 1px solid #dbe4ee; padding: 0.55rem; text-align: left; ",
        "vertical-align: top; }",
        "ul.steps { list-style: none; padding: 0; margin: 0; }",
        "ul.steps li { display: flex; justify-content: space-between; ",
        "border-bottom: 1px solid #e2e8f0; padding: 0.45rem 0; }",
        "button { background: #2563eb; color: white; border: 0; ",
        "border-radius: 10px; padding: 0.6rem 0.9rem; cursor: pointer; }",
        ".secondary { background: #0f172a; }",
        ".link { color: #2563eb; text-decoration: none; }",
        "select { width: 100%; padding: 0.45rem; }",
        ".card-grid { display: grid; ",
        "grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.75rem; }",
        ".card { border: 1px solid #dbe4ee; border-radius: 12px; ",
        "padding: 0.8rem; background: #f8fafc; }",
        ".card-title { font-size: 0.9rem; color: #475569; }",
        ".card-value { font-size: 1.35rem; font-weight: 700; margin: 0.4rem 0; }",
        ".card-note { font-size: 0.85rem; color: #64748b; }",
        "code { background: #f1f5f9; padding: 0.1rem 0.35rem; border-radius: 6px; }",
    ]
)


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename.strip())
    return cleaned or "upload.csv"


def _metadata_path(upload_id: str) -> Path:
    return UPLOAD_DIR / f"{upload_id}.json"


def _write_metadata(payload: dict[str, Any]) -> None:
    path = _metadata_path(payload["upload_id"])
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _read_metadata(upload_id: str) -> dict[str, Any]:
    path = _metadata_path(upload_id)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found.",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _detect_delimiter(sample_text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=SUPPORTED_DELIMITERS)
    except csv.Error:
        return ","
    return getattr(dialect, "delimiter", ",")


def _read_rows(
    *,
    stored_path: Path,
    delimiter: str,
    encoding: str,
) -> tuple[list[str], list[dict[str, str | None]]]:
    with stored_path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        columns = [str(column) for column in (reader.fieldnames or [])]
        rows: list[dict[str, str | None]] = []
        for row in reader:
            normalized_row: dict[str, str | None] = {}
            for key, value in row.items():
                if key is None:
                    continue
                normalized_row[str(key)] = value if value is None else str(value)
            rows.append(normalized_row)
    return columns, rows


def _preview_rows(rows: list[dict[str, str | None]]) -> list[dict[str, str | None]]:
    return rows[:PREVIEW_LIMIT]


def _build_preview(
    *,
    upload_id: str,
    filename: str,
    stored_path: Path,
    delimiter: str,
    encoding: str,
) -> EasyCsvPreviewResponse:
    columns, rows = _read_rows(
        stored_path=stored_path,
        delimiter=delimiter,
        encoding=encoding,
    )
    return EasyCsvPreviewResponse(
        upload_id=upload_id,
        filename=filename,
        stored_path=str(stored_path),
        delimiter=delimiter,
        encoding=encoding,
        columns=columns,
        sample_rows=_preview_rows(rows),
        preview_row_count=min(len(rows), PREVIEW_LIMIT),
    )


def _mapping_result_for_upload(metadata: dict[str, Any]) -> tuple[list[dict[str, Any]], Any]:
    mapping = metadata.get("mapping") or {}
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No mapping saved for this upload.",
        )

    stored_path = Path(metadata["stored_path"])
    columns, rows = _read_rows(
        stored_path=stored_path,
        delimiter=metadata["delimiter"],
        encoding=metadata["encoding"],
    )
    mapper = ColumnMapper()
    mapping_result = mapper.build_mapping(
        columns,
        explicit_mapping=mapping,
        required_columns=REQUIRED_FIELDS,
    )
    mapped_rows = mapper.apply_mapping(rows, mapping_result)
    return mapped_rows, mapping_result


def _validate_mapping_payload(columns: list[str], payload: EasyCsvMappingRequest) -> None:
    unknown_targets = [target for target in payload.mappings if target not in CANONICAL_FIELDS]
    if unknown_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown canonical fields in mapping: {unknown_targets}",
        )

    unknown_sources = [source for source in payload.mappings.values() if source not in columns]
    if unknown_sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source columns in mapping: {unknown_sources}",
        )

    sources = list(payload.mappings.values())
    if len(sources) != len(set(sources)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Each source column may map to only one canonical field.",
        )


def _build_validation_response(metadata: dict[str, Any]) -> EasyCsvValidationResponse:
    mapped_rows, mapping_result = _mapping_result_for_upload(metadata)
    from core.ingestion.base.validator import DataValidator

    validation = DataValidator().validate(
        mapped_rows,
        required_columns=REQUIRED_FIELDS,
        type_hints=TYPE_HINTS,
        unique_key_columns=UNIQUE_KEY_COLUMNS,
    )
    warnings = [
        EasyCsvValidationIssue.model_validate(issue.model_dump()) for issue in validation.warnings
    ]
    warnings.extend(
        [
            EasyCsvValidationIssue(
                level="warning",
                code="unmapped_columns",
                message="One or more source columns were left unmapped.",
                value=mapping_result.unmapped_source_columns,
            )
        ]
        if mapping_result.unmapped_source_columns
        else []
    )
    blocking_errors = [
        EasyCsvValidationIssue.model_validate(issue.model_dump()) for issue in validation.errors
    ]
    if mapping_result.missing_required:
        blocking_errors.insert(
            0,
            EasyCsvValidationIssue(
                level="error",
                code="required_mapping_missing",
                message="One or more required canonical fields are not mapped.",
                value=mapping_result.missing_required,
            ),
        )
    return EasyCsvValidationResponse(
        upload_id=metadata["upload_id"],
        filename=metadata["filename"],
        row_count=len(mapped_rows),
        mapped_columns=metadata.get("mapping") or {},
        warnings=warnings,
        blocking_errors=blocking_errors,
        can_import=not blocking_errors,
    )


def _save_upload(file_name: str, raw_bytes: bytes) -> EasyCsvPreviewResponse:
    if not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    if not file_name.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are supported in this step.",
        )

    _ensure_upload_dir()

    upload_id = uuid.uuid4().hex
    safe_name = _safe_filename(file_name)
    stored_path = UPLOAD_DIR / f"{upload_id}_{safe_name}"

    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        decoded_text = raw_bytes.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only UTF-8 CSV files are supported in this step.",
        ) from exc

    stored_path.write_bytes(raw_bytes)

    sample_text = decoded_text[:4096]
    delimiter = _detect_delimiter(sample_text)
    preview = _build_preview(
        upload_id=upload_id,
        filename=file_name,
        stored_path=stored_path,
        delimiter=delimiter,
        encoding=encoding,
    )

    metadata = {
        "upload_id": upload_id,
        "filename": file_name,
        "stored_path": str(stored_path),
        "delimiter": delimiter,
        "encoding": encoding,
        "columns": preview.columns,
        "mapping": {},
    }
    _write_metadata(metadata)
    return preview


def _save_mapping(upload_id: str, payload: EasyCsvMappingRequest) -> EasyCsvMappingResponse:
    metadata = _read_metadata(upload_id)
    columns = metadata.get("columns") or []
    _validate_mapping_payload(columns, payload)

    mapper = ColumnMapper()
    mapping_result = mapper.build_mapping(
        columns,
        explicit_mapping=payload.mappings,
        required_columns=REQUIRED_FIELDS,
    )

    metadata["mapping"] = payload.mappings
    metadata["mapping_summary"] = {
        "mapped_columns": payload.mappings,
        "unmapped_columns": mapping_result.unmapped_source_columns,
        "required_missing": mapping_result.missing_required,
        "aliases_applied": mapping_result.aliases_applied,
    }
    _write_metadata(metadata)
    return EasyCsvMappingResponse(
        upload_id=metadata["upload_id"],
        filename=metadata["filename"],
        mapped_columns=payload.mappings,
        unmapped_columns=mapping_result.unmapped_source_columns,
        required_missing=mapping_result.missing_required,
        aliases_applied=mapping_result.aliases_applied,
    )


def _validate_upload(upload_id: str) -> EasyCsvValidationResponse:
    metadata = _read_metadata(upload_id)
    response = _build_validation_response(metadata)
    metadata["validation_summary"] = response.model_dump(mode="json")
    _write_metadata(metadata)
    return response


def _import_upload(upload_id: str, request: Request) -> EasyCsvImportResponse:
    metadata = _read_metadata(upload_id)
    validation_response = _build_validation_response(metadata)
    if not validation_response.can_import:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation must pass before import can run.",
        )

    repository = request.app.state.repository
    state_store = request.app.state.state_store
    raw_loader = request.app.state.raw_loader
    registry = request.app.state.registry

    safe_stem = Path(metadata["filename"]).stem or "csv_source"
    source_request = SourceCreateRequest(
        name=f"easy_csv_{safe_stem}_{upload_id[:8]}",
        type=SourceType.CSV,
        config={
            "file_path": metadata["stored_path"],
            "delimiter": metadata["delimiter"],
            "encoding": metadata["encoding"],
        },
    )
    source = repository.create_source(source_request)
    connector = registry.create(source, state_store, raw_loader)

    repository.update_source_status(source.source_id, SourceStatus.RUNNING)
    import_job_id = repository.create_import_job(
        source.source_id,
        source.name,
        source.type,
    )
    sync_run_id = repository.create_sync_run(source.name, None, "full")

    try:
        result = connector.run_import(
            import_job_id=import_job_id,
            sync_run_id=sync_run_id,
            explicit_mapping=metadata["mapping"],
            required_columns=REQUIRED_FIELDS,
            type_hints=TYPE_HINTS,
            unique_key_columns=UNIQUE_KEY_COLUMNS,
        )
    except Exception as exc:
        message = str(exc)
        repository.update_source_status(source.source_id, SourceStatus.FAILED)
        repository.finish_import_job(import_job_id, "failed", 0, 0, message)
        repository.finish_sync_run(sync_run_id, "failed", 0, None, message)
        repository.record_error(source.source_id, "easy_csv_import", message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

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

    metadata["import_summary"] = {
        "source_id": source.source_id,
        "source_name": source.name,
        "import_job_id": import_job_id,
        "sync_run_id": sync_run_id,
        "rows_extracted": result.rows_extracted,
        "rows_loaded": result.rows_loaded,
        "source_status": SourceStatus.READY.value,
    }
    _write_metadata(metadata)
    return EasyCsvImportResponse(
        upload_id=upload_id,
        filename=metadata["filename"],
        source_id=source.source_id,
        source_name=source.name,
        import_job_id=import_job_id,
        sync_run_id=sync_run_id,
        rows_extracted=result.rows_extracted,
        rows_loaded=result.rows_loaded,
        source_status=SourceStatus.READY.value,
    )


def _run_transform(upload_id: str) -> EasyCsvTransformResponse:
    metadata = _read_metadata(upload_id)
    if not metadata.get("import_summary"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Import must finish before the first transform run can start.",
        )
    mapped_rows, _mapping_result = _mapping_result_for_upload(metadata)
    artifact = run_first_transform(
        mapped_rows,
        artifact_dir=TRANSFORM_ARTIFACT_DIR,
        upload_id=upload_id,
    )
    response = EasyCsvTransformResponse(
        upload_id=upload_id,
        filename=metadata["filename"],
        transform_run_id=artifact.transform_run_id,
        input_row_count=artifact.input_row_count,
        output_row_count=artifact.output_row_count,
        total_orders=artifact.total_orders,
        total_quantity=artifact.total_quantity,
        total_revenue=artifact.total_revenue,
        daily_sales=[
            EasyCsvTransformDailyMetric(
                sales_date=item.sales_date,
                order_count=item.order_count,
                total_quantity=item.total_quantity,
                total_revenue=item.total_revenue,
            )
            for item in artifact.daily_sales
        ],
        artifact_path=artifact.artifact_path,
    )
    metadata["transform_summary"] = response.model_dump(mode="json")
    _write_metadata(metadata)
    return response


def _publish_dashboard(upload_id: str) -> EasyCsvDashboardResponse:
    metadata = _read_metadata(upload_id)
    transform_summary = metadata.get("transform_summary")
    if not transform_summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run the first transform before publishing the starter dashboard.",
        )
    artifact = publish_first_dashboard(
        upload_id=upload_id,
        filename=metadata["filename"],
        transform_summary=transform_summary,
        artifact_dir=DASHBOARD_ARTIFACT_DIR,
    )
    response = EasyCsvDashboardResponse(
        upload_id=upload_id,
        filename=metadata["filename"],
        dashboard_id=artifact.dashboard_id,
        dashboard_title=artifact.dashboard_title,
        dashboard_url=artifact.dashboard_url,
        artifact_path=artifact.artifact_path,
        cards=[
            EasyCsvDashboardCard(
                title=item.title,
                value=item.value,
                description=item.description,
            )
            for item in artifact.cards
        ],
    )
    metadata["dashboard_summary"] = response.model_dump(mode="json")
    _write_metadata(metadata)
    return response


def _run_forecast(upload_id: str) -> EasyCsvForecastResponse:
    metadata = _read_metadata(upload_id)
    transform_summary = metadata.get("transform_summary")
    if not transform_summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run the first transform before the starter forecast can execute.",
        )
    artifact = run_first_forecast(
        upload_id=upload_id,
        transform_summary=transform_summary,
        artifact_dir=FORECAST_ARTIFACT_DIR,
    )
    response = EasyCsvForecastResponse(
        upload_id=upload_id,
        filename=metadata["filename"],
        forecast_run_id=artifact.forecast_run_id,
        baseline_method=artifact.baseline_method,
        base_daily_orders=artifact.base_daily_orders,
        base_daily_units=artifact.base_daily_units,
        base_daily_revenue=artifact.base_daily_revenue,
        horizons=[
            EasyCsvForecastHorizon(
                horizon_days=item.horizon_days,
                projected_orders=item.projected_orders,
                projected_units=item.projected_units,
                projected_revenue=item.projected_revenue,
            )
            for item in artifact.horizons
        ],
        daily_forecast=[
            EasyCsvForecastDailyPoint(
                forecast_date=item.forecast_date,
                projected_units=item.projected_units,
                projected_revenue=item.projected_revenue,
            )
            for item in artifact.daily_forecast
        ],
        artifact_path=artifact.artifact_path,
    )
    metadata["forecast_summary"] = response.model_dump(mode="json")
    _write_metadata(metadata)
    return response


def _step_status(metadata: dict[str, Any]) -> list[tuple[str, bool]]:
    return [
        ("File uploaded", True),
        ("Columns mapped", bool(metadata.get("mapping"))),
        ("Validation complete", bool(metadata.get("validation_summary"))),
        ("Raw import complete", bool(metadata.get("import_summary"))),
        ("First transform run", bool(metadata.get("transform_summary"))),
        ("Starter dashboard published", bool(metadata.get("dashboard_summary"))),
        ("Starter forecast ready", bool(metadata.get("forecast_summary"))),
    ]


def _selected_mapping_for_column(metadata: dict[str, Any], column: str) -> str:
    current_mapping = metadata.get("mapping") or {}
    for canonical, source in current_mapping.items():
        if source == column:
            return canonical
    suggested = ColumnMapper().build_mapping(
        metadata.get("columns") or [],
        required_columns=REQUIRED_FIELDS,
    )
    for item in suggested.mappings:
        if item.source == column:
            return item.target
    return ""


def _render_step_list(metadata: dict[str, Any]) -> str:
    items: list[str] = []
    for label, done in _step_status(metadata):
        status_label = "Complete" if done else "Pending"
        badge_class = "done" if done else "pending"
        items.append(
            f"<li><span>{html.escape(label)}</span>"
            f"<span class='badge {badge_class}'>{status_label}</span></li>"
        )
    return "\n".join(items)


def _render_preview_table(metadata: dict[str, Any]) -> str:
    preview = _build_preview(
        upload_id=metadata["upload_id"],
        filename=metadata["filename"],
        stored_path=Path(metadata["stored_path"]),
        delimiter=metadata["delimiter"],
        encoding=metadata["encoding"],
    )
    headers = "".join(f"<th>{html.escape(column)}</th>" for column in preview.columns)
    body_rows: list[str] = []
    for row in preview.sample_rows:
        cells = "".join(
            f"<td>{html.escape(str(row.get(column) or ''))}</td>" for column in preview.columns
        )
        body_rows.append(f"<tr>{cells}</tr>")
    body = "\n".join(body_rows) or (
        f"<tr><td colspan='{max(len(preview.columns), 1)}'>No rows</td></tr>"
    )
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table>"


def _render_mapping_form(metadata: dict[str, Any]) -> str:
    rows: list[str] = []
    for column in metadata.get("columns") or []:
        selected = _selected_mapping_for_column(metadata, column)
        options = ["<option value=''>Leave unmapped</option>"]
        for canonical in CANONICAL_FIELDS:
            attr = " selected" if canonical == selected else ""
            required_marker = " *" if canonical in REQUIRED_FIELDS else ""
            label = html.escape(canonical + required_marker)
            options.append(f"<option value='{html.escape(canonical)}'{attr}>{label}</option>")
        rows.append(
            "<tr>"
            f"<td>{html.escape(column)}</td>"
            f"<td><select name='map::{html.escape(column)}'>"
            f"{''.join(options)}"
            "</select></td>"
            "</tr>"
        )
    return (
        "<form method='post' action='wizard/mapping'>"
        "<table><thead><tr><th>Source column</th><th>Canonical field</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "<button type='submit'>Save mapping</button>"
        "</form>"
    )


def _render_issues(title: str, issues: list[dict[str, Any]]) -> str:
    if not issues:
        return f"<p>{html.escape(title)}: none.</p>"
    parts = [f"<h3>{html.escape(title)}</h3>", "<ul>"]
    for issue in issues:
        label = issue.get("message") or issue.get("code") or "Issue"
        parts.append(f"<li>{html.escape(str(label))}</li>")
    parts.append("</ul>")
    return "".join(parts)


def _render_dashboard_cards(metadata: dict[str, Any]) -> str:
    dashboard = metadata.get("dashboard_summary")
    if not dashboard:
        return ""
    cards = dashboard.get("cards") or []
    items: list[str] = []
    for card in cards:
        items.append(
            "<div class='card'>"
            f"<div class='card-title'>{html.escape(str(card.get('title', 'Metric')))}</div>"
            f"<div class='card-value'>{html.escape(str(card.get('value', '0')))}</div>"
            f"<div class='card-note'>{html.escape(str(card.get('description', '')))}</div>"
            "</div>"
        )
    return "<div class='card-grid'>" + "".join(items) + "</div>"


def _wizard_shell(title: str, body: str) -> HTMLResponse:
    page = (
        "<!doctype html>"
        "<html lang='en'>"
        "<head>"
        "<meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        f"<style>{WIZARD_CSS}</style>"
        "</head>"
        f"<body>{body}</body>"
        "</html>"
    )
    return HTMLResponse(page)


def _render_home_page(message: str | None = None) -> HTMLResponse:
    flash = f"<div class='flash'>{html.escape(message)}</div>" if message else ""
    description = (
        "Easy CSV onboarding starter path for upload, preview, mapping, validation, raw import, "
        "first transform, dashboard, and forecast."
    )
    body = (
        "<h1>RetailOps Easy CSV Wizard</h1>"
        f"<p class='muted'>{html.escape(description)}</p>"
        f"{flash}"
        "<div class='panel'>"
        "<h2>1. Upload a CSV file</h2>"
        "<form method='post' action='/easy-csv/wizard/upload' "
        "enctype='multipart/form-data'>"
        "<input type='file' name='file' accept='.csv' required>"
        "<button type='submit'>Upload and preview</button>"
        "</form>"
        "<p class='muted'>Sample file: <code>data/sample/orders.csv</code></p>"
        "</div>"
    )
    return _wizard_shell("RetailOps Easy CSV Wizard", body)


def _action_form(action: str, label: str) -> str:
    return (
        f"<form method='post' action='{action}'>"
        f"<button type='submit'>{html.escape(label)}</button>"
        "</form>"
    )


def _metric_paragraph(label: str, value: Any) -> str:
    return f"<p><strong>{html.escape(label)}:</strong> {html.escape(str(value))}</p>"


def _link_paragraph(url: str, label: str) -> str:
    return f"<p><a class='link' href='{html.escape(url)}'>{html.escape(label)}</a></p>"


def _render_transform_table(transform_summary: dict[str, Any]) -> str:
    daily_sales = transform_summary.get("daily_sales") or []
    if not daily_sales:
        return ""
    rows: list[str] = []
    for item in daily_sales:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('sales_date', '')))}</td>"
            f"<td>{html.escape(str(item.get('order_count', '')))}</td>"
            f"<td>{html.escape(str(item.get('total_quantity', '')))}</td>"
            f"<td>{html.escape(str(item.get('total_revenue', '')))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>Date</th><th>Orders</th><th>Quantity</th><th>Revenue</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _render_forecast_table(forecast_summary: dict[str, Any]) -> str:
    horizons = forecast_summary.get("horizons") or []
    if not horizons:
        return ""
    rows: list[str] = []
    for item in horizons:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('horizon_days', '')))}</td>"
            f"<td>{html.escape(str(item.get('projected_orders', '')))}</td>"
            f"<td>{html.escape(str(item.get('projected_units', '')))}</td>"
            f"<td>{html.escape(str(item.get('projected_revenue', '')))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>Days</th>"
        "<th>Projected orders</th>"
        "<th>Projected units</th>"
        "<th>Projected revenue</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def _render_upload_page(metadata: dict[str, Any], message: str | None = None) -> HTMLResponse:
    flash = f"<div class='flash'>{html.escape(message)}</div>" if message else ""
    validation_summary = metadata.get("validation_summary") or {}
    transform_summary = metadata.get("transform_summary") or {}
    forecast_summary = metadata.get("forecast_summary") or {}
    import_summary = metadata.get("import_summary") or {}
    transform_table = _render_transform_table(transform_summary)
    forecast_table = _render_forecast_table(forecast_summary)
    upload_id = html.escape(str(metadata["upload_id"]))
    filename = html.escape(str(metadata["filename"]))

    next_actions = "<br>".join(
        [
            _action_form("wizard/validate", "Run validation"),
            _action_form("wizard/import", "Import to raw"),
            _action_form("wizard/transform", "Run first transform"),
            _action_form("wizard/dashboard", "Publish starter dashboard"),
            _action_form("wizard/forecast", "Run starter forecast"),
        ]
    )

    body = (
        "<h1>RetailOps Easy CSV Wizard</h1>"
        "<p class='muted'><a class='link' href='/easy-csv/wizard'>"
        "Start a new file</a></p>"
        f"{flash}"
        "<div class='grid'>"
        "<div class='panel'>"
        "<h2>Current file</h2>"
        f"<p><strong>{filename}</strong></p>"
        f"<p class='muted'>Upload ID: <code>{upload_id}</code></p>"
        f"<ul class='steps'>{_render_step_list(metadata)}</ul>"
        "</div>"
        "<div class='panel'>"
        "<h2>Next actions</h2>"
        f"{next_actions}"
        "</div>"
        "</div>"
        "<div class='panel'>"
        "<h2>2. Preview</h2>"
        f"{_render_preview_table(metadata)}"
        "</div>"
        "<div class='panel'>"
        "<h2>3. Mapping</h2>"
        f"<p class='muted'>Required canonical fields: {', '.join(REQUIRED_FIELDS)}</p>"
        f"{_render_mapping_form(metadata)}"
        "</div>"
        "<div class='panel'>"
        "<h2>4. Validation report</h2>"
        f"{_render_issues('Warnings', validation_summary.get('warnings') or [])}"
        f"{_render_issues('Blocking errors', validation_summary.get('blocking_errors') or [])}"
        f"{_metric_paragraph('Can import', validation_summary.get('can_import', False))}"
        "</div>"
        "<div class='panel'>"
        "<h2>5. Raw import</h2>"
        f"{_metric_paragraph('Rows loaded', import_summary.get('rows_loaded', 0))}"
        f"{_metric_paragraph('Source status', import_summary.get('source_status', 'pending'))}"
        "</div>"
        "<div class='panel'>"
        "<h2>6. First transform</h2>"
        f"{_metric_paragraph('Total orders', transform_summary.get('total_orders', 0))}"
        f"{_metric_paragraph('Total quantity', transform_summary.get('total_quantity', 0))}"
        f"{_metric_paragraph('Total revenue', transform_summary.get('total_revenue', 0))}"
        f"{transform_table}"
        "</div>"
        "<div class='panel'>"
        "<h2>7. Starter dashboard</h2>"
        f"{_render_dashboard_cards(metadata)}"
        f"{_link_paragraph(f'/easy-csv/{upload_id}/dashboard/view', 'Open dashboard view')}"
        f"{
            _link_paragraph(
                f'/api/v1/dashboard-hub/{upload_id}/view',
                'Open professional dashboard workspace',
            )
        }"
        "</div>"
        "<div class='panel'>"
        "<h2>8. Starter forecast</h2>"
        f"{
            _metric_paragraph(
                'Baseline method',
                forecast_summary.get('baseline_method', 'not-run'),
            )
        }"
        f"{forecast_table}"
        f"{_link_paragraph(f'/easy-csv/{upload_id}/forecast/view', 'Open forecast view')}"
        "</div>"
        "<div class='panel'>"
        "<h2>JSON endpoints</h2>"
        "<p class='muted'>The same flow is available in Swagger at <code>/docs</code>.</p>"
        "</div>"
    )
    title = f"RetailOps Easy CSV Wizard - {metadata['filename']}"
    return _wizard_shell(title, body)


def _redirect_to_wizard(upload_id: str, *, message: str | None = None) -> RedirectResponse:
    target = f"/easy-csv/{upload_id}/wizard"
    if message:
        target = f"{target}?message={message}"
    return RedirectResponse(target, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/wizard", response_class=HTMLResponse)
def wizard_home(message: str | None = None) -> HTMLResponse:
    return _render_home_page(message)


@router.get("/{upload_id}/wizard", response_class=HTMLResponse)
def wizard_detail(upload_id: str, message: str | None = None) -> HTMLResponse:
    metadata = _read_metadata(upload_id)
    return _render_upload_page(metadata, message)


@router.post("/wizard/upload")
async def wizard_upload(file: Annotated[UploadFile, File(...)]) -> RedirectResponse:
    preview = _save_upload(file.filename or "", await file.read())
    return RedirectResponse(
        f"/easy-csv/{preview.upload_id}/wizard?message=Upload completed.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{upload_id}/wizard/mapping")
async def wizard_save_mapping(upload_id: str, request: Request) -> RedirectResponse:
    form = await request.form()
    chosen_targets: dict[str, str] = {}
    for key, value in form.items():
        if not str(key).startswith("map::"):
            continue
        source_column = str(key).removeprefix("map::")
        target_column = str(value).strip()
        if not target_column:
            continue
        if target_column in chosen_targets:
            return _redirect_to_wizard(
                upload_id,
                message="Each canonical field may be selected only once.",
            )
        chosen_targets[target_column] = source_column
    _save_mapping(upload_id, EasyCsvMappingRequest(mappings=chosen_targets))
    return _redirect_to_wizard(upload_id, message="Mapping saved.")


@router.post("/{upload_id}/wizard/validate")
def wizard_validate(upload_id: str) -> RedirectResponse:
    _validate_upload(upload_id)
    return _redirect_to_wizard(upload_id, message="Validation report updated.")


@router.post("/{upload_id}/wizard/import")
def wizard_import(upload_id: str, request: Request) -> RedirectResponse:
    _import_upload(upload_id, request)
    return _redirect_to_wizard(upload_id, message="Raw import completed.")


@router.post("/{upload_id}/wizard/transform")
def wizard_transform(upload_id: str) -> RedirectResponse:
    _run_transform(upload_id)
    return _redirect_to_wizard(upload_id, message="First transform completed.")


@router.post("/{upload_id}/wizard/dashboard")
def wizard_dashboard(upload_id: str) -> RedirectResponse:
    _publish_dashboard(upload_id)
    return _redirect_to_wizard(upload_id, message="Starter dashboard published.")


@router.post("/{upload_id}/wizard/forecast")
def wizard_forecast(upload_id: str) -> RedirectResponse:
    _run_forecast(upload_id)
    return _redirect_to_wizard(upload_id, message="Starter forecast generated.")


@router.get("/{upload_id}/dashboard/view", response_class=HTMLResponse)
def dashboard_view(upload_id: str) -> HTMLResponse:
    metadata = _read_metadata(upload_id)
    dashboard = metadata.get("dashboard_summary")
    transform = metadata.get("transform_summary")
    if not dashboard or not transform:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dashboard has not been published yet.",
        )
    rows: list[str] = []
    for item in transform.get("daily_sales") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('sales_date', '')))}</td>"
            f"<td>{html.escape(str(item.get('order_count', '')))}</td>"
            f"<td>{html.escape(str(item.get('total_quantity', '')))}</td>"
            f"<td>{html.escape(str(item.get('total_revenue', '')))}</td>"
            "</tr>"
        )
    sales_table = (
        "<table><thead><tr>"
        "<th>Date</th><th>Orders</th><th>Quantity</th><th>Revenue</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )
    title = html.escape(str(dashboard["dashboard_title"]))
    body = (
        f"<h1>{title}</h1>"
        f"{_link_paragraph(f'/easy-csv/{html.escape(upload_id)}/wizard', 'Back to wizard')}"
        f"<div class='panel'>{_render_dashboard_cards(metadata)}</div>"
        "<div class='panel'>"
        "<h2>Daily sales</h2>"
        f"{sales_table}"
        "</div>"
    )
    return _wizard_shell(str(dashboard["dashboard_title"]), body)


def _forecast_horizon_table(horizon_rows: list[str]) -> str:
    return (
        "<table><thead><tr>"
        "<th>Days</th>"
        "<th>Projected orders</th>"
        "<th>Projected units</th>"
        "<th>Projected revenue</th>"
        "</tr></thead>"
        f"<tbody>{''.join(horizon_rows)}</tbody>"
        "</table>"
    )


def _forecast_daily_table(daily_rows: list[str]) -> str:
    return (
        "<table><thead><tr>"
        "<th>Date</th><th>Projected units</th><th>Projected revenue</th>"
        "</tr></thead>"
        f"<tbody>{''.join(daily_rows)}</tbody>"
        "</table>"
    )


@router.get("/{upload_id}/forecast/view", response_class=HTMLResponse)
def forecast_view(upload_id: str) -> HTMLResponse:
    metadata = _read_metadata(upload_id)
    forecast = metadata.get("forecast_summary")
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forecast has not been generated yet.",
        )
    horizon_rows: list[str] = []
    for item in forecast.get("horizons") or []:
        horizon_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('horizon_days', '')))}</td>"
            f"<td>{html.escape(str(item.get('projected_orders', '')))}</td>"
            f"<td>{html.escape(str(item.get('projected_units', '')))}</td>"
            f"<td>{html.escape(str(item.get('projected_revenue', '')))}</td>"
            "</tr>"
        )
    daily_rows: list[str] = []
    for item in forecast.get("daily_forecast") or []:
        daily_rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('forecast_date', '')))}</td>"
            f"<td>{html.escape(str(item.get('projected_units', '')))}</td>"
            f"<td>{html.escape(str(item.get('projected_revenue', '')))}</td>"
            "</tr>"
        )
    body = (
        "<h1>Starter forecast view</h1>"
        f"{_link_paragraph(f'/easy-csv/{html.escape(upload_id)}/wizard', 'Back to wizard')}"
        "<div class='panel'>"
        f"{_metric_paragraph('Baseline', forecast.get('baseline_method', 'unknown'))}"
        f"{_metric_paragraph('Base daily orders', forecast.get('base_daily_orders', 0))}"
        f"{_metric_paragraph('Base daily units', forecast.get('base_daily_units', 0))}"
        f"{_metric_paragraph('Base daily revenue', forecast.get('base_daily_revenue', 0))}"
        "</div>"
        "<div class='panel'>"
        "<h2>7 / 14 / 30 day summary</h2>"
        f"{_forecast_horizon_table(horizon_rows)}"
        "</div>"
        "<div class='panel'>"
        "<h2>Next 7 days</h2>"
        f"{_forecast_daily_table(daily_rows)}"
        "</div>"
    )
    return _wizard_shell("Starter forecast view", body)


@router.post("/upload", response_model=EasyCsvPreviewResponse)
async def upload_csv(file: Annotated[UploadFile, File(...)]) -> EasyCsvPreviewResponse:
    return _save_upload(file.filename or "", await file.read())


@router.get("/{upload_id}/preview", response_model=EasyCsvPreviewResponse)
def get_preview(upload_id: str) -> EasyCsvPreviewResponse:
    metadata = _read_metadata(upload_id)
    stored_path = Path(metadata["stored_path"])
    if not stored_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored CSV file not found.",
        )

    return _build_preview(
        upload_id=metadata["upload_id"],
        filename=metadata["filename"],
        stored_path=stored_path,
        delimiter=metadata["delimiter"],
        encoding=metadata["encoding"],
    )


@router.post("/{upload_id}/mapping", response_model=EasyCsvMappingResponse)
def save_mapping(upload_id: str, payload: EasyCsvMappingRequest) -> EasyCsvMappingResponse:
    return _save_mapping(upload_id, payload)


@router.post("/{upload_id}/validate", response_model=EasyCsvValidationResponse)
def validate_upload(upload_id: str) -> EasyCsvValidationResponse:
    return _validate_upload(upload_id)


@router.post("/{upload_id}/import", response_model=EasyCsvImportResponse)
def import_upload(upload_id: str, request: Request) -> EasyCsvImportResponse:
    return _import_upload(upload_id, request)


@router.post("/{upload_id}/transform", response_model=EasyCsvTransformResponse)
def transform_upload(upload_id: str) -> EasyCsvTransformResponse:
    return _run_transform(upload_id)


@router.post("/{upload_id}/dashboard", response_model=EasyCsvDashboardResponse)
def publish_dashboard(upload_id: str) -> EasyCsvDashboardResponse:
    return _publish_dashboard(upload_id)


@router.post("/{upload_id}/forecast", response_model=EasyCsvForecastResponse)
def forecast_upload(upload_id: str) -> EasyCsvForecastResponse:
    return _run_forecast(upload_id)
