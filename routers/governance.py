import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from governance import evaluate_release, transition, validate_source
from models import User

router = APIRouter(prefix="/api/governance", tags=["governance"])


class SourceIn(BaseModel):
    source_uri: str
    publisher: str = Field(min_length=2)
    jurisdiction: str = Field(min_length=2)
    effective_at: datetime
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_version: str = Field(min_length=1)
    content_digest: str
    provenance: dict

    @field_validator("content_digest")
    @classmethod
    def sha256_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdefABCDEF" for char in value):
            raise ValueError("content_digest must be a SHA-256 hex digest")
        return value.lower()


class PolicyIn(BaseModel):
    policy_key: str = Field(pattern=r"^[A-Za-z0-9_.-]{2,80}$")
    body_digest: str
    reviewer_id: str
    retain_until: Optional[datetime] = None
    legal_hold: bool = False

    @field_validator("body_digest")
    @classmethod
    def sha256_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdefABCDEF" for char in value):
            raise ValueError("body_digest must be a SHA-256 hex digest")
        return value.lower()


class EvidenceIn(BaseModel):
    source_version_id: str
    locator: str = Field(min_length=1, max_length=300)
    obligation: str = Field(min_length=3, max_length=4000)
    owner_id: str
    deadline: datetime
    risk_rating: Literal["low", "medium", "high", "critical"]


class EvaluationIn(BaseModel):
    scenario: str = Field(min_length=3, max_length=1000)


class TransitionIn(BaseModel):
    target: Literal["review", "approval_pending", "changes_requested", "approved", "rejected", "released"]
    rationale: str = Field(min_length=5, max_length=2000)


class RetentionIn(BaseModel):
    retain_until: Optional[datetime] = None
    legal_hold: bool = False


def as_dict(row):
    return dict(row._mapping) if row else None


def policy_for(db: Session, policy_id: str, tenant_id: str, lock: bool = False):
    suffix = " FOR UPDATE" if lock else ""
    row = db.execute(text("SELECT * FROM governed_policy_versions WHERE id=CAST(:id AS UUID) AND tenant_id=:tenant" + suffix), {"id": policy_id, "tenant": tenant_id}).first()
    if not row:
        raise HTTPException(status_code=404, detail="Policy version not found")
    return as_dict(row)


