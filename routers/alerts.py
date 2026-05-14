from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import (
    ComplianceAlert, ComplianceAssessment, AlertSeverity, User
)
from schemas import AlertListOut, AlertOut, PaginationMeta

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertListOut)
def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    severity: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ComplianceAlert).filter(ComplianceAlert.user_id == current_user.id)
    if unread_only:
        q = q.filter(ComplianceAlert.is_read == False)
    if severity:
        q = q.filter(ComplianceAlert.severity == severity)

    total = q.count()
    unread_count = db.query(ComplianceAlert).filter(
        ComplianceAlert.user_id == current_user.id,
        ComplianceAlert.is_read == False,
    ).count()

    alerts = (
        q.order_by(ComplianceAlert.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return AlertListOut(
        data=[AlertOut.model_validate(a) for a in alerts],
        unread_count=unread_count,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit if total > 0 else 1,
        ),
    )


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(ComplianceAlert).filter(
        ComplianceAlert.id == alert_id,
        ComplianceAlert.user_id == current_user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(ComplianceAlert).filter(
        ComplianceAlert.user_id == current_user.id,
        ComplianceAlert.is_read == False,
    ).update({"is_read": True})
    db.commit()


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check compliance conditions and create relevant alerts (with deduplication)."""
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")
    overdue_cutoff = now
    upcoming_cutoff = now + timedelta(days=30)

    assessments = (
        db.query(ComplianceAssessment)
        .filter(ComplianceAssessment.user_id == current_user.id)
        .all()
    )

    created = 0
    for assessment in assessments:
        if assessment.next_review_date:
            if assessment.next_review_date < overdue_cutoff:
                dedup_key = f"overdue_review:{assessment.id}:{today_str}"
                existing = db.query(ComplianceAlert).filter(
                    ComplianceAlert.dedup_key == dedup_key
                ).first()
                if not existing:
                    alert = ComplianceAlert(
                        user_id=current_user.id,
                        regulation_id=assessment.regulation_id,
                        alert_type="overdue_review",
                        severity=AlertSeverity.critical,
                        message=(
                            f"Assessment review is overdue. "
                            f"It was due on {assessment.next_review_date.strftime('%Y-%m-%d')}."
                        ),
                        dedup_key=dedup_key,
                    )
                    db.add(alert)
                    created += 1
            elif now < assessment.next_review_date <= upcoming_cutoff:
                days_left = (assessment.next_review_date - now).days
                dedup_key = f"upcoming_review:{assessment.id}:{today_str}"
                existing = db.query(ComplianceAlert).filter(
                    ComplianceAlert.dedup_key == dedup_key
                ).first()
                if not existing:
                    alert = ComplianceAlert(
                        user_id=current_user.id,
                        regulation_id=assessment.regulation_id,
                        alert_type="upcoming_review",
                        severity=AlertSeverity.warning,
                        message=(
                            f"Assessment review is due in {days_left} day(s) "
                            f"on {assessment.next_review_date.strftime('%Y-%m-%d')}."
                        ),
                        dedup_key=dedup_key,
                    )
                    db.add(alert)
                    created += 1

        if assessment.status == "non_compliant":
            dedup_key = f"non_compliant:{assessment.id}:{today_str}"
            existing = db.query(ComplianceAlert).filter(
                ComplianceAlert.dedup_key == dedup_key
            ).first()
            if not existing:
                alert = ComplianceAlert(
                    user_id=current_user.id,
                    regulation_id=assessment.regulation_id,
                    alert_type="non_compliant_status",
                    severity=AlertSeverity.critical,
                    message=f"Assessment is marked non-compliant with a score of {assessment.overall_score}/100.",
                    dedup_key=dedup_key,
                )
                db.add(alert)
                created += 1

    db.commit()
    return {"alerts_created": created, "message": f"Generated {created} new alert(s)"}


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(ComplianceAlert).filter(
        ComplianceAlert.id == alert_id,
        ComplianceAlert.user_id == current_user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
