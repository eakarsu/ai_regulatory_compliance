"""Deterministic governance invariants used by API handlers and tests."""
from datetime import datetime, timezone
from urllib.parse import urlparse

TRANSITIONS = {"draft": {"review"}, "review": {"approval_pending", "changes_requested"}, "changes_requested": {"review"}, "approval_pending": {"approved", "rejected"}, "approved": {"released"}}
GRANTS = {"analyst": {("draft", "review"), ("changes_requested", "review")}, "admin": {("draft", "review"), ("changes_requested", "review"), ("review", "approval_pending"), ("review", "changes_requested"), ("approval_pending", "approved"), ("approval_pending", "rejected"), ("approved", "released")}}

def validate_source(source):
    required = ("source_uri", "publisher", "jurisdiction", "effective_at", "source_version", "content_digest")
    if any(not source.get(key) for key in required) or urlparse(source["source_uri"]).scheme != "https":
        raise ValueError("authoritative HTTPS source provenance is required")
    datetime.fromisoformat(source["effective_at"].replace("Z", "+00:00"))
    return source

def evaluate_release(citations, obligations):
    failures = []
    if not citations or any(not c.get("locator") or not c.get("source_uri") for c in citations): failures.append("citations")
    if not obligations or any(not o.get("owner_id") or not o.get("deadline") or o.get("risk_rating") not in {"low","medium","high","critical"} for o in obligations): failures.append("obligations")
    return {"passed": not failures, "failures": failures, "evaluated_at": datetime.now(timezone.utc).isoformat()}

def transition(status, target, role, owner_id, actor_id, reviewer_id=None, approver_id=None, evaluation_passed=False):
    if target not in TRANSITIONS.get(status, set()) or (status, target) not in GRANTS.get(role, set()): raise PermissionError("forbidden transition")
    if status in {"draft", "changes_requested"} and actor_id != owner_id: raise PermissionError("only the owner may submit a policy")
    if status == "review" and target == "approval_pending" and actor_id != reviewer_id: raise PermissionError("assigned reviewer required")
    if target in {"approved", "released"} and actor_id in {owner_id, reviewer_id}: raise ValueError("segregation of duties violation")
    if target == "released" and approver_id and actor_id != approver_id: raise ValueError("approver must release the approved policy")
    if target in {"approved", "released"} and not evaluation_passed: raise ValueError("passing evaluation required")
    return target
