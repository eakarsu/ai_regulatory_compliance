import json
import os
import time
import uuid
from collections import Counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text

from database import SessionLocal
import auth
from routers import governance as governance_router
from scheduler import start_scheduler, stop_scheduler

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
AUTH_MODE = os.getenv("AUTH_MODE", "local")
if ENVIRONMENT == "production":
    required_oidc = ["OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL"]
    missing = [key for key in required_oidc if not os.getenv(key)]
    insecure = any(not os.getenv(key, "").startswith("https://") for key in ["OIDC_ISSUER", "OIDC_JWKS_URL"])
    if AUTH_MODE != "oidc" or missing or insecure:
        raise RuntimeError(f"Production requires OIDC authentication; missing: {', '.join(missing) or 'AUTH_MODE=oidc'}")
elif AUTH_MODE == "local" and len(os.getenv("JWT_SECRET", "")) < 32:
    raise RuntimeError("JWT_SECRET of at least 32 characters is required for local authentication")

limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])
app = FastAPI(title="Governed Regulatory Compliance Platform", version="3.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
request_totals: Counter[tuple[str, int]] = Counter()


@app.middleware("http")
async def security_and_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    started = time.monotonic()
    response = await call_next(request)
    response.headers.update({
        "X-Request-Id": request_id, "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin", "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    })
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    request_totals[(request.method, response.status_code)] += 1
    print(json.dumps({"level": "info", "event": "http_request", "request_id": request_id, "method": request.method,
                      "path": request.url.path, "status": response.status_code, "duration_ms": round((time.monotonic() - started) * 1000)}))
    return response


client_url = os.getenv("CLIENT_URL", "http://localhost:5173")
app.add_middleware(CORSMiddleware, allow_origins=[client_url], allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-Id"])

app.include_router(auth.router)
app.include_router(governance_router.router)

# Historic CRUD, generic AI, generated gaps, and sample integrations do not have
# the governed tenant/evidence guarantees. They can only be inspected in a
# non-production sandbox with explicit operator intent.
if os.getenv("ENABLE_LEGACY_ROUTES", "false").lower() == "true" and ENVIRONMENT != "production":
    from routers import regulations, assessments, alerts, ai, risk_items, evidence, calendar, watches, reports
    from routers import regulation_feed, readiness_simulator, cross_regulation_mapper, evidence_assistant, external_connectors
    from routers import gap_limited_ai_policy_generation_pipeline, gap_streaming_regulation_change_alerting
    from routers import gap_ai_control_mapping_regulation_clause, gap_ai_audit_question_rehearsal_interviewer
    from routers import gap_approval_workflows_policy_sign_offs, gap_external_regulation_data_feeds_sec
    from routers import gap_third_party_audit_tool_integration, gap_evidence_collection_request_workflow_reminders
    from routers import gap_outbound_webhooks, gap_multi_tenant_separation_primitives_visible, control_attestation_queue
    for legacy in [regulations, assessments, alerts, ai, risk_items, evidence, calendar, watches, reports,
                   regulation_feed, readiness_simulator, cross_regulation_mapper, evidence_assistant, external_connectors,
                   gap_limited_ai_policy_generation_pipeline, gap_streaming_regulation_change_alerting,
                   gap_ai_control_mapping_regulation_clause, gap_ai_audit_question_rehearsal_interviewer,
                   gap_approval_workflows_policy_sign_offs, gap_external_regulation_data_feeds_sec,
                   gap_third_party_audit_tool_integration, gap_evidence_collection_request_workflow_reminders,
                   gap_outbound_webhooks, gap_multi_tenant_separation_primitives_visible, control_attestation_queue]:
        app.include_router(legacy.router)


@app.on_event("startup")
def startup():
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        start_scheduler()


@app.on_event("shutdown")
def shutdown():
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        stop_scheduler()


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy", "service": "regulatory-compliance-platform", "version": "3.0.0"}


@app.get("/ready", tags=["health"])
def ready():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="database unavailable")
    finally:
        db.close()


@app.get("/metrics", response_class=PlainTextResponse, tags=["health"])
def metrics():
    lines = [f'http_requests_total{{method="{method}",status="{status}"}} {count}' for (method, status), count in sorted(request_totals.items())]
    return "\n".join(lines) + "\n"
