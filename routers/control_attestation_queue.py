from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/control-attestation-queue", tags=["control-attestation-queue"])


class Attestation(BaseModel):
    id: int | None = None
    control: str
    owner: str
    regulation: str
    due_date: str
    evidence: str
    status: str = "pending"


items: List[dict] = [
    {"id": 1, "control": "SOC2-CC6.1", "owner": "Security", "regulation": "SOC 2", "due_date": "2026-05-30", "evidence": "access review export", "status": "pending"},
    {"id": 2, "control": "GDPR-32", "owner": "Privacy", "regulation": "GDPR", "due_date": "2026-06-04", "evidence": "encryption policy", "status": "complete"},
    {"id": 3, "control": "ISO-A.5.23", "owner": "Vendor risk", "regulation": "ISO 27001", "due_date": "2026-05-27", "evidence": "supplier attestation", "status": "blocked"},
]


@router.get("/")
def list_items():
    summary = {"total": len(items), "blocked": sum(1 for i in items if i["status"] == "blocked"), "pending": sum(1 for i in items if i["status"] == "pending")}
    return {"items": items, "summary": summary}


@router.post("/")
def create_item(item: Attestation):
    row = item.dict()
    row["id"] = max([i["id"] for i in items] + [0]) + 1
    items.insert(0, row)
    return row
