"""Compliance deadline calendar endpoint."""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ComplianceAssessment, Regulation, User
from schemas import CalendarEvent, CalendarOut

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("", response_model=CalendarOut)
def get_calendar(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all compliance deadlines and events for a given month."""
    from calendar import monthrange
    first_day = datetime(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num, 23, 59, 59)

    events: List[CalendarEvent] = []

    # Assessment review dates
    assessments = (
        db.query(ComplianceAssessment)
        .filter(
            ComplianceAssessment.user_id == current_user.id,
            ComplianceAssessment.next_review_date != None,
            ComplianceAssessment.next_review_date >= first_day,
            ComplianceAssessment.next_review_date <= last_day,
        )
        .all()
    )

    now = datetime.utcnow()
    for a in assessments:
        reg = db.query(Regulation).filter(Regulation.id == a.regulation_id).first()
        reg_title = reg.title if reg else "Unknown Regulation"
        is_overdue = a.next_review_date < now

        events.append(CalendarEvent(
            date=a.next_review_date.strftime("%Y-%m-%d"),
            type="overdue" if is_overdue else "review_due",
            title=f"{'[OVERDUE] ' if is_overdue else ''}Review Due: {reg_title}",
            severity="critical" if is_overdue else ("warning" if a.status == "non_compliant" else "info"),
            link=f"/assessments/{a.id}",
            assessment_id=a.id,
            regulation_id=a.regulation_id,
        ))

    # Regulation effective dates
    regs_effective = (
        db.query(Regulation)
        .filter(
            Regulation.is_active == True,
            Regulation.effective_date != None,
        )
        .all()
    )

    for reg in regs_effective:
        if reg.effective_date:
            eff_dt = datetime(reg.effective_date.year, reg.effective_date.month, reg.effective_date.day)
            if first_day <= eff_dt <= last_day:
                events.append(CalendarEvent(
                    date=reg.effective_date.isoformat(),
                    type="effective_date",
                    title=f"Regulation Effective: {reg.title}",
                    severity="info",
                    link=f"/regulations/{reg.id}",
                    regulation_id=reg.id,
                ))

    # Sort events by date
    events.sort(key=lambda e: e.date)

    return CalendarOut(year=year, month=month, events=events)
