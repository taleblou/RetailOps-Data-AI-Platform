#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

PROFILE="lite"
START_STACK=1
RUN_SYNC=1

while [ $# -gt 0 ]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
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

if [ "$RUN_SYNC" -eq 1 ]; then
  if uv_ready; then
    log "Installing Python dependencies with uv"
    (cd "$ROOT_DIR" && uv sync)
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
