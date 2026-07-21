# Governed compliance runbook

The governed release path records immutable authoritative source versions with provenance and change detection, separately versioned policies, exact citations and owned obligations, deterministic scenario evaluations, independent review/approval/release decisions, retention/legal holds, and checksum-bearing audit exports. AI and historic CRUD surfaces are non-authoritative and unavailable by default; they cannot be enabled in production.

Run `./start.sh check`. CI creates PostgreSQL, applies all ordered migrations twice, runs four unit/API workflow tests, builds the UI and containers, and audits Python/production frontend dependencies. Deploy migrations as a one-shot `ALLOW_SCHEMA_MIGRATION=1 ./start.sh migrate` job before starting the API. Production requires OIDC; tenant and role mapping remain locally provisioned and cannot be supplied by token claims.

Use `compose.yaml` as the reference topology. `/health` is liveness, `/ready` verifies PostgreSQL, `/metrics` exposes request counters, and logs are structured JSON with request IDs. Alert on readiness failures, 5xx/error ratio, authentication failures, rejected segregation-of-duties transitions, overdue critical obligations, failed source polling, database saturation, and backup age. Run the optional scheduler on one elected instance only.

Create and verify a restricted backup with `DATABASE_URL=... BACKUP_FILE=/approved/path/compliance.dump ./scripts/backup.sh`. Restore only to the exact approved target during maintenance with `ALLOW_DATABASE_RESTORE=1`, rehearse quarterly, and reconcile tenant/source/policy/evidence/evaluation/decision counts plus audit-export hashes. Legal-hold release is deliberately not exposed and requires a separate counsel-approved procedure.
