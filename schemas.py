from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator
import re


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    data: List[Any]
    pagination: PaginationMeta


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    organization: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    organization: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip() if v else v


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    organization: Optional[str]
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Regulation ────────────────────────────────────────────────────────────────

class RegulationCreate(BaseModel):
    title: str
    jurisdiction: str
    category: str
    summary: Optional[str] = None
    full_text: Optional[str] = None
    effective_date: Optional[date] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = True

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        allowed = {"GDPR", "HIPAA", "SOX", "PCI", "CCPA", "Other"}
        if v not in allowed:
            raise ValueError(f"category must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("jurisdiction")
    @classmethod
    def jurisdiction_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Jurisdiction cannot be empty")
        return v.strip()


class RequirementOut(BaseModel):
    id: str
    regulation_id: str
    requirement_text: str
    category: Optional[str]
    risk_level: str
    is_mandatory: bool

    model_config = {"from_attributes": True}


class RegulationOut(BaseModel):
    id: str
    title: str
    jurisdiction: str
    category: str
    summary: Optional[str]
    effective_date: Optional[date]
    last_updated: Optional[datetime]
    source_url: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class RegulationDetailOut(RegulationOut):
    full_text: Optional[str]
    requirements: List[RequirementOut] = []


class RegulationListOut(BaseModel):
    data: List[RegulationOut]
    pagination: PaginationMeta


# ── Assessment ────────────────────────────────────────────────────────────────

class AssessmentCreate(BaseModel):
    regulation_id: str
    next_review_date: Optional[datetime] = None

    @field_validator("regulation_id")
    @classmethod
    def regulation_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("regulation_id cannot be empty")
        return v.strip()


class RiskItemOut(BaseModel):
    id: str
    assessment_id: str
    title: str
    description: Optional[str]
    risk_level: str
    mitigation_plan: Optional[str]
    status: str
    due_date: Optional[datetime]

    model_config = {"from_attributes": True}


class RiskItemUpdate(BaseModel):
    status: Optional[str] = None
    mitigation_plan: Optional[str] = None
    due_date: Optional[datetime] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"open", "mitigated", "accepted"}:
            raise ValueError("status must be one of: open, mitigated, accepted")
        return v


class AssessmentOut(BaseModel):
    id: str
    user_id: str
    regulation_id: str
    regulation_title: Optional[str] = None
    overall_score: int
    status: str
    findings: Optional[List[Any]]
    recommendations: Optional[List[Any]]
    assessed_at: datetime
    next_review_date: Optional[datetime]

    model_config = {"from_attributes": True}


class AssessmentDetailOut(AssessmentOut):
    risk_items: List[RiskItemOut] = []


class AssessmentListOut(BaseModel):
    data: List[AssessmentOut]
    pagination: PaginationMeta


class AssessmentSnapshotOut(BaseModel):
    id: str
    assessment_id: str
    score: int
    status: str
    snapshot_at: datetime
    notes: Optional[str]

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_assessments: int
    compliant_count: int
    partial_count: int
    non_compliant_count: int
    compliance_rate_percent: float
    open_risks: int
    upcoming_reviews: int
    average_score: float


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: str
    user_id: str
    regulation_id: Optional[str]
    alert_type: str
    severity: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListOut(BaseModel):
    data: List[AlertOut]
    unread_count: int
    pagination: PaginationMeta


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceOut(BaseModel):
    id: str
    assessment_id: str
    risk_item_id: Optional[str]
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str]
    description: Optional[str]
    uploaded_by: Optional[str]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ── RegulationWatch ───────────────────────────────────────────────────────────

class RegulationWatchOut(BaseModel):
    id: str
    user_id: str
    regulation_id: str
    regulation_title: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Calendar ──────────────────────────────────────────────────────────────────

class CalendarEvent(BaseModel):
    date: str
    type: str   # "review_due", "overdue", "effective_date"
    title: str
    severity: str
    link: str
    assessment_id: Optional[str] = None
    regulation_id: Optional[str] = None


class CalendarOut(BaseModel):
    year: int
    month: int
    events: List[CalendarEvent]


# ── AI ────────────────────────────────────────────────────────────────────────

class AnalyzeRegulationRequest(BaseModel):
    regulation_text: str
    regulation_id: Optional[str] = None

    @field_validator("regulation_text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("regulation_text cannot be empty")
        if len(v) > 50000:
            raise ValueError("regulation_text must be under 50,000 characters")
        return v


class RiskAssessmentRequest(BaseModel):
    organization_type: str
    industry: str
    current_practices: List[str] = []

    @field_validator("organization_type", "industry")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("current_practices")
    @classmethod
    def practices_limit(cls, v: List[str]) -> List[str]:
        if len(v) > 100:
            raise ValueError("current_practices must have at most 100 items")
        return [p.strip() for p in v if p.strip()]


class GapAnalysisRequest(BaseModel):
    regulation_id: str
    stated_controls: List[str] = []

    @field_validator("regulation_id")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("regulation_id cannot be empty")
        return v.strip()

    @field_validator("stated_controls")
    @classmethod
    def controls_limit(cls, v: List[str]) -> List[str]:
        if len(v) > 200:
            raise ValueError("stated_controls must have at most 200 items")
        return [c.strip() for c in v if c.strip()]


class GeneratePolicyRequest(BaseModel):
    regulation_id: str
    organization_name: str
    organization_context: Optional[str] = None

    @field_validator("regulation_id", "organization_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("organization_context")
    @classmethod
    def context_limit(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 2000:
            raise ValueError("organization_context must be under 2000 characters")
        return v


class ChatRequest(BaseModel):
    message: str
    session_id: str
    context_assessment_id: Optional[str] = None
    context_regulation_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message cannot be empty")
        if len(v) > 4000:
            raise ValueError("message must be under 4000 characters")
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def session_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("session_id cannot be empty")
        return v.strip()


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AIAnalysisLogOut(BaseModel):
    id: str
    user_id: str
    analysis_type: str
    regulation_id: Optional[str]
    input_summary: Optional[str]
    result: Optional[Dict[str, Any]]
    tokens_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AILogListOut(BaseModel):
    data: List[AIAnalysisLogOut]
    pagination: PaginationMeta


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
