# Project:      RetailOps Data & AI Platform
# Module:       core.api.routes
# File:         setup.py
# Path:         core/api/routes/setup.py
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
#   - Key APIs: router, create_session, get_session, set_store, set_source,
#     test_connection, get_source_types
#   - Dependencies: __future__, html, json, typing, fastapi,
#     fastapi.responses, config.settings, core.api.schemas.setup,
#     core.ingestion.base.registry, core.setup.service
#   - Constraints: Public request and response behavior should remain backward
#     compatible with documented API flows.
#   - Compatibility: Python 3.12+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

import html
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from config.settings import get_settings
from core.api.schemas.setup import (
    SetupMappingRequest,
    SetupModulesRequest,
    SetupSessionCreateRequest,
    SetupSessionResponse,
    SetupSourceRequest,
    SetupStoreRequest,
)
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.registry import ConnectorRegistry, ConnectorSpec, get_connector_specs
from core.ingestion.base.repository import RepositoryProtocol
from core.ingestion.base.state_store import StateStore
from core.setup.service import (
    DEFAULT_MODULES,
    configure_setup_source,
    create_setup_session,
    enable_setup_modules,
    get_setup_session,
    publish_setup_dashboards,
    run_setup_first_import,
    run_setup_first_training,
    run_setup_first_transform,
    save_setup_mapping,
    test_setup_source_connection,
    update_setup_store,
)

router = APIRouter(tags=["setup"])

CREATE_SETUP_SESSION = create_setup_session
GET_SETUP_SESSION = get_setup_session
UPDATE_SETUP_STORE = update_setup_store
CONFIGURE_SETUP_SOURCE = configure_setup_source
TEST_SETUP_SOURCE_CONNECTION = test_setup_source_connection
SAVE_SETUP_MAPPING = save_setup_mapping
RUN_SETUP_FIRST_IMPORT = run_setup_first_import
RUN_SETUP_FIRST_TRANSFORM = run_setup_first_transform
ENABLE_SETUP_MODULES = enable_setup_modules
RUN_SETUP_FIRST_TRAINING = run_setup_first_training
PUBLISH_SETUP_DASHBOARDS = publish_setup_dashboards


def _repository(request: Request) -> RepositoryProtocol:
    return request.app.state.repository


def _state_store(request: Request) -> StateStore:
    return request.app.state.state_store


def _raw_loader(request: Request) -> RawLoader:
    return request.app.state.raw_loader


def _registry(request: Request) -> ConnectorRegistry:
    return request.app.state.registry


RepositoryDep = Annotated[RepositoryProtocol, Depends(_repository)]
StateStoreDep = Annotated[StateStore, Depends(_state_store)]
RawLoaderDep = Annotated[RawLoader, Depends(_raw_loader)]
RegistryDep = Annotated[ConnectorRegistry, Depends(_registry)]


WIZARD_CSS = "\n".join(
    [
        (
            "body { font-family: Arial, sans-serif; margin: 2rem auto; "
            "max-width: 1080px; color: #1f2937; }"
        ),
        "h1, h2, h3 { color: #0f172a; }",
        (
            ".panel { border: 1px solid #dbe4ee; border-radius: 14px; "
            "padding: 1rem 1.2rem; margin-bottom: 1rem; }"
        ),
        ".grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }",
        ".steps { list-style: none; padding: 0; margin: 0; }",
        (
            ".steps li { display: flex; justify-content: space-between; "
            "border-bottom: 1px solid #e2e8f0; padding: 0.5rem 0; }"
        ),
        ".badge { border-radius: 999px; padding: 0.2rem 0.6rem; font-size: 0.82rem; }",
        ".done { background: #dcfce7; color: #166534; }",
        ".pending { background: #e2e8f0; color: #334155; }",
        ".failed { background: #fee2e2; color: #991b1b; }",
        (
            "button { background: #2563eb; color: white; border: 0; "
            "border-radius: 10px; padding: 0.6rem 0.9rem; cursor: pointer; }"
        ),
        (
            "input, select, textarea { width: 100%; padding: 0.55rem; "
            "margin-top: 0.35rem; box-sizing: border-box; }"
        ),
        "textarea { min-height: 120px; }",
        ".muted { color: #64748b; }",
        (
            ".flash { background: #fef3c7; border: 1px solid #f59e0b; "
            "border-radius: 12px; padding: 0.75rem 1rem; }"
        ),
        "a { color: #2563eb; text-decoration: none; }",
        "code { background: #f1f5f9; padding: 0.1rem 0.35rem; border-radius: 6px; }",
    ]
)


