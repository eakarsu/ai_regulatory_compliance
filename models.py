import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Text,
    ForeignKey, Date, Enum as SAEnum, BigInteger
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
import enum

from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class RegulationCategory(str, enum.Enum):
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    SOX = "SOX"
    PCI = "PCI"
    CCPA = "CCPA"
    Other = "Other"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AssessmentStatus(str, enum.Enum):
    compliant = "compliant"
    partial = "partial"
    non_compliant = "non_compliant"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class RiskItemStatus(str, enum.Enum):
    open = "open"
    mitigated = "mitigated"
    accepted = "accepted"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    organization = Column(String)
    role = Column(SAEnum(UserRole), default=UserRole.analyst, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessments = relationship("ComplianceAssessment", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("ComplianceAlert", back_populates="user", cascade="all, delete-orphan")
    ai_logs = relationship("AIAnalysisLog", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    watched_regulations = relationship("RegulationWatch", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    jurisdiction = Column(String, nullable=False)
    category = Column(SAEnum(RegulationCategory), nullable=False)
    summary = Column(Text)
    full_text = Column(Text)
    effective_date = Column(Date)
    last_updated = Column(DateTime, default=datetime.utcnow)
    source_url = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    content_hash = Column(String)  # for change detection

    requirements = relationship("ComplianceRequirement", back_populates="regulation", cascade="all, delete-orphan")
    assessments = relationship("ComplianceAssessment", back_populates="regulation")
    alerts = relationship("ComplianceAlert", back_populates="regulation")
    ai_logs = relationship("AIAnalysisLog", back_populates="regulation")
    watchers = relationship("RegulationWatch", back_populates="regulation", cascade="all, delete-orphan")


class ComplianceRequirement(Base):
    __tablename__ = "compliance_requirements"

    id = Column(String, primary_key=True, default=gen_uuid)
    regulation_id = Column(String, ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False)
    requirement_text = Column(Text, nullable=False)
    category = Column(String)
    risk_level = Column(SAEnum(RiskLevel), default=RiskLevel.medium, nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)

    regulation = relationship("Regulation", back_populates="requirements")


class ComplianceAssessment(Base):
    __tablename__ = "compliance_assessments"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    regulation_id = Column(String, ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Integer, default=0)
    status = Column(SAEnum(AssessmentStatus), default=AssessmentStatus.non_compliant, nullable=False)
    findings = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    assessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    next_review_date = Column(DateTime)

    user = relationship("User", back_populates="assessments")
    regulation = relationship("Regulation", back_populates="assessments")
    risk_items = relationship("RiskItem", back_populates="assessment", cascade="all, delete-orphan")
    snapshots = relationship("AssessmentSnapshot", back_populates="assessment", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentSnapshot(Base):
    """Score history for trend tracking."""
    __tablename__ = "assessment_snapshots"

    id = Column(String, primary_key=True, default=gen_uuid)
    assessment_id = Column(String, ForeignKey("compliance_assessments.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    status = Column(SAEnum(AssessmentStatus), nullable=False)
    snapshot_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)

    assessment = relationship("ComplianceAssessment", back_populates="snapshots")


class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    regulation_id = Column(String, ForeignKey("regulations.id", ondelete="SET NULL"), nullable=True)
    alert_type = Column(String, nullable=False)
    severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.info, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # deduplication key: prevents duplicate alerts for same event
    dedup_key = Column(String, index=True)

    user = relationship("User", back_populates="alerts")
    regulation = relationship("Regulation", back_populates="alerts")


class RiskItem(Base):
    __tablename__ = "risk_items"

    id = Column(String, primary_key=True, default=gen_uuid)
    assessment_id = Column(String, ForeignKey("compliance_assessments.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    risk_level = Column(SAEnum(RiskLevel), default=RiskLevel.medium, nullable=False)
    mitigation_plan = Column(Text)
    status = Column(SAEnum(RiskItemStatus), default=RiskItemStatus.open, nullable=False)
    due_date = Column(DateTime)

    assessment = relationship("ComplianceAssessment", back_populates="risk_items")
    evidence = relationship("Evidence", back_populates="risk_item", cascade="all, delete-orphan")


class Evidence(Base):
    """File evidence attached to assessments or risk items."""
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=gen_uuid)
    assessment_id = Column(String, ForeignKey("compliance_assessments.id", ondelete="CASCADE"), nullable=False)
    risk_item_id = Column(String, ForeignKey("risk_items.id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # local path or S3 key
    file_size = Column(BigInteger, default=0)
    mime_type = Column(String)
    description = Column(Text)
    uploaded_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("ComplianceAssessment", back_populates="evidence")
    risk_item = relationship("RiskItem", back_populates="evidence")


class AIAnalysisLog(Base):
    __tablename__ = "ai_analysis_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_type = Column(String, nullable=False)
    regulation_id = Column(String, ForeignKey("regulations.id", ondelete="SET NULL"), nullable=True)
    input_summary = Column(Text)
    result = Column(JSON, default=dict)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="ai_logs")
    regulation = relationship("Regulation", back_populates="ai_logs")


class AuditLog(Base):
    """General audit trail for all user actions."""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)  # e.g. "create_assessment", "delete_alert"
    resource_type = Column(String)           # e.g. "assessment", "regulation"
    resource_id = Column(String)
    details = Column(JSON, default=dict)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")


class RegulationWatch(Base):
    """User subscription to a regulation for change alerts."""
    __tablename__ = "regulation_watches"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    regulation_id = Column(String, ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="watched_regulations")
    regulation = relationship("Regulation", back_populates="watchers")


class ChatMessage(Base):
    """AI compliance chat assistant messages."""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    context_assessment_id = Column(String, ForeignKey("compliance_assessments.id", ondelete="SET NULL"), nullable=True)
    context_regulation_id = Column(String, ForeignKey("regulations.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="chat_messages")
