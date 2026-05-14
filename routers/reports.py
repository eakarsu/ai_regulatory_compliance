"""Compliance report generation endpoints."""
import json
import os
from datetime import datetime

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import AIAnalysisLog, ComplianceAssessment, Regulation, RiskItem, User

router = APIRouter(prefix="/api/reports", tags=["reports"])

MODEL = "claude-3-5-sonnet-20241022"


@router.get("/assessment/{assessment_id}")
def generate_assessment_report(
    assessment_id: str,
    template: str = Query("executive", regex="^(executive|technical|audit)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a narrative compliance report for an assessment."""
    assessment = db.query(ComplianceAssessment).filter(
        ComplianceAssessment.id == assessment_id,
        ComplianceAssessment.user_id == current_user.id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    regulation = db.query(Regulation).filter(Regulation.id == assessment.regulation_id).first()
    risk_items = db.query(RiskItem).filter(RiskItem.assessment_id == assessment_id).all()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    template_guidance = {
        "executive": "Write for a C-suite audience. Focus on business risk, overall posture, and strategic priorities. Keep it concise (1-2 pages equivalent). Use plain language.",
        "technical": "Write for a technical compliance team. Include detailed findings, specific control gaps, technical remediation steps, and implementation timelines.",
        "audit": "Write in formal audit report style. Include scope, methodology, findings with evidence references, risk ratings, management responses section, and conclusion.",
    }

    findings_text = json.dumps(assessment.findings or [], indent=2)
    recommendations_text = json.dumps(assessment.recommendations or [], indent=2)
    risks_text = "\n".join(
        f"- [{ri.risk_level.upper()}] {ri.title}: {ri.description or ''} (Status: {ri.status})"
        for ri in risk_items
    )

    prompt = f"""Generate a {template} compliance report for the following assessment.

{template_guidance[template]}

Regulation: {regulation.title if regulation else 'Unknown'} ({regulation.category if regulation else 'N/A'})
Jurisdiction: {regulation.jurisdiction if regulation else 'N/A'}
Assessment Date: {assessment.assessed_at.strftime('%Y-%m-%d')}
Overall Score: {assessment.overall_score}/100
Status: {assessment.status}
Next Review: {assessment.next_review_date.strftime('%Y-%m-%d') if assessment.next_review_date else 'Not set'}

Findings:
{findings_text}

Recommendations:
{recommendations_text}

Risk Items:
{risks_text or 'None identified'}

Prepared for: {current_user.organization or current_user.name}

Write the complete report as markdown text."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system="You are a compliance report writer producing professional audit and compliance documentation.",
            messages=[{"role": "user", "content": prompt}],
        )
        report_text = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    # Log AI usage
    db.add(AIAnalysisLog(
        user_id=current_user.id,
        analysis_type=f"report_{template}",
        regulation_id=assessment.regulation_id,
        input_summary=f"{template.title()} report for {regulation.title if regulation else 'Unknown'}",
        result={"report_length": len(report_text), "template": template},
        tokens_used=tokens,
    ))
    db.commit()

    return PlainTextResponse(
        content=report_text,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="compliance-report-{assessment_id[:8]}.md"'
        },
    )


@router.get("/cross-regulation")
def cross_regulation_comparison(
    regulation_ids: str = Query(..., description="Comma-separated regulation IDs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI-powered comparison of requirements across multiple regulations."""
    ids = [r.strip() for r in regulation_ids.split(",") if r.strip()]
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 regulation IDs required")
    if len(ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 regulations for comparison")

    regs = db.query(Regulation).filter(Regulation.id.in_(ids)).all()
    if len(regs) < 2:
        raise HTTPException(status_code=404, detail="One or more regulations not found")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    reg_texts = []
    for reg in regs:
        reqs = "\n".join(f"  - {r.requirement_text}" for r in reg.requirements)
        reg_texts.append(f"## {reg.title} ({reg.category})\nRequirements:\n{reqs}")

    prompt = f"""Compare the following regulations and identify overlapping controls and unique requirements.

{chr(10).join(reg_texts)}

Respond with ONLY valid JSON:
{{
  "regulations_compared": ["list of regulation names"],
  "overlapping_controls": [
    {{
      "theme": "string",
      "description": "string",
      "regulations_requiring": ["list of regulation names"],
      "implementation_note": "string"
    }}
  ],
  "unique_to_each": [
    {{
      "regulation": "string",
      "unique_requirements": ["list of requirements unique to this regulation"]
    }}
  ],
  "recommended_unified_control_framework": ["controls that satisfy multiple regulations simultaneously"],
  "implementation_priority": ["ordered list of controls to implement first for max coverage"],
  "overlap_percentage": 0,
  "summary": "string"
}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system="You are a regulatory compliance expert specializing in multi-framework compliance programs.",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        from routers.ai import parse_ai_json
        result = parse_ai_json(content)
        if result is None:
            result = {"raw_response": content}
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    # Log
    db.add(AIAnalysisLog(
        user_id=current_user.id,
        analysis_type="cross_regulation_comparison",
        input_summary=f"Comparison of {len(regs)} regulations",
        result=result,
        tokens_used=tokens,
    ))
    db.commit()

    return result
