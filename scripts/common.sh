#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="$ROOT_DIR/backups"

log() {
  printf '[INFO] %s\n' "$*"
}

warn() {
  printf '[WARN] %s\n' "$*" >&2
}

fail() {
  printf '[ERROR] %s\n' "$*" >&2
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

ensure_runtime_dirs() {
  mkdir -p \
    "$ROOT_DIR/backups" \
    "$ROOT_DIR/data/uploads" \
    "$ROOT_DIR/data/artifacts/transforms" \
    "$ROOT_DIR/data/artifacts/dashboards" \
    "$ROOT_DIR/data/artifacts/forecasts" \
    "$ROOT_DIR/data/artifacts/serving" \
    "$ROOT_DIR/data/artifacts/shipment_risk" \
    "$ROOT_DIR/data/artifacts/stockout_risk" \
    "$ROOT_DIR/data/artifacts/reorder" \
    "$ROOT_DIR/data/artifacts/model_registry" \
    "$ROOT_DIR/data/artifacts/returns_risk" \
    "$ROOT_DIR/data/artifacts/monitoring" \
    "$ROOT_DIR/data/artifacts/monitoring/overrides" \
    "$ROOT_DIR/data/artifacts/setup/sessions" \
    "$ROOT_DIR/data/artifacts/pro_platform/cdc" \
    "$ROOT_DIR/data/artifacts/pro_platform/streaming" \
    "$ROOT_DIR/data/artifacts/pro_platform/lakehouse" \
    "$ROOT_DIR/data/artifacts/pro_platform/query_layer" \
    "$ROOT_DIR/data/artifacts/pro_platform/metadata" \
    "$ROOT_DIR/data/artifacts/pro_platform/feature_store" \
    "$ROOT_DIR/data/artifacts/pro_platform/advanced_serving"
}

bootstrap_env_file() {
  local profile="$1"
  local sample_file="$ROOT_DIR/config/samples/${profile}.env"
  if [ ! -f "$ROOT_DIR/.env" ]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    log "Created .env from .env.example"
  fi
  if [ -f "$sample_file" ]; then
    python3 - "$ROOT_DIR/.env" "$sample_file" <<'PY'
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
PY
  fi
}

profile_files() {
  local profile="$1"
  case "$profile" in
    lite)
      printf '%s\n' \
        "compose/compose.core.yaml" \
        "compose/compose.connectors.yaml" \
        "compose/compose.analytics.yaml"
      ;;
    standard)
      printf '%s\n' \
        "compose/compose.core.yaml" \
        "compose/compose.connectors.yaml" \
        "compose/compose.analytics.yaml" \
        "compose/compose.ml.yaml" \
        "compose/compose.monitoring.yaml"
      ;;
    pro)
      printf '%s\n' \
        "compose/compose.core.yaml" \
        "compose/compose.connectors.yaml" \
        "compose/compose.analytics.yaml" \
        "compose/compose.ml.yaml" \
        "compose/compose.monitoring.yaml" \
        "compose/compose.cdc.yaml" \
        "compose/compose.streaming.yaml" \
        "compose/compose.lakehouse.yaml" \
        "compose/compose.query.yaml" \
        "compose/compose.metadata.yaml" \
        "compose/compose.feature_store.yaml" \
        "compose/compose.advanced_serving.yaml"
      ;;
    *)
      fail "Unsupported profile: $profile"
      ;;
  esac
}

compose_cmd() {
  local profile="$1"
  local -a args=(compose)
  while IFS= read -r file; do
    args+=( -f "$ROOT_DIR/$file" )
  done < <(profile_files "$profile")
  printf '%s\0' "${args[@]}"
}

run_compose() {
  local profile="$1"
  shift
  local -a args=()
  while IFS= read -r -d '' item; do
    args+=("$item")
  done < <(compose_cmd "$profile")
  docker "${args[@]}" "$@"
}

docker_ready() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

uv_ready() {
  command -v uv >/dev/null 2>&1
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
    PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" pg_dump \
      -h "${POSTGRES_HOST:-localhost}" \
      -p "${POSTGRES_PORT:-5433}" \
      -U "${POSTGRES_USER:-postgres}" \
      -d "${POSTGRES_DB:-retailops}" > "$output_file"
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
    PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql \
      -h "${POSTGRES_HOST:-localhost}" \
      -p "${POSTGRES_PORT:-5433}" \
      -U "${POSTGRES_USER:-postgres}" \
      -d "${POSTGRES_DB:-retailops}" < "$input_file"
    return 0
  fi
  return 1
}

apply_sql_migrations() {
  local profile="$1"
  load_env
  local -a migration_files=()
  while IFS= read -r file; do
    migration_files+=("$file")
  done < <(find "$ROOT_DIR/core/db/migrations" -maxdepth 1 -type f -name '*.sql' | sort)

  if [ ${#migration_files[@]} -eq 0 ]; then
    warn "No SQL migrations were found."
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
      PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql \
        -v ON_ERROR_STOP=1 \
        -h "${POSTGRES_HOST:-localhost}" \
        -p "${POSTGRES_PORT:-5433}" \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-retailops}" < "$file"
    done
    return 0
  fi

  warn "Skipping SQL migration execution because neither Docker nor psql is available."
}
