#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

PROFILE="standard"
RUN_SYNC=1
RUN_MIGRATIONS=1
RESTART_STACK=1
OPTIONAL_EXTRAS_OVERRIDE="__UNSET__"

while [ $# -gt 0 ]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --skip-sync)
      RUN_SYNC=0
      shift
      ;;
    --extras)
      OPTIONAL_EXTRAS_OVERRIDE="$2"
      shift 2
      ;;
    --skip-migrations)
      RUN_MIGRATIONS=0
      shift
      ;;
    --no-restart)
      RESTART_STACK=0
      shift
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

ensure_runtime_dirs
bootstrap_env_file "$PROFILE"

if [ "$OPTIONAL_EXTRAS_OVERRIDE" != "__UNSET__" ]; then
  PROFILE_OPTIONAL_EXTRAS_OVERRIDE="$(normalize_optional_extra_list "$OPTIONAL_EXTRAS_OVERRIDE")"
  export PROFILE_OPTIONAL_EXTRAS_OVERRIDE
  update_env_value "$ROOT_DIR/.env" "ENABLED_OPTIONAL_EXTRAS" "$PROFILE_OPTIONAL_EXTRAS_OVERRIDE"
fi

if [ "$RUN_SYNC" -eq 1 ]; then
  if uv_ready; then
    log "Refreshing Python dependencies"
    RESOLVED_OPTIONAL_EXTRAS="$(resolve_enabled_extras "$PROFILE")"
    UV_EXTRA_ARGS=()
    while IFS= read -r extra; do
      if [ -n "$extra" ]; then
        UV_EXTRA_ARGS+=(--extra "$extra")
      fi
    done < <(extras_as_lines "$RESOLVED_OPTIONAL_EXTRAS")
    (cd "$ROOT_DIR" && uv sync --upgrade "${UV_EXTRA_ARGS[@]}")
  else
    warn "uv is not installed. Skipping dependency refresh."
  fi
fi

if [ "$RUN_MIGRATIONS" -eq 1 ]; then
  apply_sql_migrations "$PROFILE"
fi

if [ "$RESTART_STACK" -eq 1 ] && docker_ready; then
  log "Pulling updated images for profile '$PROFILE'"
  run_compose "$PROFILE" pull
  log "Restarting services for profile '$PROFILE'"
  run_compose "$PROFILE" up -d --build
fi

log "Upgrade routine completed for profile '$PROFILE'."
