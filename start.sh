#!/bin/sh
set -eu
cd "$(dirname "$0")"
mode="${1:-check}"
case "$mode" in
  check) python -m unittest discover -s tests -v && (cd frontend && npm run build) ;;
  migrate) : "${DATABASE_URL:?DATABASE_URL is required}"; [ "${ALLOW_SCHEMA_MIGRATION:-}" = 1 ] || { echo 'Set ALLOW_SCHEMA_MIGRATION=1' >&2; exit 1; }; for migration in migrations/*.sql; do psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"; done ;;
  start) : "${DATABASE_URL:?DATABASE_URL is required}"; if [ "${AUTH_MODE:-local}" = oidc ]; then : "${OIDC_ISSUER:?OIDC_ISSUER is required}"; : "${OIDC_AUDIENCE:?OIDC_AUDIENCE is required}"; : "${OIDC_JWKS_URL:?OIDC_JWKS_URL is required}"; else : "${JWT_SECRET:?JWT_SECRET is required}"; [ "${#JWT_SECRET}" -ge 32 ] || exit 1; fi; exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" ;;
  *) echo 'usage: ./start.sh check|migrate|start' >&2; exit 2 ;;
esac
