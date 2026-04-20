#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="$ROOT_DIR/backups"

log() {
  printf '[INFO] %s
' "$*"
}

warn() {
  printf '[WARN] %s
' "$*" >&2
}

fail() {
  printf '[ERROR] %s
' "$*" >&2
  exit 1
}

load_env() {
  local env_file
  if [ -f "$ROOT_DIR/.env" ]; then
    env_file="$ROOT_DIR/.env"
  else
    env_file="$ROOT_DIR/.env.example"
  fi

  set -a
  # shellcheck disable=SC1090
  . "$env_file"
  set +a
}

all_connectors() {
  printf '%s
'     csv     database     shopify     woocommerce     adobe_commerce     bigcommerce     prestashop
}

all_optional_extras() {
  printf '%s
'     reporting     feature-store     advanced-serving
}

profile_default_connectors() {
  local profile="$1"
  case "$profile" in
    lite)
      printf '%s
' 'csv'
      ;;
    standard)
      printf '%s
' 'csv,database,shopify'
      ;;
    pro)
      printf '%s
' 'csv,database,shopify,woocommerce,adobe_commerce,bigcommerce,prestashop'
      ;;
    *)
      fail "Unsupported profile: $profile"
      ;;
  esac
}

profile_default_extras() {
  local profile="$1"
  case "$profile" in
    lite)
      printf '%s
' 'reporting'
      ;;
    standard)
      printf '%s
' 'reporting'
      ;;
    pro)
      printf '%s
' 'reporting,feature-store,advanced-serving'
      ;;
    *)
      fail "Unsupported profile: $profile"
      ;;
  esac
}

normalize_connector_list() {
  local raw="$1"
  local normalized=''
  local seen=',' candidate item

  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | tr ';:' ',,')"
  IFS=',' read -r -a __connector_items <<< "$raw"
  for item in "${__connector_items[@]}"; do
    candidate="$(printf '%s' "$item" | xargs)"
    case "$candidate" in
      '')
        continue
        ;;
      db)
        candidate='database'
        ;;
      *)
        ;;
    esac
    if ! all_connectors | grep -Fxq "$candidate"; then
      fail "Unsupported connector: $candidate"
    fi
    case "$seen" in
      *",${candidate},"*)
        continue
        ;;
      *)
        seen="${seen}${candidate},"
        if [ -n "$normalized" ]; then
          normalized="${normalized},${candidate}"
        else
          normalized="$candidate"
        fi
        ;;
    esac
  done

  if [ -z "$normalized" ]; then
    fail 'At least one connector must be enabled.'
  fi
  printf '%s
' "$normalized"
}

normalize_optional_extra_list() {
  local raw="$1"
  local normalized=''
  local seen=',' candidate item

  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | tr ';:' ',,')"
  raw="$(printf '%s' "$raw" | xargs)"
  case "$raw" in
    ''|none)
      printf '%s
' ''
      return 0
      ;;
    *)
      ;;
  esac

  IFS=',' read -r -a __extra_items <<< "$raw"
  for item in "${__extra_items[@]}"; do
    candidate="$(printf '%s' "$item" | xargs)"
    case "$candidate" in
      ''|none)
        continue
        ;;
      feature_store)
        candidate='feature-store'
        ;;
      advanced_serving)
        candidate='advanced-serving'
        ;;
      *)
        ;;
    esac
    if ! all_optional_extras | grep -Fxq "$candidate"; then
      fail "Unsupported optional extra: $candidate"
    fi
    case "$seen" in
      *",${candidate},"*)
        continue
        ;;
      *)
        seen="${seen}${candidate},"
        if [ -n "$normalized" ]; then
          normalized="${normalized},${candidate}"
        else
          normalized="$candidate"
        fi
        ;;
    esac
  done
  printf '%s
' "$normalized"
}

resolve_enabled_connectors() {
  local profile="$1"
  local raw=''
  if [ -n "${PROFILE_CONNECTORS_OVERRIDE+x}" ]; then
    raw="$PROFILE_CONNECTORS_OVERRIDE"
  else
    load_env
    raw="${ENABLED_CONNECTORS:-}"
  fi
  if [ -z "$raw" ]; then
    raw="$(profile_default_connectors "$profile")"
  fi
  normalize_connector_list "$raw"
}

resolve_enabled_extras() {
  local profile="$1"
  local raw=''
  if [ -n "${PROFILE_OPTIONAL_EXTRAS_OVERRIDE+x}" ]; then
    raw="$PROFILE_OPTIONAL_EXTRAS_OVERRIDE"
  else
    load_env
    raw="${ENABLED_OPTIONAL_EXTRAS:-}"
  fi
  if [ -z "$raw" ] && [ -z "${PROFILE_OPTIONAL_EXTRAS_OVERRIDE+x}" ]; then
    raw="$(profile_default_extras "$profile")"
  fi
  normalize_optional_extra_list "$raw"
}

