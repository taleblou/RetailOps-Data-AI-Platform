#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

PROFILE="lite"
START_STACK=1
RUN_SYNC=1
CONNECTORS_OVERRIDE=""
OPTIONAL_EXTRAS_OVERRIDE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --connectors)
      CONNECTORS_OVERRIDE="$2"
      shift 2
      ;;
    --list-connectors)
      all_connectors
      exit 0
      ;;
    --extras)
      OPTIONAL_EXTRAS_OVERRIDE="$2"
      shift 2
      ;;
    --list-extras)
      all_optional_extras
      exit 0
      ;;
    --no-docker)
      START_STACK=0
      shift
      ;;
    --skip-sync)
      RUN_SYNC=0
      shift
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

ensure_runtime_dirs
bootstrap_env_file "$PROFILE"

if [ -n "$CONNECTORS_OVERRIDE" ]; then
  PROFILE_CONNECTORS_OVERRIDE="$(normalize_connector_list "$CONNECTORS_OVERRIDE")"
else
  PROFILE_CONNECTORS_OVERRIDE="$(profile_default_connectors "$PROFILE")"
fi
export PROFILE_CONNECTORS_OVERRIDE

if [ -n "$OPTIONAL_EXTRAS_OVERRIDE" ]; then
  PROFILE_OPTIONAL_EXTRAS_OVERRIDE="$(normalize_optional_extra_list "$OPTIONAL_EXTRAS_OVERRIDE")"
else
  PROFILE_OPTIONAL_EXTRAS_OVERRIDE="$(profile_default_extras "$PROFILE")"
fi
export PROFILE_OPTIONAL_EXTRAS_OVERRIDE

update_env_value "$ROOT_DIR/.env" "APP_PROFILE" "$PROFILE"
update_env_value "$ROOT_DIR/.env" "ENABLED_CONNECTORS" "$PROFILE_CONNECTORS_OVERRIDE"
update_env_value "$ROOT_DIR/.env" "ENABLED_OPTIONAL_EXTRAS" "$PROFILE_OPTIONAL_EXTRAS_OVERRIDE"
update_env_value "$ROOT_DIR/.env" "COMPOSE_FILES" "$(profile_files_csv "$PROFILE")"

log "Selected profile: $PROFILE"
log "Enabled connectors: $PROFILE_CONNECTORS_OVERRIDE"
if [ -n "$PROFILE_OPTIONAL_EXTRAS_OVERRIDE" ]; then
  log "Enabled optional extras: $PROFILE_OPTIONAL_EXTRAS_OVERRIDE"
else
  log "Enabled optional extras: none"
fi

if [ "$RUN_SYNC" -eq 1 ]; then
  if uv_ready; then
    log "Installing Python dependencies with uv"
    UV_EXTRA_ARGS=()
    while IFS= read -r extra; do
      if [ -n "$extra" ]; then
        UV_EXTRA_ARGS+=(--extra "$extra")
      fi
    done < <(extras_as_lines "$PROFILE_OPTIONAL_EXTRAS_OVERRIDE")
    (cd "$ROOT_DIR" && uv sync "${UV_EXTRA_ARGS[@]}")
  else
    warn "uv is not installed. Skipping dependency installation."
  fi
fi

if [ "$START_STACK" -eq 1 ]; then
  if docker_ready; then
    log "Starting Docker Compose profile: $PROFILE"
    run_compose "$PROFILE" up -d
  else
    warn "Docker is not available. The files are ready, but containers were not started."
  fi
fi

log "Installation completed for profile '$PROFILE'."
log "Quickstart guide: docs/quickstart/${PROFILE}.md"
