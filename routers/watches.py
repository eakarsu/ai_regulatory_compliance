"""Regulation watch/subscription management."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Regulation, RegulationWatch, User
from schemas import RegulationWatchOut

router = APIRouter(prefix="/api/watches", tags=["regulation-watches"])


@router.get("", response_model=List[RegulationWatchOut])
def list_watches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all regulations the user is watching."""
    watches = (
        db.query(RegulationWatch)
        .filter(RegulationWatch.user_id == current_user.id)
        .all()
    )
    result = []
    for w in watches:
        out = RegulationWatchOut.model_validate(w)
        if w.regulation:
            out.regulation_title = w.regulation.title
        result.append(out)
    return result


@router.post("/{regulation_id}", response_model=RegulationWatchOut, status_code=status.HTTP_201_CREATED)
def watch_regulation(
    regulation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Subscribe to change alerts for a regulation."""
    reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")

    existing = db.query(RegulationWatch).filter(
        RegulationWatch.user_id == current_user.id,
        RegulationWatch.regulation_id == regulation_id,
    ).first()
    if existing:
        out = RegulationWatchOut.model_validate(existing)
        out.regulation_title = reg.title
        return out

    watch = RegulationWatch(user_id=current_user.id, regulation_id=regulation_id)
    db.add(watch)
    db.commit()
    db.refresh(watch)

    out = RegulationWatchOut.model_validate(watch)
    out.regulation_title = reg.title
    return out


@router.delete("/{regulation_id}", status_code=status.HTTP_204_NO_CONTENT)
def unwatch_regulation(
    regulation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unsubscribe from a regulation's change alerts."""
    watch = db.query(RegulationWatch).filter(
        RegulationWatch.user_id == current_user.id,
        RegulationWatch.regulation_id == regulation_id,
    ).first()
    if not watch:
        raise HTTPException(status_code=404, detail="Watch not found")
    db.delete(watch)
    db.commit()