def _enabled_connector_specs() -> list[ConnectorSpec]:
    return get_connector_specs(get_settings().enabled_connector_values)


def _enabled_source_types() -> set[str]:
    return {item.source_value for item in _enabled_connector_specs()}


def _ensure_source_type_enabled(source_type: str) -> str:
    normalized = str(source_type).strip().lower()
    if normalized not in _enabled_source_types():
        enabled = ", ".join(item.label for item in _enabled_connector_specs())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Source type '{normalized}' is not enabled in this installation. "
                f"Enabled connectors: {enabled}."
            ),
        )
    return normalized


def _wizard_shell(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        "<!DOCTYPE html>"
        "<html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        f"<style>{WIZARD_CSS}</style>"
        "</head><body>"
        f"{body}"
        "</body></html>"
    )


def _escaped_text(value: Any, default: str = "") -> str:
    raw_value = value if value not in {None, ""} else default
    return html.escape(str(raw_value))


def _input_field(label: str, name: str, value: Any) -> str:
    return (
        f"<label>{html.escape(label)}"
        f"<input name='{html.escape(name)}' value='{_escaped_text(value)}'>"
        "</label>"
    )


def _select_source_type(current_value: Any) -> str:
    current = str(current_value or "csv")
    rendered_options: list[str] = []
    for spec in _enabled_connector_specs():
        selected = " selected" if spec.source_value == current else ""
        rendered_options.append(
            f"<option value='{spec.source_value}'{selected}>{html.escape(spec.label)}</option>"
        )
    return (
        f"<label>Source type<select name='source_type'>{''.join(rendered_options)}</select></label>"
    )


def _render_source_configuration_fields(source_type: Any, source_config: dict[str, Any]) -> str:
    current = str(source_type or "csv")
    for spec in _enabled_connector_specs():
        if spec.source_value != current:
            continue
        fields = [
            _input_field(field.label, field.name, source_config.get(field.name) or field.default)
            for field in spec.wizard_fields
        ]
        fields.append(
            "<p class='muted'>Only the fields required by the selected connector are used. "
            "You can switch connectors without installing the other connector services.</p>"
        )
        return "".join(fields)
    return "<p class='muted'>No source fields are available for this connector selection.</p>"


def _post_button_form(action: str, button_label: str) -> str:
    return (
        f"<form method='post' action='{action}'>"
        f"<p><button type='submit'>{html.escape(button_label)}</button></p>"
        "</form>"
    )


def _render_step_list(session: SetupSessionResponse) -> str:
    items: list[str] = []
    for step in session.steps:
        badge_class = (
            "done" if step.status == "done" else "failed" if step.status == "failed" else "pending"
        )
        items.append(
            f"<li><span>{html.escape(step.label)}</span>"
            f"<span class='badge {badge_class}'>{html.escape(step.status.title())}</span></li>"
        )
    return "".join(items)


def _render_logs(session: SetupSessionResponse) -> str:
    if not session.logs:
        return "<p class='muted'>No logs yet.</p>"
    lines = [
        (
            f"<li><code>{html.escape(item.timestamp)}</code> "
            f"{html.escape(item.step)} - {html.escape(item.message)}</li>"
        )
        for item in session.logs[-8:]
    ]
    return f"<ul>{''.join(lines)}</ul>"


