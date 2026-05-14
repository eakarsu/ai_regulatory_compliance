"""Evidence upload and management for compliance assessments."""
import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ComplianceAssessment, Evidence, RiskItem, User
from schemas import EvidenceOut

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

UPLOAD_DIR = os.getenv("EVIDENCE_UPLOAD_DIR", "/tmp/compliance_evidence")


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    assessment_id: str = Form(...),
    risk_item_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload evidence file linked to an assessment (and optionally a risk item)."""
    # Verify assessment belongs to user
    assessment = db.query(ComplianceAssessment).filter(
        ComplianceAssessment.id == assessment_id,
        ComplianceAssessment.user_id == current_user.id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Verify risk item if provided
    if risk_item_id:
        ri = db.query(RiskItem).filter(
            RiskItem.id == risk_item_id,
            RiskItem.assessment_id == assessment_id,
        ).first()
        if not ri:
            raise HTTPException(status_code=404, detail="Risk item not found")

    # Validate file size (max 50 MB)
    MAX_SIZE = 50 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    # Save file
    _ensure_upload_dir()
    file_ext = os.path.splitext(file.filename or "file")[1]
    stored_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(file_path, "wb") as f:
        f.write(content)

    evidence = Evidence(
        assessment_id=assessment_id,
        risk_item_id=risk_item_id,
        file_name=file.filename or stored_name,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        description=description,
        uploaded_by=current_user.id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return EvidenceOut.model_validate(evidence)


@router.get("/by-assessment/{assessment_id}", response_model=List[EvidenceOut])
def list_evidence(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = db.query(ComplianceAssessment).filter(
        ComplianceAssessment.id == assessment_id,
        ComplianceAssessment.user_id == current_user.id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    evidence_list = (
        db.query(Evidence)
        .filter(Evidence.assessment_id == assessment_id)
        .order_by(Evidence.uploaded_at.desc())
        .all()
    )
    return [EvidenceOut.model_validate(e) for e in evidence_list]


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence = (
        db.query(Evidence)
        .join(ComplianceAssessment)
        .filter(
            Evidence.id == evidence_id,
            ComplianceAssessment.user_id == current_user.id,
        )
        .first()
    )
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Remove file
    try:
        if os.path.exists(evidence.file_path):
            os.remove(evidence.file_path)
    except OSError:
        pass  # File already gone

    db.delete(evidence)
    db.commit()
