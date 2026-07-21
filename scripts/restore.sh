#!/bin/sh
set -eu
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"
[ "${ALLOW_DATABASE_RESTORE:-}" = 1 ] || { echo 'Set ALLOW_DATABASE_RESTORE=1 during an approved maintenance window' >&2; exit 1; }
[ -f "$BACKUP_FILE" ] || { echo "Backup not found: $BACKUP_FILE" >&2; exit 1; }
pg_restore --list "$BACKUP_FILE" >/dev/null
pg_restore --dbname="$DATABASE_URL" --clean --if-exists --no-owner --single-transaction "$BACKUP_FILE"
echo "Restore completed from: $BACKUP_FILE"
