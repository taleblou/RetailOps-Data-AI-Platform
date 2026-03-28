#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

PROFILE="standard"
BACKUP_DIR=""
SKIP_DB=0

while [ $# -gt 0 ]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --backup-dir)
      BACKUP_DIR="$2"
      shift 2
      ;;
    --latest)
      BACKUP_DIR="$(latest_backup_dir || true)"
      shift
      ;;
    --skip-db)
      SKIP_DB=1
      shift
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

if [ -z "$BACKUP_DIR" ]; then
  fail "Pass --backup-dir <path> or use --latest"
fi
if [ ! -d "$BACKUP_DIR" ]; then
  fail "Backup directory does not exist: $BACKUP_DIR"
fi

if [ -f "$BACKUP_DIR/files.tar.gz" ]; then
  log "Restoring files from $BACKUP_DIR/files.tar.gz"
  tar -xzf "$BACKUP_DIR/files.tar.gz" -C "$ROOT_DIR"
else
  warn "No files.tar.gz found in $BACKUP_DIR"
fi

if [ "$SKIP_DB" -eq 0 ] && [ -f "$BACKUP_DIR/postgres.sql" ]; then
  if postgres_restore "$PROFILE" "$BACKUP_DIR/postgres.sql"; then
    log "Database restore completed from $BACKUP_DIR/postgres.sql"
  else
    warn "Database restore skipped because PostgreSQL access tools were not available."
  fi
fi

log "Restore completed from $BACKUP_DIR"
