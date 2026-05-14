"""Risk item management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ComplianceAssessment, RiskItem, User
from schemas import RiskItemOut, RiskItemUpdate

router = APIRouter(prefix="/api/risk-items", tags=["risk-items"])


def _get_risk_item_for_user(risk_item_id: str, user: User, db: Session) -> RiskItem:
    ri = (
        db.query(RiskItem)
        .join(ComplianceAssessment)
        .filter(
            RiskItem.id == risk_item_id,
            ComplianceAssessment.user_id == user.id,
        )
        .first()
    )
    if not ri:
        raise HTTPException(status_code=404, detail="Risk item not found")
    return ri


@router.get("/{risk_item_id}", response_model=RiskItemOut)
def get_risk_item(
    risk_item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ri = _get_risk_item_for_user(risk_item_id, current_user, db)
    return RiskItemOut.model_validate(ri)


@router.patch("/{risk_item_id}", response_model=RiskItemOut)
def update_risk_item(
    risk_item_id: str,
    payload: RiskItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update risk item status, mitigation plan, or due date."""
    ri = _get_risk_item_for_user(risk_item_id, current_user, db)

    if payload.status is not None:
        ri.status = payload.status
    if payload.mitigation_plan is not None:
        ri.mitigation_plan = payload.mitigation_plan
    if payload.due_date is not None:
        ri.due_date = payload.due_date

    db.commit()
    db.refresh(ri)
    return RiskItemOut.model_validate(ri)


@router.get("/by-assessment/{assessment_id}", response_model=list[RiskItemOut])
def list_risk_items_for_assessment(
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

    risk_items = (
        db.query(RiskItem)
        .filter(RiskItem.assessment_id == assessment_id)
        .order_by(RiskItem.risk_level.desc())
        .all()
    )
    return [RiskItemOut.model_validate(ri) for ri in risk_items]
