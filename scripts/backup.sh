#!/bin/sh
set -eu
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"
umask 077
pg_dump --dbname="$DATABASE_URL" --format=custom --no-owner --file="$BACKUP_FILE"
pg_restore --list "$BACKUP_FILE" >/dev/null
echo "Verified PostgreSQL backup: $BACKUP_FILE"
