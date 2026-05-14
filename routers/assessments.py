import json
import os
from datetime import datetime, timedelta
from typing import List

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import (
    AssessmentSnapshot, ComplianceAssessment, ComplianceAlert, AIAnalysisLog,
    Regulation, RiskItem, User, AssessmentStatus, AlertSeverity
)
from schemas import (
    AssessmentCreate, AssessmentDetailOut, AssessmentListOut, AssessmentOut,
    AssessmentSnapshotOut, DashboardStats, PaginationMeta, RiskItemOut,
)

router = APIRouter(prefix="/api/assessments", tags=["assessments"])

MODEL = "claude-3-5-sonnet-20241022"


def _parse_ai_json(text: str):
    """Robust JSON extraction from AI response."""
    import json
    try:
        return json.loads(text)
    except Exception:
        pass
    stripped = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(stripped)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass
    return None


def _get_assessment_or_404(assessment_id: str, user: User, db: Session) -> ComplianceAssessment:
    a = db.query(ComplianceAssessment).filter(
        ComplianceAssessment.id == assessment_id,
        ComplianceAssessment.user_id == user.id,
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return a


def _assessment_out(a: ComplianceAssessment) -> AssessmentOut:
    """Build AssessmentOut with regulation title included."""
    data = AssessmentOut.model_validate(a)
    if a.regulation:
        data.regulation_title = a.regulation.title
    return data


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessments = (
        db.query(ComplianceAssessment)
        .filter(ComplianceAssessment.user_id == current_user.id)
        .all()
    )
    total = len(assessments)
    compliant = sum(1 for a in assessments if a.status == AssessmentStatus.compliant)
    partial = sum(1 for a in assessments if a.status == AssessmentStatus.partial)
    non_compliant = sum(1 for a in assessments if a.status == AssessmentStatus.non_compliant)

    now = datetime.utcnow()
    upcoming_cutoff = now + timedelta(days=30)
    upcoming = sum(
        1 for a in assessments
        if a.next_review_date and now < a.next_review_date <= upcoming_cutoff
    )

    open_risks = (
        db.query(RiskItem)
        .join(ComplianceAssessment)
        .filter(
            ComplianceAssessment.user_id == current_user.id,
            RiskItem.status == "open",
        )
        .count()
    )

    compliance_rate = (compliant / total * 100) if total > 0 else 0.0
    avg_score = (sum(a.overall_score for a in assessments) / total) if total > 0 else 0.0

    return DashboardStats(
        total_assessments=total,
        compliant_count=compliant,
        partial_count=partial,
        non_compliant_count=non_compliant,
        compliance_rate_percent=round(compliance_rate, 1),
        open_risks=open_risks,
        upcoming_reviews=upcoming,
        average_score=round(avg_score, 1),
    )


@router.get("", response_model=AssessmentListOut)
def list_assessments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(ComplianceAssessment)
        .filter(ComplianceAssessment.user_id == current_user.id)
    )
    if status_filter:
        q = q.filter(ComplianceAssessment.status == status_filter)

    total = q.count()
    assessments = (
        q.order_by(ComplianceAssessment.assessed_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return AssessmentListOut(
        data=[_assessment_out(a) for a in assessments],
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit if total > 0 else 1,
        ),
    )


@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reg = db.query(Regulation).filter(Regulation.id == payload.regulation_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")

    assessment = ComplianceAssessment(
        user_id=current_user.id,
        regulation_id=payload.regulation_id,
        next_review_date=payload.next_review_date,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return _assessment_out(assessment)


@router.get("/{assessment_id}", response_model=AssessmentDetailOut)
def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = _get_assessment_or_404(assessment_id, current_user, db)
    out = AssessmentDetailOut.model_validate(a)
    if a.regulation:
        out.regulation_title = a.regulation.title
    return out


@router.get("/{assessment_id}/history", response_model=List[AssessmentSnapshotOut])
def get_assessment_history(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return score history snapshots for trend analysis."""
    a = _get_assessment_or_404(assessment_id, current_user, db)
    snapshots = (
        db.query(AssessmentSnapshot)
        .filter(AssessmentSnapshot.assessment_id == a.id)
        .order_by(AssessmentSnapshot.snapshot_at.asc())
        .all()
    )
    return [AssessmentSnapshotOut.model_validate(s) for s in snapshots]


@router.post("/{assessment_id}/run-ai", response_model=AssessmentDetailOut)
def run_ai_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = _get_assessment_or_404(assessment_id, current_user, db)
    regulation = db.query(Regulation).filter(Regulation.id == assessment.regulation_id).first()
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    requirements_text = "\n".join(
        f"- [{r.risk_level.upper()}] {r.requirement_text}"
        for r in regulation.requirements
    ) or "No specific requirements listed."

    prompt = f"""You are a compliance expert. Analyze the compliance status for the following regulation and generate a comprehensive assessment.

Regulation: {regulation.title} ({regulation.category})
Jurisdiction: {regulation.jurisdiction}
Summary: {regulation.summary}

Key Requirements:
{requirements_text}

Generate a compliance assessment with:
1. An overall compliance score (0-100)
2. Compliance status: compliant (80-100), partial (50-79), non_compliant (0-49)
3. Specific findings
4. Actionable recommendations
5. Risk items that need attention

Respond with ONLY valid JSON, no other text:
{{
  "overall_score": number,
  "status": "compliant|partial|non_compliant",
  "findings": [
    {{"area": "string", "observation": "string", "severity": "low|medium|high|critical"}}
  ],
  "recommendations": [
    {{"priority": "high|medium|low", "action": "string", "timeline": "string"}}
  ],
  "risk_items": [
    {{
      "title": "string",
      "description": "string",
      "risk_level": "low|medium|high|critical",
      "mitigation_plan": "string"
    }}
  ],
  "next_review_days": number
}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system="You are a regulatory compliance expert. Always respond with valid JSON only.",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        result = _parse_ai_json(content)
        if result is None:
            raise HTTPException(status_code=502, detail="Failed to parse AI response as JSON")
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    # Validate status value before DB write
    valid_statuses = {"compliant", "partial", "non_compliant"}
    ai_status = result.get("status", "non_compliant")
    # normalize hyphenated variant
    ai_status = ai_status.replace("-", "_")
    if ai_status not in valid_statuses:
        ai_status = "non_compliant"

    # Save snapshot of previous state before updating
    db.add(AssessmentSnapshot(
        assessment_id=assessment.id,
        score=assessment.overall_score,
        status=assessment.status,
        notes="Snapshot before AI assessment run",
    ))

    # Update assessment
    assessment.overall_score = max(0, min(100, int(result.get("overall_score", 0))))
    assessment.status = ai_status
    assessment.findings = result.get("findings", [])
    assessment.recommendations = result.get("recommendations", [])
    assessment.assessed_at = datetime.utcnow()

    next_days = max(1, int(result.get("next_review_days", 90)))
    assessment.next_review_date = datetime.utcnow() + timedelta(days=next_days)

    # Clear old risk items and create new ones
    db.query(RiskItem).filter(RiskItem.assessment_id == assessment.id).delete()
    for ri in result.get("risk_items", []):
        rl = ri.get("risk_level", "medium")
        if rl not in {"low", "medium", "high", "critical"}:
            rl = "medium"
        db.add(RiskItem(
            assessment_id=assessment.id,
            title=ri.get("title", "Risk"),
            description=ri.get("description"),
            risk_level=rl,
            mitigation_plan=ri.get("mitigation_plan"),
        ))

    # Log AI usage
    db.add(AIAnalysisLog(
        user_id=current_user.id,
        analysis_type="run_assessment",
        regulation_id=regulation.id,
        input_summary=f"Assessment for {regulation.title}",
        result=result,
        tokens_used=tokens,
    ))

    db.commit()
    db.refresh(assessment)
    out = AssessmentDetailOut.model_validate(assessment)
    if assessment.regulation:
        out.regulation_title = assessment.regulation.title
    return out
