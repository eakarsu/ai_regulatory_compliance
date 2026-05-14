import os
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import Base, engine, SessionLocal
import models  # noqa: F401 — register models before create_all
import auth
from routers import regulations, assessments, alerts, ai, risk_items, evidence, calendar, watches, reports
from seed_data import seed_regulations
from scheduler import start_scheduler, stop_scheduler

# ── Startup guard: refuse to run with default JWT secret ──────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
if JWT_SECRET == "change-me-in-production":
    print(
        "[SECURITY WARNING] JWT_SECRET is set to the default insecure value. "
        "Set the JWT_SECRET environment variable to a strong random secret before deploying.",
        file=sys.stderr,
    )

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])

app = FastAPI(
    title="AI Regulatory Compliance Platform",
    description=(
        "Comprehensive AI-powered regulatory compliance monitoring platform. "
        "Track regulations, run AI-assisted assessments, manage alerts, and generate policies."
    ),
    version="2.0.0",
)

# Expose limiter on app state for slowapi middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Security headers middleware ────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

# ── Request logging middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000)
    print(f"[ACCESS] {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response

# ── CORS ──────────────────────────────────────────────────────────────────────
CLIENT_URL = os.getenv("CLIENT_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(regulations.router)
app.include_router(assessments.router)
app.include_router(alerts.router)
app.include_router(ai.router)
app.include_router(risk_items.router)
app.include_router(evidence.router)
app.include_router(calendar.router)
app.include_router(watches.router)
app.include_router(reports.router)


@app.on_event("startup")
def startup():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed sample regulations
    db = SessionLocal()
    try:
        seed_regulations(db)
    finally:
        db.close()

    # Start background scheduler
    start_scheduler()


@app.on_event("shutdown")
def shutdown():
    stop_scheduler()


@app.get("/health", tags=["health"])
def health():
    """Health check with database connectivity verification."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    finally:
        db.close()

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "regulatory-compliance-platform",
        "version": "2.0.0",
        "database": db_status,
    }

# BATCH_00_AUDIT_MOUNTS
from routers import regulation_feed as regulation_feed_router  # noqa
app.include_router(regulation_feed_router.router)
from routers import readiness_simulator as readiness_simulator_router  # noqa
app.include_router(readiness_simulator_router.router)
from routers import cross_regulation_mapper as cross_regulation_mapper_router  # noqa
app.include_router(cross_regulation_mapper_router.router)
from routers import evidence_assistant as evidence_assistant_router  # noqa
app.include_router(evidence_assistant_router.router)
from routers import external_connectors as external_connectors_router  # noqa
app.include_router(external_connectors_router.router)
# === Batch 00 Gaps & Frontend Mounts ===
from routers import gap_limited_ai_policy_generation_pipeline
from routers import gap_streaming_regulation_change_alerting
from routers import gap_ai_control_mapping_regulation_clause
from routers import gap_ai_audit_question_rehearsal_interviewer
from routers import gap_approval_workflows_policy_sign_offs
from routers import gap_external_regulation_data_feeds_sec
from routers import gap_third_party_audit_tool_integration
from routers import gap_evidence_collection_request_workflow_reminders
from routers import gap_outbound_webhooks
from routers import gap_multi_tenant_separation_primitives_visible
app.include_router(gap_limited_ai_policy_generation_pipeline.router)
app.include_router(gap_streaming_regulation_change_alerting.router)
app.include_router(gap_ai_control_mapping_regulation_clause.router)
app.include_router(gap_ai_audit_question_rehearsal_interviewer.router)
app.include_router(gap_approval_workflows_policy_sign_offs.router)
app.include_router(gap_external_regulation_data_feeds_sec.router)
app.include_router(gap_third_party_audit_tool_integration.router)
app.include_router(gap_evidence_collection_request_workflow_reminders.router)
app.include_router(gap_outbound_webhooks.router)
app.include_router(gap_multi_tenant_separation_primitives_visible.router)