def _render_mapping_text(session: SetupSessionResponse) -> str:
    if not session.mapping:
        return "{}"
    return json.dumps(session.mapping, ensure_ascii=False, indent=2)


@router.get("/api/v1/setup/source-types")
def get_source_types() -> list[dict[str, Any]]:
    return [
        {
            "source_type": spec.source_value,
            "label": spec.label,
            "fields": [
                {"name": field.name, "label": field.label, "default": field.default}
                for field in spec.wizard_fields
            ],
        }
        for spec in _enabled_connector_specs()
    ]


@router.post(
    "/api/v1/setup/sessions",
    response_model=SetupSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(request: SetupSessionCreateRequest) -> dict[str, Any]:
    return CREATE_SETUP_SESSION(
        store_name=request.store_name,
        store_code=request.store_code,
        sample_mode=request.sample_mode,
    )


@router.get("/api/v1/setup/sessions/{session_id}", response_model=SetupSessionResponse)
def get_session(session_id: str) -> dict[str, Any]:
    try:
        return GET_SETUP_SESSION(session_id=session_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/api/v1/setup/sessions/{session_id}/store", response_model=SetupSessionResponse)
def set_store(session_id: str, request: SetupStoreRequest) -> dict[str, Any]:
    return UPDATE_SETUP_STORE(
        session_id=session_id,
        store_name=request.store_name,
        store_code=request.store_code,
        currency=request.currency,
        timezone=request.timezone,
    )


@router.post("/api/v1/setup/sessions/{session_id}/source", response_model=SetupSessionResponse)
def set_source(session_id: str, request: SetupSourceRequest) -> dict[str, Any]:
    _ensure_source_type_enabled(request.source_type.value)
    try:
        return CONFIGURE_SETUP_SOURCE(
            session_id=session_id,
            source_type=request.source_type.value,
            source_name=request.source_name,
            config=request.config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/api/v1/setup/sessions/{session_id}/test-connection", response_model=SetupSessionResponse
)
def test_connection(
    session_id: str,
    repository: RepositoryDep,
    state_store: StateStoreDep,
    raw_loader: RawLoaderDep,
    registry: RegistryDep,
) -> dict[str, Any]:
    try:
        return TEST_SETUP_SOURCE_CONNECTION(
            session_id=session_id,
            repository=repository,
            state_store=state_store,
            raw_loader=raw_loader,
            registry=registry,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/api/v1/setup/sessions/{session_id}/mapping", response_model=SetupSessionResponse)
def save_mapping(session_id: str, request: SetupMappingRequest) -> dict[str, Any]:
    try:
        return SAVE_SETUP_MAPPING(session_id=session_id, mappings=request.mappings)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/api/v1/setup/sessions/{session_id}/import", response_model=SetupSessionResponse)
def run_import(
    session_id: str,
    repository: RepositoryDep,
    state_store: StateStoreDep,
    raw_loader: RawLoaderDep,
    registry: RegistryDep,
) -> dict[str, Any]:
    try:
        return RUN_SETUP_FIRST_IMPORT(
            session_id=session_id,
            repository=repository,
            state_store=state_store,
            raw_loader=raw_loader,
            registry=registry,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/api/v1/setup/sessions/{session_id}/dbt-run", response_model=SetupSessionResponse)
def run_dbt(session_id: str) -> dict[str, Any]:
    try:
        return RUN_SETUP_FIRST_TRANSFORM(session_id=session_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/api/v1/setup/sessions/{session_id}/enable-modules", response_model=SetupSessionResponse
)
def set_modules(session_id: str, request: SetupModulesRequest) -> dict[str, Any]:
    return ENABLE_SETUP_MODULES(session_id=session_id, modules=request.modules)


@router.post("/api/v1/setup/sessions/{session_id}/train", response_model=SetupSessionResponse)
def run_training(session_id: str) -> dict[str, Any]:
    try:
        return RUN_SETUP_FIRST_TRAINING(session_id=session_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/api/v1/setup/sessions/{session_id}/publish-dashboards", response_model=SetupSessionResponse
)
def run_dashboards(session_id: str) -> dict[str, Any]:
    try:
        return PUBLISH_SETUP_DASHBOARDS(session_id=session_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/setup/wizard", response_class=HTMLResponse)
def setup_wizard_home(message: str | None = None) -> HTMLResponse:
    flash = f"<div class='flash'>{html.escape(message)}</div>" if message else ""
    body_parts = [
        "<h1>RetailOps Setup wizard Setup Wizard</h1>",
        (
            "<p class='muted'>This guided wizard covers create store, choose source, "
            "test connection, map fields, first import, first dbt run, enable "
            "modules, first model training, and publish dashboards.</p>"
        ),
        flash,
        "<div class='panel'>",
        "<h2>Start a new session</h2>",
        "<form method='post' action='/setup/wizard/start'>",
        "<label>Store name<input name='store_name' value='RetailOps Demo Store'></label>",
        "<label>Store code<input name='store_code' value='DEMO-01'></label>",
        (
            "<label><input type='checkbox' name='sample_mode' checked> "
            "Start in sample data mode</label>"
        ),
        "<p><button type='submit'>Create setup session</button></p>",
        "</form>",
        "</div>",
    ]
    return _wizard_shell("RetailOps Setup wizard Setup Wizard", "".join(body_parts))


@router.post("/setup/wizard/start")
def setup_wizard_start(
    store_name: Annotated[str, Form()],
    store_code: Annotated[str, Form()],
    sample_mode: Annotated[str | None, Form()] = None,
) -> RedirectResponse:
    session = CREATE_SETUP_SESSION(
        store_name=store_name,
        store_code=store_code,
        sample_mode=sample_mode is not None,
    )
    return RedirectResponse(
        url=f"/setup/sessions/{session['session_id']}/wizard?message=Setup session created.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/setup/sessions/{session_id}/wizard", response_class=HTMLResponse)
def setup_wizard_detail(session_id: str, message: str | None = None) -> HTMLResponse:
    try:
        session = SetupSessionResponse.model_validate(GET_SETUP_SESSION(session_id=session_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    flash = f"<div class='flash'>{html.escape(message)}</div>" if message else ""
    escaped_session_id = html.escape(session.session_id)
    store = session.store
    source = session.source
    source_config = source.get("config") or {}
    next_step = html.escape(str(session.next_step or "done"))
    progress_line = (
        f"<p><strong>{session.progress_percent}%</strong> complete. "
        f"Next step: <code>{next_step}</code></p>"
    )
    store_form_action = f"/setup/sessions/{escaped_session_id}/wizard/store"
    source_form_action = f"/setup/sessions/{escaped_session_id}/wizard/source"
    mapping_form_action = f"/setup/sessions/{escaped_session_id}/wizard/mapping"
    test_form_action = f"/setup/sessions/{escaped_session_id}/wizard/test"
    import_form_action = f"/setup/sessions/{escaped_session_id}/wizard/import"
    dbt_form_action = f"/setup/sessions/{escaped_session_id}/wizard/dbt"
    modules_form_action = f"/setup/sessions/{escaped_session_id}/wizard/modules"
    train_form_action = f"/setup/sessions/{escaped_session_id}/wizard/train"
    dashboard_form_action = f"/setup/sessions/{escaped_session_id}/wizard/dashboard"
    enabled_modules_text = ", ".join(session.enabled_modules or DEFAULT_MODULES)
    source_type_select = _select_source_type(source.get("type"))

    body_parts = [
        f"<h1>RetailOps Setup wizard Setup Wizard · {escaped_session_id}</h1>",
        "<p class='muted'><a href='/setup/wizard'>Start another session</a></p>",
        flash,
        "<div class='grid'>",
        "<div class='panel'>",
        "<h2>Progress</h2>",
        progress_line,
        f"<ul class='steps'>{_render_step_list(session)}</ul>",
        "</div>",
        "<div class='panel'>",
        "<h2>Recent logs</h2>",
        _render_logs(session),
        "</div>",
        "</div>",
        "<div class='grid'>",
        "<div class='panel'>",
        "<h2>Store</h2>",
        f"<form method='post' action='{store_form_action}'>",
        _input_field("Store name", "store_name", store.get("name")),
        _input_field("Store code", "store_code", store.get("code")),
        _input_field("Currency", "currency", store.get("currency") or "EUR"),
        _input_field(
            "Timezone",
            "timezone",
            store.get("timezone") or "Europe/Helsinki",
        ),
        "<p><button type='submit'>Save store</button></p>",
        "</form>",
        "</div>",
        "<div class='panel'>",
        "<h2>Source</h2>",
        f"<form method='post' action='{source_form_action}'>",
        source_type_select,
        _input_field("Source name", "source_name", source.get("name")),
        _render_source_configuration_fields(source.get("type"), source_config),
        "<p><button type='submit'>Save source</button></p>",
        "</form>",
        _post_button_form(test_form_action, "Test connection"),
        "</div>",
        "</div>",
        "<div class='grid'>",
        "<div class='panel'>",
        "<h2>Mapping</h2>",
        f"<form method='post' action='{mapping_form_action}'>",
        "<label>Mapping JSON<textarea name='mapping_json'>",
        html.escape(_render_mapping_text(session)),
        "</textarea></label>",
        "<p class='muted'>Leave <code>{}</code> to auto-map the CSV columns.</p>",
        "<p><button type='submit'>Save mapping</button></p>",
        "</form>",
        _post_button_form(import_form_action, "Run first import"),
        _post_button_form(dbt_form_action, "Run first dbt step"),
        "</div>",
        "<div class='panel'>",
        "<h2>Modules and outputs</h2>",
        f"<form method='post' action='{modules_form_action}'>",
        _input_field("Enabled modules", "modules_csv", enabled_modules_text),
        "<p><button type='submit'>Enable modules</button></p>",
        "</form>",
        _post_button_form(train_form_action, "Run first model training"),
        _post_button_form(dashboard_form_action, "Publish dashboards"),
        "</div>",
        "</div>",
    ]
    return _wizard_shell("RetailOps Setup wizard Setup Wizard", "".join(body_parts))


@router.post("/setup/sessions/{session_id}/wizard/store")
def wizard_store(
    session_id: str,
    store_name: Annotated[str, Form()],
    store_code: Annotated[str, Form()],
    currency: Annotated[str, Form()] = "EUR",
    timezone: Annotated[str, Form()] = "Europe/Helsinki",
) -> RedirectResponse:
    UPDATE_SETUP_STORE(
        session_id=session_id,
        store_name=store_name,
        store_code=store_code,
        currency=currency,
        timezone=timezone,
    )
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message=Store saved.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/setup/sessions/{session_id}/wizard/source")
def wizard_source(
    session_id: str,
    source_type: Annotated[str, Form()],
    source_name: Annotated[str, Form()],
    file_path: Annotated[str, Form()] = "",
    delimiter: Annotated[str, Form()] = ",",
    encoding: Annotated[str, Form()] = "utf-8",
    database_url: Annotated[str, Form()] = "",
    query: Annotated[str, Form()] = "",
    store_url: Annotated[str, Form()] = "",
    access_token: Annotated[str, Form()] = "",
    api_version: Annotated[str, Form()] = "",
    resource: Annotated[str, Form()] = "orders",
    consumer_key: Annotated[str, Form()] = "",
    consumer_secret: Annotated[str, Form()] = "",
    base_url: Annotated[str, Form()] = "",
    store_code: Annotated[str, Form()] = "default",
    api_root: Annotated[str, Form()] = "https://api.bigcommerce.com/stores",
    store_hash: Annotated[str, Form()] = "",
    api_key: Annotated[str, Form()] = "",
) -> RedirectResponse:
    config: dict[str, Any] = {}
    normalized_type = _ensure_source_type_enabled(source_type)
    for key, value in {
        "file_path": file_path,
        "delimiter": delimiter,
        "encoding": encoding,
        "database_url": database_url,
        "query": query,
        "store_url": store_url,
        "access_token": access_token,
        "api_version": api_version,
        "resource": resource,
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "base_url": base_url,
        "store_code": store_code,
        "api_root": api_root,
        "store_hash": store_hash,
        "api_key": api_key,
    }.items():
        if str(value).strip():
            config[key] = str(value).strip()
    try:
        CONFIGURE_SETUP_SOURCE(
            session_id=session_id,
            source_type=normalized_type,
            source_name=source_name,
            config=config,
        )
        message = "Source saved."
    except ValueError as exc:
        message = str(exc)
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message={html.escape(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/setup/sessions/{session_id}/wizard/test")
def wizard_test_connection(
    session_id: str,
    repository: RepositoryDep,
    state_store: StateStoreDep,
    raw_loader: RawLoaderDep,
    registry: RegistryDep,
) -> RedirectResponse:
    try:
        TEST_SETUP_SOURCE_CONNECTION(
            session_id=session_id,
            repository=repository,
            state_store=state_store,
            raw_loader=raw_loader,
            registry=registry,
        )
        message = "Connection test completed."
    except (FileNotFoundError, ValueError) as exc:
        message = str(exc)
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message={html.escape(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/setup/sessions/{session_id}/wizard/mapping")
def wizard_mapping(
    session_id: str,
    mapping_json: Annotated[str, Form()] = "{}",
) -> RedirectResponse:
    try:
        payload = json.loads(mapping_json or "{}")
        mappings = payload if isinstance(payload, dict) else {}
        SAVE_SETUP_MAPPING(
            session_id=session_id,
            mappings={str(k): str(v) for k, v in mappings.items()},
        )
        message = "Mapping saved."
    except Exception as exc:
        message = str(exc)
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message={html.escape(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/setup/sessions/{session_id}/wizard/import")
def wizard_import(
    session_id: str,
    repository: RepositoryDep,
    state_store: StateStoreDep,
    raw_loader: RawLoaderDep,
    registry: RegistryDep,
) -> RedirectResponse:
    try:
        RUN_SETUP_FIRST_IMPORT(
            session_id=session_id,
            repository=repository,
            state_store=state_store,
            raw_loader=raw_loader,
            registry=registry,
        )
        message = "First import completed."
    except Exception as exc:
        message = str(exc)
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message={html.escape(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/setup/sessions/{session_id}/wizard/dbt")
def wizard_dbt(session_id: str) -> RedirectResponse:
    try:
        RUN_SETUP_FIRST_TRANSFORM(session_id=session_id)
        message = "First dbt step completed."
    except Exception as exc:
        message = str(exc)
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message={html.escape(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/setup/sessions/{session_id}/wizard/modules")
def wizard_modules(
    session_id: str,
    modules_csv: Annotated[str, Form()] = ", ".join(DEFAULT_MODULES),
) -> RedirectResponse:
    selected = [item.strip() for item in modules_csv.split(",") if item.strip()]
    ENABLE_SETUP_MODULES(session_id=session_id, modules=selected)
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message=Modules enabled.",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/setup/sessions/{session_id}/wizard/train")
def wizard_train(session_id: str) -> RedirectResponse:
    try:
        RUN_SETUP_FIRST_TRAINING(session_id=session_id)
        message = "First model training completed."
    except Exception as exc:
        message = str(exc)
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message={html.escape(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/setup/sessions/{session_id}/wizard/dashboard")
def wizard_dashboard(session_id: str) -> RedirectResponse:
    try:
        PUBLISH_SETUP_DASHBOARDS(session_id=session_id)
        message = "Dashboards published."
    except Exception as exc:
        message = str(exc)
    return RedirectResponse(
        url=f"/setup/sessions/{session_id}/wizard?message={html.escape(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
