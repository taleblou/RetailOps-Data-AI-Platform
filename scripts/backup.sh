#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

PROFILE="standard"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET_DIR="$BACKUP_ROOT/$TIMESTAMP"
mkdir -p "$TARGET_DIR"

while [ $# -gt 0 ]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --output-dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

mkdir -p "$TARGET_DIR"
ensure_runtime_dirs
bootstrap_env_file "$PROFILE"

log "Creating file-system backup at $TARGET_DIR"
tar -czf "$TARGET_DIR/files.tar.gz" \
  -C "$ROOT_DIR" \
  .env .env.example README.md compose config docs/quickstart scripts data/demo_csv data/uploads data/artifacts

if postgres_dump "$PROFILE" "$TARGET_DIR/postgres.sql"; then
  log "Database dump created: $TARGET_DIR/postgres.sql"
else
  warn "Database dump skipped because PostgreSQL access tools were not available."
fi

cat > "$TARGET_DIR/manifest.json" <<EOF
{
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "profile": "$PROFILE",
  "root_dir": "$ROOT_DIR",
  "contains_files_archive": true,
  "contains_postgres_dump": $( [ -f "$TARGET_DIR/postgres.sql" ] && printf 'true' || printf 'false' )
}
EOF

log "Backup completed: $TARGET_DIR"
printf '%s\n' "$TARGET_DIR"
