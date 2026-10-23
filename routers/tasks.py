"""Authenticated staff tasks over the caller's own records."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import StaffTask, User

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def parse_task_priority(value):
    return value if value in {"LOW", "HIGH"} else "NORMAL"


def parse_task_status(value):
    return value if value in {"OPEN", "DONE", "CANCELLED"} else None


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: Optional[str] = None
    due_at: Optional[datetime] = None


class TaskPatch(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    priority: Optional[str] = None
    status: Optional[str] = None


def as_dict(task: StaffTask):
    return {
        "id": task.id, "title": task.title, "description": task.description,
        "priority": task.priority, "status": task.status,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


@router.get("")
def list_tasks(status: str = "", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    parsed = parse_task_status(status) if status else None
    query = db.query(StaffTask).filter(StaffTask.tenant_id == user.tenant_id, StaffTask.user_id == user.id)
    if parsed:
        query = query.filter(StaffTask.status == parsed)
    rows = query.order_by(StaffTask.status.asc(), StaffTask.due_at.asc(), StaffTask.created_at.desc()).limit(200).all()
    return {"tasks": [as_dict(row) for row in rows]}


@router.post("", status_code=201)
def create_task(payload: TaskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="title is required")
    task = StaffTask(
        tenant_id=user.tenant_id, user_id=user.id, title=title,
        description=payload.description, priority=parse_task_priority(payload.priority),
        due_at=payload.due_at,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"task": as_dict(task)}


@router.patch("/{task_id}")
def update_task(task_id: str, payload: TaskPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(StaffTask).filter(
        StaffTask.id == task_id, StaffTask.tenant_id == user.tenant_id, StaffTask.user_id == user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.status is not None:
        status = parse_task_status(payload.status)
        if not status:
            raise HTTPException(status_code=422, detail="status must be OPEN, DONE, or CANCELLED")
        task.status = status
        task.completed_at = datetime.utcnow() if status == "DONE" else None
    if payload.title and payload.title.strip():
        task.title = payload.title.strip()[:200]
    if payload.priority is not None:
        task.priority = parse_task_priority(payload.priority)
    db.commit()
    db.refresh(task)
    return {"task": as_dict(task)}
