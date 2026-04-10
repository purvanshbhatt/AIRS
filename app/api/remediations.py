"""Remediation endpoints backed by roadmap tracker items."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.core.demo_guard import require_writable
from app.db.database import get_db
from app.models.assessment import Assessment
from app.models.roadmap_item import RoadmapItem
from app.services.audit import record_audit_event

router = APIRouter()


class RemediationPatchRequest(BaseModel):
    status: str | None = None
    priority: str | None = None
    owner: str | None = None
    notes: str | None = None


def _from_remediation_status(status_value: str | None) -> str:
    value = (status_value or "open").lower()
    if value == "open":
        return "not_started"
    if value == "in_progress":
        return "in_progress"
    if value == "resolved":
        return "completed"
    return value


def _normalize_remediation_status(status_value: str | None) -> str:
    value = (status_value or "not_started").lower()
    if value in {"not_started", "todo", "open"}:
        return "open"
    if value in {"in_progress", "doing"}:
        return "in_progress"
    if value in {"completed", "done", "resolved"}:
        return "resolved"
    return "open"


def _normalize_priority(priority_value: str | None) -> str:
    value = (priority_value or "medium").lower()
    if value in {"critical", "high", "medium", "low"}:
        return value
    return "medium"


@router.patch("/{item_id}")
async def patch_remediation(
    item_id: str,
    payload: RemediationPatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Update remediation/action tracker item by id."""
    item = (
        db.query(RoadmapItem)
        .join(Assessment, Assessment.id == RoadmapItem.assessment_id)
        .filter(
            RoadmapItem.id == item_id,
            RoadmapItem.owner_uid == user.uid,
            Assessment.owner_uid == user.uid,
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remediation item not found")

    if payload.status is not None:
        item.status = _from_remediation_status(payload.status)
    if payload.priority is not None:
        item.priority = payload.priority.lower()
    if payload.owner is not None:
        item.owner = payload.owner
    if payload.notes is not None:
        item.notes = payload.notes

    db.commit()
    db.refresh(item)

    assessment = db.query(Assessment).filter(Assessment.id == item.assessment_id).first()
    if assessment:
        record_audit_event(
            db=db,
            org_id=assessment.organization_id,
            action="remediation.updated",
            actor=user.uid,
        )

    return {
        "id": item.id,
        "assessment_id": item.assessment_id,
        "title": item.title,
        "description": item.description,
        "phase": item.phase,
        "status": _normalize_remediation_status(item.status),
        "priority": _normalize_priority(item.priority),
        "owner": item.owner,
        "due_date": item.due_date,
        "notes": item.notes,
        "effort": item.effort,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
