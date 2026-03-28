#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

PROFILE="standard"
RUN_SYNC=1
RUN_MIGRATIONS=1
RESTART_STACK=1

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

if [ "$RUN_SYNC" -eq 1 ]; then
  if uv_ready; then
    log "Refreshing Python dependencies"
    (cd "$ROOT_DIR" && uv sync --upgrade)
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
