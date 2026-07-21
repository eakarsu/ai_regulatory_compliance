# Completeness Review: ai_regulatory_compliance

**Review date:** 2026-07-18

## Assessment basis

Static inspection of project-owned source and configuration only; no dependency installation, build, database migration, external-service call, or runtime launch was performed. The scan considered 83 project files (74 source files), 2 manifest(s), 0 test-like file(s), and 0 CI workflow(s), excluding dependency/generated directories.

## Classification

**Functional but incomplete**

This is a substantive but unfinished governance/compliance application, not just an empty scaffold. Inspection found 74 source files across `frontend/`, `routers/` using Next.js, React, Python; however, the checked-in workflow and delivery controls do not yet demonstrate a complete, production-operable product.

## Why it is not complete

- Generated gap/visualization routes describe missing capabilities or simulate recommendations; they do not implement the underlying domain operation.
- Generic LLM calls are used as product behavior without enough typed tools, grounded evidence, deterministic rules, or output evaluation.
- Mock, demo, sample, fixture, or placeholder behavior remains in executable/product paths.
- No recognizable project-owned automated tests were found for the main workflow.
- No checked-in CI workflow proves builds, tests, migrations, and security checks on every change.

## Needed features

1. Replace advisory-only AI output with versioned policies, evidence links, accountable owners, approvals, and immutable decisions.
2. Add authoritative regulatory/contract ingestion with source provenance, effective dates, jurisdiction, and change detection.
3. Implement SSO, least-privilege RBAC, segregation of duties, retention/legal holds, and exportable audit logs.
4. Build scenario-specific evaluations so citations, obligations, deadlines, and risk ratings are checked before release.
5. Add risk-based unit, integration, and end-to-end tests in CI, including migration and failure-path coverage.

## Risks or launch blockers

- AI-provider availability, cost, privacy, prompt injection, and unvalidated output are launch risks until bounded and evaluated.
- Regression risk is high because no recognizable project-owned automated tests cover the main path.
- No CI evidence prevents broken or insecure changes from reaching a release.

## Evidence inspected

- `README.md`
- `frontend/src/App.tsx:22`
- `frontend/src/pages/AIAnalyzeRegulation.tsx:39`
- `auth.py`
- `requirements.txt`

## Recommended next action

Choose one real governance/compliance journey, define acceptance criteria and external contracts, then close its persistence, permission, integration, failure, and test gaps before expanding features.

## Implementation progress — 2026-07-19

1. Implemented the authenticated PostgreSQL API and Governed Release UI for versioned policies, immutable evidence/obligations, accountable owner/reviewer/approver roles, deterministic evaluations, legal holds/retention, and append-only decision snapshots. Independent review and approval are enforced before release.
2. Implemented tenant-scoped authoritative source ingestion with HTTPS validation, publisher, jurisdiction, effective/retrieval timestamps, source version, SHA-256 digest, provenance, duplicate rejection, and prior-version change detection. Sources and evidence links are database-immutable.
3. Added explicit tenant identity, tenant-scoped queries, database-backed role mapping, verified OIDC/JWKS bearer support, production refusal of local auth, administrator user provisioning, segregation of duties, irreversible legal holds, monotonic retention, and checksum-bearing tenant audit exports. Historic, generic-AI, and generated routes are opt-in outside production and impossible to enable in production.
4. Wired scenario evaluation to stored exact citations and obligations; each obligation requires an active tenant owner, future deadline, and bounded risk. A passing latest evaluation is mandatory for approval and release, and failure/SoD decisions return explicit conflicts.
5. Four tests pass: three deterministic governance unit tests plus a PostgreSQL API end-to-end test covering identity provisioning, source/policy/evidence persistence, evaluation, SoD failure, complete release, audit export, tenant isolation, and legacy-route quarantine. Ordered idempotent migrations replay, the UI builds, production frontend and Python dependency audits are clean, container/Compose, request-ID logs, health/readiness/metrics, backup/restore scripts, environment contract, and runbook are present, and a local backup/restore round trip reconciled all immutable decisions.

Readiness: all source-actionable review requirements for the governed release workflow are implemented. Launch still requires external OIDC and licensed feed credentials, counsel-approved jurisdiction scenarios/retention policy, representative acceptance, monitoring integration, and a witnessed restore drill.

## Runtime verification (2026-07-20)

- The explicit migration hook replayed the checked-in SQL into disposable PostgreSQL on port `55626`; the normal `start` path remained nondestructive and owned only API port `6066`.
- The acknowledgement-gated admin hook created a bcrypt-hashed PostgreSQL identity from environment-supplied credentials. Login succeeded through `/api/auth/login`, and `/api/auth/me` revalidated the bearer session against PostgreSQL.
- The first attempt recorded `FAILED` / `login_failed` because strict email validation rejected the verifier's reserved `.test` address. After allowing syntactically valid test-environment addresses, the retry recorded `API_VERIFIED` / `startup_login_session_api` in `_runtime_non_suite_repair_shard1l.tsv`.
- Python unit checks and the frontend production build passed.
