#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

PROFILE="standard"
load_env

api_port="${API_PORT:-8000}"
health_url="http://127.0.0.1:${api_port}/health"
missing=0

for required in \
  "$ROOT_DIR/README.md" \
  "$ROOT_DIR/pyproject.toml" \
  "$ROOT_DIR/compose/compose.core.yaml" \
  "$ROOT_DIR/docs/quickstart/lite.md" \
  "$ROOT_DIR/docs/quickstart/standard.md" \
  "$ROOT_DIR/docs/quickstart/pro.md" \
  "$ROOT_DIR/docs/pro_data_platform_phase20.md" \
  "$ROOT_DIR/compose/compose.streaming.yaml" \
  "$ROOT_DIR/compose/compose.query.yaml" \
  "$ROOT_DIR/compose/compose.feature_store.yaml" \
  "$ROOT_DIR/compose/compose.advanced_serving.yaml"; do
  if [ ! -e "$required" ]; then
    warn "Missing required file: $required"
    missing=1
  fi
done

if python3 - <<PY >/dev/null 2>&1
import urllib.request
urllib.request.urlopen('$health_url', timeout=2)
PY
then
  log "API health endpoint is reachable at $health_url"
else
  warn "API health endpoint is not reachable at $health_url"
fi

if docker_ready; then
  log "Docker is available. Active services for profile '$PROFILE':"
  run_compose "$PROFILE" ps || true
else
  warn "Docker is not available for compose health inspection."
fi

if [ "$missing" -ne 0 ]; then
  fail "Static health checks failed."
fi

log "Static health checks completed."
