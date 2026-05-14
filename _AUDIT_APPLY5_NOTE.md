# Apply Pass 5 — ai_regulatory_compliance

- **Date:** 2026-05-08
- **Project:** ai_regulatory_compliance
- **Stack:** Python / FastAPI + React (Vite + TS). SQLAlchemy + scheduler.py. Existing AI helper in `routers/ai.py` returns 503 when API key unset.
- **Audit source:** `/Users/erolakarsu/projects/_AUDIT/reports/batch_00.md` section 4
- **Action:** LEFT-AS-IS (verified prior pass-5 implementation present on disk)

## Audit detector false positive

Audit flagged "0 AI endpoints" — wrong. `routers/ai.py` already exposes `analyze-regulation`, `risk-assessment`, `gap-analysis`, `generate-policy`, `chat`, `chat/{session_id}`, `logs`, `compliance-summary/stream` (SSE). Plus `assessments.py` has `/{assessment_id}/run-ai`. Evidence collection lives at `routers/evidence.py`.

## Verified present

- AI policy generation → `/api/ai/generate-policy`
- AI compliance audit readiness (partial) → `/api/ai/gap-analysis` + `/api/ai/compliance-summary/stream`
- Streaming regulation alerts → `compliance-summary/stream` (SSE)
- Evidence collection → `routers/evidence.py` (upload/list/delete)
- FE pages: `AIAnalyzeRegulation`, `AIRiskAssessment`, `AIGapAnalysis`, `AIGeneratePolicy`, `AIChat`, `AIHistory`

## Implemented (verified on disk — pass-5 already done; 4 endpoints, within cap)

`routers/ai.py` extended (verified at lines 591, 676, 748, 826):

- `POST /api/ai/cross-regulation-mapper` (line 591) — defaults to 5 most-recently-updated regs when `regulation_ids` omitted
- `POST /api/ai/readiness-simulator` (line 676) — default scenario "surprise external audit next quarter"
- `POST /api/ai/evidence-extract` (line 748) — caller-supplied OCR text → structured evidence
- `POST /api/ai/external-feed/sec-edgar` (line 826) — NEEDS-CREDS `SEC_EDGAR_USER_AGENT` (503 when unset)

FE: `frontend/src/pages/AIBacklogTools.tsx` + `services/api.ts` (4 helpers) + `App.tsx` route + Nav link.

## Deferred

| Item | Category | Reason |
|---|---|---|
| Policy approval workflow | NEEDS-PRODUCT-DECISION | `PolicyApproval` model + signature/audit-trail design |
| ServiceNow / Salesforce Compliance Cloud | NEEDS-CREDS | OAuth + tenant config |
| Real OCR vision-model integration | NEEDS-PRODUCT-DECISION | Tesseract vs vision-LLM choice |
| FDA / EUR-Lex feeds | NEEDS-CREDS | Per-regulator clients |
| Mobile field auditor app | OUT-OF-SCOPE | Separate project |

## Smoke test

Per `_AUDIT_NOTE.md`: deferred (Postgres + Anthropic SDK install required). `python3 -m py_compile routers/ai.py` passed; `tsc --noEmit` shows no new errors in changed files.