extras_as_lines() {
  local raw="$1"
  local item
  if [ -z "$raw" ]; then
    return 0
  fi
  IFS=',' read -r -a __extras <<< "$raw"
  for item in "${__extras[@]}"; do
    if [ -n "$item" ]; then
      printf '%s
' "$item"
    fi
  done
}

update_env_value() {
  local env_path="$1"
  local key="$2"
  local value="$3"
  python3 - "$env_path" "$key" "$value" <<'PY2'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
text = path.read_text(encoding='utf-8') if path.exists() else ''
pattern = rf'^{re.escape(key)}=.*$'
line = f'{key}={value}'
if re.search(pattern, text, flags=re.MULTILINE):
    text = re.sub(pattern, line, text, flags=re.MULTILINE)
else:
    if text and not text.endswith('\n'):
        text += '\n'
    text += line + '\n'
path.write_text(text, encoding='utf-8')
PY2
}

ensure_runtime_dirs() {
  mkdir -p     "$ROOT_DIR/backups"     "$ROOT_DIR/data/uploads"     "$ROOT_DIR/data/artifacts/transforms"     "$ROOT_DIR/data/artifacts/dashboards"     "$ROOT_DIR/data/artifacts/forecasts"     "$ROOT_DIR/data/artifacts/serving"     "$ROOT_DIR/data/artifacts/shipment_risk"     "$ROOT_DIR/data/artifacts/stockout_risk"     "$ROOT_DIR/data/artifacts/reorder"     "$ROOT_DIR/data/artifacts/model_registry"     "$ROOT_DIR/data/artifacts/returns_risk"     "$ROOT_DIR/data/artifacts/monitoring"     "$ROOT_DIR/data/artifacts/monitoring/overrides"     "$ROOT_DIR/data/artifacts/setup/sessions"     "$ROOT_DIR/data/artifacts/pro_platform/cdc"     "$ROOT_DIR/data/artifacts/pro_platform/streaming"     "$ROOT_DIR/data/artifacts/pro_platform/lakehouse"     "$ROOT_DIR/data/artifacts/pro_platform/query_layer"     "$ROOT_DIR/data/artifacts/pro_platform/metadata"     "$ROOT_DIR/data/artifacts/pro_platform/feature_store"     "$ROOT_DIR/data/artifacts/pro_platform/advanced_serving"
}

bootstrap_env_file() {
  local profile="$1"
  local sample_file="$ROOT_DIR/config/samples/${profile}.env"
  if [ ! -f "$ROOT_DIR/.env" ]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    log 'Created .env from .env.example'
  fi
  if [ -f "$sample_file" ]; then
    python3 - "$ROOT_DIR/.env" "$sample_file" <<'PY2'
from pathlib import Path
import sys

env_path = Path(sys.argv[1])
sample_path = Path(sys.argv[2])

def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip()
    return values

current = parse_env(env_path)
sample = parse_env(sample_path)
missing = {k: v for k, v in sample.items() if k not in current}
if missing:
    with env_path.open('a', encoding='utf-8') as handle:
        handle.write('\n# Added from profile sample\n')
        for key, value in missing.items():
            handle.write(f'{key}={value}\n')
PY2
  fi
}

connector_file() {
  local connector="$1"
  case "$connector" in
    csv)
      printf '%s
' 'compose/compose.connector_csv.yaml'
      ;;
    database)
      printf '%s
' 'compose/compose.connector_db.yaml'
      ;;
    shopify)
      printf '%s
' 'compose/compose.connector_shopify.yaml'
      ;;
    woocommerce)
      printf '%s
' 'compose/compose.connector_woocommerce.yaml'
      ;;
    adobe_commerce)
      printf '%s
' 'compose/compose.connector_adobe_commerce.yaml'
      ;;
    bigcommerce)
      printf '%s
' 'compose/compose.connector_bigcommerce.yaml'
      ;;
    prestashop)
      printf '%s
' 'compose/compose.connector_prestashop.yaml'
      ;;
    *)
      fail "Unsupported connector: $connector"
      ;;
  esac
}

profile_files() {
  local profile="$1"
  local connectors
  local connector
  connectors="$(resolve_enabled_connectors "$profile")"
  case "$profile" in
    lite)
      printf '%s
'         'compose/compose.core.yaml'         'compose/compose.analytics.yaml'
      ;;
    standard)
      printf '%s
'         'compose/compose.core.yaml'         'compose/compose.analytics.yaml'         'compose/compose.ml.yaml'         'compose/compose.monitoring.yaml'
      ;;
    pro)
      printf '%s