def role_of(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


@router.post("/sources", status_code=201)
def ingest_source(payload: SourceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if role_of(user) not in {"admin", "analyst"}:
        raise HTTPException(status_code=403, detail="Analyst access required")
    source = payload.model_dump(mode="json")
    validate_source(source)
    previous = db.execute(text("SELECT content_digest, source_version FROM regulatory_source_versions WHERE tenant_id=:tenant AND source_uri=:uri ORDER BY retrieved_at DESC LIMIT 1"), {"tenant": user.tenant_id, "uri": payload.source_uri}).first()
    source_id = str(uuid.uuid4())
    try:
        row = db.execute(text("""INSERT INTO regulatory_source_versions
            (id,tenant_id,source_uri,publisher,jurisdiction,effective_at,retrieved_at,source_version,content_digest,provenance)
            VALUES(CAST(:id AS UUID),:tenant,:uri,:publisher,:jurisdiction,:effective,:retrieved,:version,:digest,CAST(:provenance AS JSONB)) RETURNING *"""),
            {"id": source_id, "tenant": user.tenant_id, "uri": payload.source_uri, "publisher": payload.publisher,
             "jurisdiction": payload.jurisdiction, "effective": payload.effective_at, "retrieved": payload.retrieved_at,
             "version": payload.source_version, "digest": payload.content_digest, "provenance": json.dumps(payload.provenance)}).first()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Source version already exists or violates provenance constraints")
    result = as_dict(row)
    result["changed"] = bool(previous and previous.content_digest != payload.content_digest)
    result["previous_version"] = previous.source_version if previous else None
    return result


@router.get("/sources")
def list_sources(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM regulatory_source_versions WHERE tenant_id=:tenant ORDER BY retrieved_at DESC"), {"tenant": user.tenant_id}).all()
    return [as_dict(row) for row in rows]


@router.post("/policies", status_code=201)
def create_policy(payload: PolicyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if role_of(user) not in {"admin", "analyst"}:
        raise HTTPException(status_code=403, detail="Analyst access required")
    reviewer = db.execute(text("SELECT id FROM users WHERE id=:id AND tenant_id=:tenant AND is_active"), {"id": payload.reviewer_id, "tenant": user.tenant_id}).first()
    if not reviewer or payload.reviewer_id == user.id:
        raise HTTPException(status_code=400, detail="An active, independent tenant reviewer is required")
    version = db.execute(text("SELECT COALESCE(MAX(version),0)+1 FROM governed_policy_versions WHERE tenant_id=:tenant AND policy_key=:key"), {"tenant": user.tenant_id, "key": payload.policy_key}).scalar_one()
    policy_id = str(uuid.uuid4())
    row = db.execute(text("""INSERT INTO governed_policy_versions
        (id,tenant_id,policy_key,version,status,owner_id,reviewer_id,body_digest,retain_until,legal_hold)
        VALUES(CAST(:id AS UUID),:tenant,:key,:version,'draft',:owner,:reviewer,:digest,:retain,:hold) RETURNING *"""),
        {"id": policy_id, "tenant": user.tenant_id, "key": payload.policy_key, "version": version, "owner": user.id,
         "reviewer": payload.reviewer_id, "digest": payload.body_digest, "retain": payload.retain_until, "hold": payload.legal_hold}).first()
    db.commit()
    return as_dict(row)


@router.get("/policies")
def list_policies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM governed_policy_versions WHERE tenant_id=:tenant ORDER BY created_at DESC"), {"tenant": user.tenant_id}).all()
    return [as_dict(row) for row in rows]


@router.get("/policies/{policy_id}")
def policy_detail(policy_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    policy = policy_for(db, policy_id, user.tenant_id)
    evidence = db.execute(text("""SELECT e.*,s.source_uri,s.publisher,s.jurisdiction,s.effective_at,s.content_digest
        FROM governed_evidence_links e JOIN regulatory_source_versions s ON s.id=e.source_version_id
        WHERE e.policy_version_id=CAST(:id AS UUID) AND s.tenant_id=:tenant ORDER BY e.deadline"""), {"id": policy_id, "tenant": user.tenant_id}).all()
    evaluations = db.execute(text("SELECT * FROM governed_evaluations WHERE policy_version_id=CAST(:id AS UUID) AND tenant_id=:tenant ORDER BY evaluated_at DESC"), {"id": policy_id, "tenant": user.tenant_id}).all()
    decisions = db.execute(text("SELECT * FROM governed_decisions WHERE policy_version_id=CAST(:id AS UUID) AND tenant_id=:tenant ORDER BY id"), {"id": policy_id, "tenant": user.tenant_id}).all()
    return {**policy, "evidence": [as_dict(row) for row in evidence], "evaluations": [as_dict(row) for row in evaluations], "decisions": [as_dict(row) for row in decisions]}


@router.post("/policies/{policy_id}/evidence", status_code=201)
def link_evidence(policy_id: str, payload: EvidenceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    policy = policy_for(db, policy_id, user.tenant_id)
    if role_of(user) != "admin" and policy["owner_id"] != user.id:
        raise HTTPException(status_code=403, detail="Policy owner access required")
    source = db.execute(text("SELECT id FROM regulatory_source_versions WHERE id=CAST(:id AS UUID) AND tenant_id=:tenant"), {"id": payload.source_version_id, "tenant": user.tenant_id}).first()
    owner = db.execute(text("SELECT id FROM users WHERE id=:id AND tenant_id=:tenant AND is_active"), {"id": payload.owner_id, "tenant": user.tenant_id}).first()
    if not source or not owner:
        raise HTTPException(status_code=400, detail="Evidence source and obligation owner must belong to the tenant")
    if payload.deadline <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Obligation deadline must be in the future")
    try:
        row = db.execute(text("""INSERT INTO governed_evidence_links(policy_version_id,source_version_id,locator,obligation,owner_id,deadline,risk_rating)
            VALUES(CAST(:policy AS UUID),CAST(:source AS UUID),:locator,:obligation,:owner,:deadline,:risk) RETURNING *"""),
            {"policy": policy_id, "source": payload.source_version_id, "locator": payload.locator, "obligation": payload.obligation,
             "owner": payload.owner_id, "deadline": payload.deadline, "risk": payload.risk_rating}).first()
        db.commit()
        return as_dict(row)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Evidence citation already exists")


@router.post("/policies/{policy_id}/evaluations", status_code=201)
def evaluate_policy(policy_id: str, payload: EvaluationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    policy_for(db, policy_id, user.tenant_id)
    rows = db.execute(text("""SELECT e.locator,e.obligation,e.owner_id,e.deadline,e.risk_rating,s.source_uri
        FROM governed_evidence_links e JOIN regulatory_source_versions s ON s.id=e.source_version_id
        WHERE e.policy_version_id=CAST(:id AS UUID) AND s.tenant_id=:tenant"""), {"id": policy_id, "tenant": user.tenant_id}).all()
    citations = [{"locator": row.locator, "source_uri": row.source_uri} for row in rows]
    obligations = [{"owner_id": row.owner_id, "deadline": row.deadline.isoformat(), "risk_rating": row.risk_rating} for row in rows]
    result = evaluate_release(citations, obligations)
    evaluation_id = str(uuid.uuid4())
    row = db.execute(text("""INSERT INTO governed_evaluations(id,tenant_id,policy_version_id,scenario,result,passed)
        VALUES(CAST(:id AS UUID),:tenant,CAST(:policy AS UUID),:scenario,CAST(:result AS JSONB),:passed) RETURNING *"""),
        {"id": evaluation_id, "tenant": user.tenant_id, "policy": policy_id, "scenario": payload.scenario,
         "result": json.dumps(result), "passed": result["passed"]}).first()
    db.commit()
    return as_dict(row)


@router.post("/policies/{policy_id}/transitions")
def transition_policy(policy_id: str, payload: TransitionIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        policy = policy_for(db, policy_id, user.tenant_id, lock=True)
        passed = bool(db.execute(text("SELECT passed FROM governed_evaluations WHERE policy_version_id=CAST(:id AS UUID) AND tenant_id=:tenant ORDER BY evaluated_at DESC LIMIT 1"), {"id": policy_id, "tenant": user.tenant_id}).scalar())
        target = transition(policy["status"], payload.target, role_of(user), policy["owner_id"], user.id,
                            reviewer_id=policy["reviewer_id"], approver_id=policy["approver_id"], evaluation_passed=passed)
        approver = user.id if target == "approved" else policy["approver_id"]
        updated = db.execute(text("UPDATE governed_policy_versions SET status=:target,approver_id=:approver WHERE id=CAST(:id AS UUID) AND tenant_id=:tenant RETURNING *"),
                             {"target": target, "approver": approver, "id": policy_id, "tenant": user.tenant_id}).first()
        snapshot = {**as_dict(updated), "id": str(updated.id), "created_at": updated.created_at.isoformat(), "retain_until": updated.retain_until.isoformat() if updated.retain_until else None}
        db.execute(text("""INSERT INTO governed_decisions(tenant_id,policy_version_id,from_status,to_status,actor_id,rationale,snapshot)
            VALUES(:tenant,CAST(:policy AS UUID),:from_status,:to_status,:actor,:rationale,CAST(:snapshot AS JSONB))"""),
            {"tenant": user.tenant_id, "policy": policy_id, "from_status": policy["status"], "to_status": target,
             "actor": user.id, "rationale": payload.rationale, "snapshot": json.dumps(snapshot)})
        db.commit()
        return as_dict(updated)
    except PermissionError as error:
        db.rollback(); raise HTTPException(status_code=403, detail=str(error))
    except ValueError as error:
        db.rollback(); raise HTTPException(status_code=409, detail=str(error))


@router.patch("/policies/{policy_id}/retention")
def update_retention(policy_id: str, payload: RetentionIn, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    policy_for(db, policy_id, user.tenant_id)
    try:
        row = db.execute(text("UPDATE governed_policy_versions SET retain_until=:retain, legal_hold=(legal_hold OR :hold) WHERE id=CAST(:id AS UUID) AND tenant_id=:tenant RETURNING *"),
                         {"retain": payload.retain_until, "hold": payload.legal_hold, "id": policy_id, "tenant": user.tenant_id}).first()
        db.commit(); return as_dict(row)
    except Exception as error:
        db.rollback(); raise HTTPException(status_code=409, detail=str(error))


@router.get("/audit-export")
def audit_export(user: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = Query(1000, ge=1, le=5000)):
    rows = db.execute(text("SELECT * FROM governed_decisions WHERE tenant_id=:tenant ORDER BY id LIMIT :limit"), {"tenant": user.tenant_id, "limit": limit}).all()
    records = [as_dict(row) for row in rows]
    canonical = json.dumps(records, default=str, sort_keys=True, separators=(",", ":"))
    return {"tenant_id": user.tenant_id, "generated_at": datetime.now(timezone.utc), "records": records, "sha256": hashlib.sha256(canonical.encode()).hexdigest(), "truncated": len(records) == limit}
