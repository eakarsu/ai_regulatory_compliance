import asyncio
import json
import os
import uuid
from typing import AsyncGenerator, List

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import AIAnalysisLog, ChatMessage, ComplianceAssessment, Regulation, RiskItem, User
from schemas import (
    AIAnalysisLogOut, AILogListOut, AnalyzeRegulationRequest,
    ChatMessageOut, ChatRequest,
    GapAnalysisRequest, GeneratePolicyRequest,
    PaginationMeta, RiskAssessmentRequest,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])

MODEL = "claude-3-5-sonnet-20241022"
SYSTEM_PROMPT = (
    "You are a regulatory compliance expert with deep knowledge of GDPR, HIPAA, SOX, PCI DSS, "
    "CCPA, and other major regulatory frameworks. Always respond with valid JSON when requested. "
    "Be precise, actionable, and risk-aware in your analysis."
)


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    return anthropic.Anthropic(api_key=api_key)


def parse_ai_json(text: str):
    """Robust multi-strategy JSON extraction."""
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


def _save_log(
    db: Session,
    user_id: str,
    analysis_type: str,
    input_summary: str,
    result: dict,
    tokens: int,
    regulation_id: str = None,
) -> AIAnalysisLog:
    log = AIAnalysisLog(
        user_id=user_id,
        analysis_type=analysis_type,
        regulation_id=regulation_id,
        input_summary=input_summary,
        result=result,
        tokens_used=tokens,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.post("/analyze-regulation", response_model=AIAnalysisLogOut)
def analyze_regulation(
    payload: AnalyzeRegulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = _get_client()

    prompt = f"""Analyze the following regulation text and extract structured compliance information.

Regulation Text:
{payload.regulation_text[:8000]}

Respond with ONLY valid JSON:
{{
  "key_requirements": ["list of specific requirements"],
  "risk_areas": [
    {{"area": "string", "description": "string", "risk_level": "low|medium|high|critical"}}
  ],
  "compliance_steps": ["ordered list of steps to achieve compliance"],
  "affected_business_functions": ["list of business areas impacted"],
  "penalties_for_non_compliance": "string describing penalties",
  "estimated_compliance_effort": "low|medium|high",
  "timeline_to_compliance": "string e.g. 3-6 months",
  "key_definitions": [{{"term": "string", "definition": "string"}}],
  "summary": "brief 2-3 sentence summary"
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        result = parse_ai_json(content)
        if result is None:
            result = {"raw_response": content, "parse_error": "Could not extract JSON"}
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    log = _save_log(
        db,
        user_id=current_user.id,
        analysis_type="analyze_regulation",
        input_summary=payload.regulation_text[:200],
        result=result,
        tokens=tokens,
        regulation_id=payload.regulation_id,
    )
    return AIAnalysisLogOut.model_validate(log)


@router.post("/risk-assessment", response_model=AIAnalysisLogOut)
def risk_assessment(
    payload: RiskAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = _get_client()

    prompt = f"""Evaluate the compliance risk profile for the following organization.

Organization Type: {payload.organization_type}
Industry: {payload.industry}
Current Practices:
{json.dumps(payload.current_practices, indent=2)}

Respond with ONLY valid JSON:
{{
  "overall_risk_score": 0,
  "risk_level": "low|medium|high|critical",
  "applicable_regulations": ["list of regulations that likely apply with jurisdiction"],
  "compliance_gaps": [
    {{"gap": "string", "regulation": "string", "priority": "high|medium|low", "impact": "string", "estimated_cost": "string"}}
  ],
  "immediate_actions": ["top 5 immediate actions needed"],
  "medium_term_roadmap": ["actions for 3-6 months"],
  "long_term_roadmap": ["actions for 6-18 months"],
  "estimated_compliance_cost": "string e.g. $50,000 - $200,000",
  "top_risks": [
    {{"risk": "string", "likelihood": "high|medium|low", "impact": "high|medium|low", "mitigation": "string"}}
  ],
  "strengths": ["existing practices that are commendable"],
  "industry_benchmarks": "string describing how this org compares to peers"
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        result = parse_ai_json(content)
        if result is None:
            result = {"raw_response": content, "parse_error": "Could not extract JSON"}
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    log = _save_log(
        db,
        user_id=current_user.id,
        analysis_type="risk_assessment",
        input_summary=f"{payload.organization_type} in {payload.industry}",
        result=result,
        tokens=tokens,
    )
    return AIAnalysisLogOut.model_validate(log)


@router.post("/gap-analysis", response_model=AIAnalysisLogOut)
def gap_analysis(
    payload: GapAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    regulation = db.query(Regulation).filter(Regulation.id == payload.regulation_id).first()
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")

    client = _get_client()

    requirements_text = "\n".join(
        f"- [{r.risk_level.upper()}] {r.requirement_text}"
        for r in regulation.requirements
    ) or regulation.summary or "No specific requirements available."

    prompt = f"""Compare the organization's stated controls against regulation requirements and identify gaps.

Regulation: {regulation.title} ({regulation.category})
Requirements:
{requirements_text}

Organization's Stated Controls:
{json.dumps(payload.stated_controls, indent=2)}

Respond with ONLY valid JSON:
{{
  "covered_requirements": ["requirements that are adequately addressed"],
  "gaps": [
    {{
      "requirement": "string",
      "gap_description": "string",
      "severity": "low|medium|high|critical",
      "remediation": "string",
      "estimated_effort_days": 0,
      "estimated_cost": "string"
    }}
  ],
  "partial_coverage": [
    {{"requirement": "string", "what_is_missing": "string", "what_is_covered": "string"}}
  ],
  "gap_score": 0,
  "compliance_percentage": 0,
  "overall_gap_summary": "string",
  "prioritized_remediation_plan": ["ordered list of remediation steps"],
  "quick_wins": ["controls that can be implemented in < 2 weeks"],
  "total_estimated_effort_days": 0
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=3500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        result = parse_ai_json(content)
        if result is None:
            result = {"raw_response": content, "parse_error": "Could not extract JSON"}
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    log = _save_log(
        db,
        user_id=current_user.id,
        analysis_type="gap_analysis",
        input_summary=f"Gap analysis against {regulation.title}",
        result=result,
        tokens=tokens,
        regulation_id=regulation.id,
    )
    return AIAnalysisLogOut.model_validate(log)


@router.post("/generate-policy", response_model=AIAnalysisLogOut)
def generate_policy(
    payload: GeneratePolicyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    regulation = db.query(Regulation).filter(Regulation.id == payload.regulation_id).first()
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")

    client = _get_client()

    requirements_text = "\n".join(
        f"- {r.requirement_text}"
        for r in regulation.requirements
    ) or regulation.summary or ""

    prompt = f"""Generate a comprehensive compliance policy document for the following organization and regulation.

Organization: {payload.organization_name}
Additional Context: {payload.organization_context or 'N/A'}
Regulation: {regulation.title} ({regulation.category}, {regulation.jurisdiction})
Summary: {regulation.summary}
Key Requirements:
{requirements_text}

Generate a structured policy document as ONLY valid JSON:
{{
  "policy_title": "string",
  "version": "1.0",
  "effective_date": "YYYY-MM-DD",
  "review_date": "YYYY-MM-DD",
  "scope": "string describing who and what is covered",
  "purpose": "string explaining why this policy exists",
  "definitions": [{{"term": "string", "definition": "string"}}],
  "policy_sections": [
    {{
      "section_number": "1",
      "title": "string",
      "content": "string",
      "subsections": [{{"number": "1.1", "title": "string", "content": "string"}}]
    }}
  ],
  "roles_and_responsibilities": [
    {{"role": "string", "responsibilities": ["string"]}}
  ],
  "procedures": [{{"title": "string", "steps": ["string"]}}],
  "exceptions": "string describing how to request policy exceptions",
  "enforcement": "string describing consequences of non-compliance",
  "review_cycle": "string e.g. Annual",
  "document_owner": "string e.g. Chief Compliance Officer",
  "related_policies": ["string"],
  "references": ["string"]
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=5000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        result = parse_ai_json(content)
        if result is None:
            result = {"raw_response": content, "parse_error": "Could not extract JSON"}
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    log = _save_log(
        db,
        user_id=current_user.id,
        analysis_type="generate_policy",
        input_summary=f"Policy for {payload.organization_name} re: {regulation.title}",
        result=result,
        tokens=tokens,
        regulation_id=regulation.id,
    )
    return AIAnalysisLogOut.model_validate(log)


@router.post("/chat", response_model=ChatMessageOut)
def compliance_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI compliance chat assistant with conversation history."""
    client = _get_client()

    # Build context
    context_parts = []
    if payload.context_assessment_id:
        assessment = db.query(ComplianceAssessment).filter(
            ComplianceAssessment.id == payload.context_assessment_id,
            ComplianceAssessment.user_id == current_user.id,
        ).first()
        if assessment:
            reg = db.query(Regulation).filter(Regulation.id == assessment.regulation_id).first()
            risk_items = db.query(RiskItem).filter(
                RiskItem.assessment_id == assessment.id
            ).limit(10).all()
            context_parts.append(
                f"Assessment context: Regulation={reg.title if reg else 'Unknown'}, "
                f"Score={assessment.overall_score}/100, Status={assessment.status}, "
                f"Open risks: {len([r for r in risk_items if r.status == 'open'])}"
            )

    if payload.context_regulation_id:
        reg = db.query(Regulation).filter(
            Regulation.id == payload.context_regulation_id
        ).first()
        if reg:
            context_parts.append(
                f"Regulation context: {reg.title} ({reg.category}, {reg.jurisdiction}). "
                f"Summary: {reg.summary}"
            )

    # Load conversation history (last 10 messages)
    history = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == payload.session_id,
            ChatMessage.user_id == current_user.id,
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(10)
        .all()
    )

    messages = [{"role": m.role, "content": m.content} for m in history]

    # Add current user message
    user_content = payload.message
    if context_parts:
        user_content = f"[Context: {'; '.join(context_parts)}]\n\n{payload.message}"
    messages.append({"role": "user", "content": user_content})

    system = (
        "You are a regulatory compliance assistant helping a compliance professional. "
        "You have expertise in GDPR, HIPAA, SOX, PCI DSS, CCPA, and other frameworks. "
        "Give clear, actionable advice. Be concise but thorough. "
        f"User organization: {current_user.organization or 'Not specified'}."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=system,
            messages=messages,
        )
        assistant_content = response.content[0].text
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    # Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        session_id=payload.session_id,
        role="user",
        content=payload.message,
        context_assessment_id=payload.context_assessment_id,
        context_regulation_id=payload.context_regulation_id,
    )
    db.add(user_msg)

    # Save assistant response
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        session_id=payload.session_id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatMessageOut.model_validate(assistant_msg)


@router.get("/chat/{session_id}", response_model=List[ChatMessageOut])
def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full chat history for a session."""
    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == current_user.id,
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [ChatMessageOut.model_validate(m) for m in messages]


@router.get("/logs", response_model=AILogListOut)
def list_ai_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    analysis_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List AI analysis history for the current user."""
    q = db.query(AIAnalysisLog).filter(AIAnalysisLog.user_id == current_user.id)
    if analysis_type:
        q = q.filter(AIAnalysisLog.analysis_type == analysis_type)

    total = q.count()
    logs = (
        q.order_by(AIAnalysisLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return AILogListOut(
        data=[AIAnalysisLogOut.model_validate(log) for log in logs],
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit if total > 0 else 1,
        ),
    )


@router.get("/compliance-summary/stream")
async def stream_compliance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE endpoint that streams a compliance status summary and persists the result."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    assessments = (
        db.query(ComplianceAssessment)
        .filter(ComplianceAssessment.user_id == current_user.id)
        .limit(20)
        .all()
    )

    assessment_summaries = []
    for a in assessments:
        reg = db.query(Regulation).filter(Regulation.id == a.regulation_id).first()
        assessment_summaries.append({
            "regulation": reg.title if reg else a.regulation_id,
            "score": a.overall_score,
            "status": a.status,
            "findings_count": len(a.findings or []),
            "open_risks": len([r for r in a.risk_items if r.status == "open"]),
        })

    user_id = current_user.id

    async def event_generator() -> AsyncGenerator[str, None]:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Provide an executive compliance summary for an organization with {len(assessments)} assessments.

Assessment Data:
{json.dumps(assessment_summaries, indent=2)}

Cover: overall posture, key risks, immediate priorities, positive progress, and recommended next steps.
Be concise (200-300 words), executive-friendly, and action-oriented."""

        full_text = ""
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=1200,
                system="You are a Chief Compliance Officer providing an executive briefing.",
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text_chunk in stream.text_stream:
                    full_text += text_chunk
                    yield f"data: {json.dumps({'chunk': text_chunk})}\n\n"
                    await asyncio.sleep(0)

            # Persist the streamed result
            db_session = db
            log = AIAnalysisLog(
                user_id=user_id,
                analysis_type="compliance_summary_stream",
                input_summary=f"Compliance summary for {len(assessments)} assessments",
                result={"summary": full_text, "assessment_count": len(assessments)},
                tokens_used=0,
            )
            db_session.add(log)
            db_session.commit()

            yield "data: [DONE]\n\n"
        except anthropic.APIError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Apply pass 5 — remaining backlog (additive endpoints)
# All endpoints below are new and do not modify existing behavior.
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/cross-regulation-mapper")
def cross_regulation_mapper(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PRODUCT-DECISION: Map overlapping requirements across multiple regulations to
    surface where a single control can satisfy several frameworks.
    Body: {regulation_ids: [str, ...]} - 2 to 8 regulation IDs.
    Default behavior picks all regulations the user can read if list omitted (capped
    at 5 most-recently-updated), so the endpoint stays usable without UX work.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    client = anthropic.Anthropic(api_key=api_key)

    reg_ids = (payload or {}).get("regulation_ids") or []
    if reg_ids:
        regs = db.query(Regulation).filter(Regulation.id.in_(reg_ids[:8])).all()
    else:
        regs = (
            db.query(Regulation)
            .order_by(Regulation.updated_at.desc() if hasattr(Regulation, "updated_at") else Regulation.id)
            .limit(5)
            .all()
        )
    if len(regs) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 regulations to map overlaps")

    summaries = [
        {
            "id": r.id,
            "title": r.title,
            "category": getattr(r, "category", None),
            "jurisdiction": getattr(r, "jurisdiction", None),
            "summary": (getattr(r, "summary", None) or "")[:1500],
            "requirements": [
                getattr(req, "requirement_text", "")[:300]
                for req in (getattr(r, "requirements", []) or [])[:25]
            ],
        }
        for r in regs
    ]

    prompt = f"""You are mapping overlapping compliance requirements across multiple regulations.

REGULATIONS:
{json.dumps(summaries, indent=2)}

Identify where a single control or process satisfies multiple regulations and where
they diverge. Respond with ONLY valid JSON:
{{
  "shared_themes": [{{"theme": "string", "regulations": ["id"], "common_requirement": "string"}}],
  "single_control_opportunities": [{{"control": "string", "covers": ["id"], "rationale": "string"}}],
  "divergences": [{{"topic": "string", "by_regulation": [{{"id": "string", "stance": "string"}}]}}],
  "consolidated_action_plan": ["ordered steps that minimize duplicate work"],
  "summary": "2-3 sentence executive summary"
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        result = parse_ai_json(content) or {"raw_response": content, "parse_error": "Could not extract JSON"}
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    log = _save_log(
        db,
        user_id=current_user.id,
        analysis_type="cross_regulation_mapper",
        input_summary=f"Mapping across {len(regs)} regulations",
        result=result,
        tokens=tokens,
    )
    return AIAnalysisLogOut.model_validate(log)


@router.post("/readiness-simulator")
def readiness_simulator(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PRODUCT-DECISION: Compliance readiness simulator. Reuses gap-analysis style
    prompting over a hypothetical scenario rather than actual stated controls.
    Body: {scenario: str, regulation_id?: str, controls_in_place?: [str], event?: str}
    Default scenario when omitted: "surprise audit next quarter".
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    client = anthropic.Anthropic(api_key=api_key)

    body = payload or {}
    scenario = (body.get("scenario") or "surprise external audit next quarter").strip()
    controls = body.get("controls_in_place") or []
    event = body.get("event") or "regulatory inspection"
    regulation_id = body.get("regulation_id")
    reg_context = ""
    if regulation_id:
        reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
        if reg:
            reg_context = f"Target regulation: {reg.title} ({getattr(reg, 'category', '')})\n{(getattr(reg, 'summary', '') or '')[:1500]}"

    prompt = f"""Run a readiness simulation against a hypothetical compliance event.

EVENT: {event}
SCENARIO: {scenario}
CONTROLS IN PLACE:
{json.dumps(controls, indent=2)}
{reg_context}

Respond ONLY with valid JSON:
{{
  "readiness_score": 0,
  "readiness_level": "low|medium|high",
  "likely_findings": [{{"finding": "string", "severity": "low|medium|high|critical", "evidence_required": "string"}}],
  "what_will_pass": ["string"],
  "what_will_fail": ["string"],
  "remediation_before_event": ["ordered steps"],
  "estimated_remediation_days": 0,
  "executive_summary": "2-3 sentences"
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        result = parse_ai_json(content) or {"raw_response": content, "parse_error": "Could not extract JSON"}
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    log = _save_log(
        db,
        user_id=current_user.id,
        analysis_type="readiness_simulator",
        input_summary=f"Readiness simulation: {scenario[:100]}",
        result=result,
        tokens=tokens,
    )
    return AIAnalysisLogOut.model_validate(log)


@router.post("/evidence-extract")
def evidence_extract(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PRODUCT-DECISION: OCR-driven evidence assistant. We do not run OCR locally;
    the caller supplies already-extracted text (e.g. from Tesseract or a vision
    model). This endpoint takes the text and structures it as compliance evidence,
    matched against optional regulation requirements.
    Body: {extracted_text: str, regulation_id?: str, document_type?: str}
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    client = anthropic.Anthropic(api_key=api_key)

    body = payload or {}
    text = (body.get("extracted_text") or "").strip()
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="extracted_text is required (>=10 chars)")
    document_type = body.get("document_type") or "uncategorized"
    regulation_id = body.get("regulation_id")
    reg_block = ""
    if regulation_id:
        reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
        if reg:
            reg_block = (
                f"\nTarget regulation: {reg.title}\n"
                f"Requirements:\n"
                + "\n".join(f"- {getattr(r, 'requirement_text', '')[:200]}" for r in (getattr(reg, 'requirements', []) or [])[:20])
            )

    prompt = f"""Structure the following OCR-extracted text as compliance evidence.

DOCUMENT TYPE: {document_type}
EXTRACTED TEXT (truncated to 6000 chars):
{text[:6000]}
{reg_block}

Respond ONLY with valid JSON:
{{
  "document_classification": "string",
  "key_facts": ["string"],
  "named_entities": [{{"type": "person|org|date|amount|location", "value": "string"}}],
  "supports_requirements": [{{"requirement": "string", "evidence_quote": "string", "confidence": "low|medium|high"}}],
  "contradicts_requirements": [{{"requirement": "string", "evidence_quote": "string"}}],
  "missing_info_needed": ["string"],
  "ocr_quality": "good|partial|poor",
  "summary": "2-3 sentences"
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        result = parse_ai_json(content) or {"raw_response": content, "parse_error": "Could not extract JSON"}
        tokens = response.usage.input_tokens + response.usage.output_tokens
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {str(e)}")

    log = _save_log(
        db,
        user_id=current_user.id,
        analysis_type="evidence_extract",
        input_summary=f"OCR evidence extract: {document_type}",
        result=result,
        tokens=tokens,
        regulation_id=regulation_id,
    )
    return AIAnalysisLogOut.model_validate(log)


@router.post("/external-feed/sec-edgar")
def sec_edgar_feed(payload: dict, current_user: User = Depends(get_current_user)):
    """
    NEEDS-CREDS: External regulation feed connector for SEC EDGAR.
    Documented env vars (none of which need to be live for local dev):
      SEC_EDGAR_USER_AGENT — required by SEC; format "Org Name email@example.com"
      SEC_EDGAR_BASE_URL   — defaults to https://data.sec.gov
    Returns 503 with `missing: SEC_EDGAR_USER_AGENT` when unset, since the SEC
    rejects requests without a contact UA.
    """
    user_agent = os.getenv("SEC_EDGAR_USER_AGENT")
    if not user_agent:
        raise HTTPException(
            status_code=503,
            detail={"error": "SEC EDGAR feed unavailable", "missing": "SEC_EDGAR_USER_AGENT"},
        )
    # When configured, this would call data.sec.gov endpoints. Keep stub
    # behavior so we don't introduce a new HTTP client dependency.
    cik = (payload or {}).get("cik")
    return {
        "status": "configured",
        "user_agent_present": True,
        "base_url": os.getenv("SEC_EDGAR_BASE_URL", "https://data.sec.gov"),
        "cik_requested": cik,
        "note": "Live fetch implementation pending; credentials accepted.",
    }