'         'compose/compose.core.yaml'         'compose/compose.analytics.yaml'         'compose/compose.ml.yaml'         'compose/compose.monitoring.yaml'         'compose/compose.cdc.yaml'         'compose/compose.streaming.yaml'         'compose/compose.lakehouse.yaml'         'compose/compose.query.yaml'         'compose/compose.metadata.yaml'         'compose/compose.feature_store.yaml'         'compose/compose.advanced_serving.yaml'
      ;;
    *)
      fail "Unsupported profile: $profile"
      ;;
  esac
  IFS=',' read -r -a __connectors <<< "$connectors"
  for connector in "${__connectors[@]}"; do
    connector_file "$connector"
  done
}

profile_files_csv() {
  local profile="$1"
  local out=''
  local file
  while IFS= read -r file; do
    if [ -n "$out" ]; then
      out="${out}:$file"
    else
      out="$file"
    fi
  done < <(profile_files "$profile")
  printf '%s
' "$out"
}

compose_cmd() {
  local profile="$1"
  local file
  local -a args=(compose)
  while IFS= read -r file; do
    args+=( -f "$ROOT_DIR/$file" )
  done < <(profile_files "$profile")
  printf '%s\n' "${args[@]}"
}

run_compose() {
  local profile="$1"
  shift
  local -a args=(compose)
  local file
  while IFS= read -r file; do
    args+=( -f "$ROOT_DIR/$file" )
  done < <(profile_files "$profile")
  docker "${args[@]}" "$@"
}

docker_ready() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

uv_ready() {
  command -v uv >/dev/null 2>&1
}


find_python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'python3'
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    printf '%s\n' 'python'
    return 0
  fi
  return 1
}

assert_python_compatible() {
  local python_cmd="$1"
  "$python_cmd" - <<'PY2'
import sys
if sys.version_info < (3, 12):
    raise SystemExit(
        f"Python 3.12+ is required, but {sys.version.split()[0]} was found."
    )
PY2
}

run_repo_python() {
  if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    "$VIRTUAL_ENV/bin/python" "$@"
    return 0
  fi
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    "$ROOT_DIR/.venv/bin/python" "$@"
    return 0
  fi
  if uv_ready; then
    (cd "$ROOT_DIR" && uv run python "$@")
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 "$@"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    python "$@"
    return 0
  fi
  fail 'No usable Python interpreter was found. Install Python 3.12+ and rerun the command.'
}

latest_backup_dir() {
  if [ ! -d "$BACKUP_ROOT" ]; then
    return 1
  fi
  find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1
}

postgres_dump() {
  local profile="$1"
  local output_file="$2"
  load_env
  if docker_ready; then
    run_compose "$profile" exec -T postgres pg_dump -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-retailops}" > "$output_file"
    return 0
  fi
  if command -v pg_dump >/dev/null 2>&1; then
    PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" pg_dump       -h "${POSTGRES_HOST:-localhost}"       -p "${POSTGRES_PORT:-5433}"       -U "${POSTGRES_USER:-postgres}"       -d "${POSTGRES_DB:-retailops}" > "$output_file"
    return 0
  fi
  return 1
}

postgres_restore() {
  local profile="$1"
  local input_file="$2"
  load_env
  if docker_ready; then
    run_compose "$profile" exec -T postgres psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-retailops}" < "$input_file"
    return 0
  fi
  if command -v psql >/dev/null 2>&1; then
    PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql       -h "${POSTGRES_HOST:-localhost}"       -p "${POSTGRES_PORT:-5433}"       -U "${POSTGRES_USER:-postgres}"       -d "${POSTGRES_DB:-retailops}" < "$input_file"
    return 0
  fi
  return 1
}

apply_sql_migrations() {
  local profile="$1"
  local -a migration_files=()
  local file
  load_env

  while IFS= read -r file; do
    migration_files+=("$file")
  done < <(find "$ROOT_DIR/core/db/migrations" -maxdepth 1 -type f -name '*.sql' | sort)

  if [ ${#migration_files[@]} -eq 0 ]; then
    warn 'No SQL migrations were found.'
    return 0
  fi

  if docker_ready; then
    for file in "${migration_files[@]}"; do
      log "Applying migration $(basename "$file") through Docker Compose"
      run_compose "$profile" exec -T postgres psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-retailops}" < "$file"
    done
    return 0
  fi

  if command -v psql >/dev/null 2>&1; then
    for file in "${migration_files[@]}"; do
      log "Applying migration $(basename "$file") through local psql"
      PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql         -v ON_ERROR_STOP=1         -h "${POSTGRES_HOST:-localhost}"         -p "${POSTGRES_PORT:-5433}"         -U "${POSTGRES_USER:-postgres}"         -d "${POSTGRES_DB:-retailops}" < "$file"
    done
    return 0
  fi

  warn 'Skipping SQL migration execution because neither Docker nor psql is available.'
}
