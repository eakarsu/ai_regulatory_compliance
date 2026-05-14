from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models import Regulation, User
from schemas import (
    PaginationMeta, RegulationCreate, RegulationDetailOut,
    RegulationListOut, RegulationOut,
)

router = APIRouter(prefix="/api/regulations", tags=["regulations"])


@router.get("", response_model=RegulationListOut)
def list_regulations(
    jurisdiction: str = Query(None),
    category: str = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Regulation).filter(Regulation.is_active == True)
    if jurisdiction:
        q = q.filter(Regulation.jurisdiction.ilike(f"%{jurisdiction}%"))
    if category:
        # Accept both enum value (GDPR) and lowercase (gdpr)
        q = q.filter(Regulation.category == category.upper())
    if search:
        q = q.filter(
            Regulation.title.ilike(f"%{search}%") |
            Regulation.summary.ilike(f"%{search}%")
        )

    total = q.count()
    regs = q.order_by(Regulation.last_updated.desc()).offset((page - 1) * limit).limit(limit).all()

    return RegulationListOut(
        data=[RegulationOut.model_validate(r) for r in regs],
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit if total > 0 else 1,
        ),
    )


@router.post("", response_model=RegulationOut, status_code=status.HTTP_201_CREATED)
def create_regulation(
    payload: RegulationCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reg = Regulation(**payload.model_dump())
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return RegulationOut.model_validate(reg)


@router.get("/search", response_model=RegulationListOut)
def search_regulations(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Regulation)
        .filter(
            Regulation.is_active == True,
            (
                Regulation.title.ilike(f"%{q}%") |
                Regulation.summary.ilike(f"%{q}%") |
                Regulation.full_text.ilike(f"%{q}%") |
                Regulation.jurisdiction.ilike(f"%{q}%")
            ),
        )
    )
    total = query.count()
    regs = query.offset((page - 1) * limit).limit(limit).all()

    return RegulationListOut(
        data=[RegulationOut.model_validate(r) for r in regs],
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit if total > 0 else 1,
        ),
    )


@router.get("/{regulation_id}", response_model=RegulationDetailOut)
def get_regulation(
    regulation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")
    return RegulationDetailOut.model_validate(reg)


@router.put("/{regulation_id}", response_model=RegulationOut)
def update_regulation(
    regulation_id: str,
    payload: RegulationCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(reg, field, value)

    from datetime import datetime
    reg.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(reg)
    return RegulationOut.model_validate(reg)


@router.delete("/{regulation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_regulation(
    regulation_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")
    # Soft delete
    reg.is_active = False
    db.commit()
