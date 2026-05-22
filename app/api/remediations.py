"""Remediation endpoints backed by roadmap tracker items."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.core.demo_guard import require_writable
from app.db.database import get_db
from app.models.assessment import Assessment
from app.models.roadmap_item import RoadmapItem
from app.models.finding import Finding
from app.services.audit import record_audit_event
from app.services.antigravity import get_remediation_agent
from app.services.ticket_sync import TicketSyncService

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


class TicketSyncRequest(BaseModel):
    target: str  # "jira" | "servicenow" | "webhook"
    config: dict = {}


@router.post("/findings/{finding_id}/agentic-fix")
async def run_remediation_agent(
    finding_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Executes the Google Antigravity SDK agent to propose technical remediation configuration-level fixes."""
    finding = (
        db.query(Finding)
        .join(Assessment, Assessment.id == Finding.assessment_id)
        .filter(
            Finding.id == finding_id,
            Assessment.owner_uid == user.uid,
        )
        .first()
    )

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )

    agent = get_remediation_agent()
    playbook = agent.execute_remediation_agent(
        finding_title=finding.title,
        finding_description=finding.description or "",
        finding_severity=finding.severity.value,
        finding_recommendation=finding.recommendation or "",
        finding_evidence=finding.evidence or "",
        rule_id=finding.question_id or finding.id,
    )

    return {
        "finding_id": finding.id,
        "title": finding.title,
        "playbook": playbook,
    }


@router.post("/findings/{finding_id}/sync")
async def sync_finding_to_ticketing(
    finding_id: str,
    payload: TicketSyncRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Exports a compliance finding directly as a tracking ticket in Jira, ServiceNow, or raw Webhook."""
    finding = (
        db.query(Finding)
        .join(Assessment, Assessment.id == Finding.assessment_id)
        .filter(
            Finding.id == finding_id,
            Assessment.owner_uid == user.uid,
        )
        .first()
    )

    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found"
        )

    sync_service = TicketSyncService(db_session=db)
    result = await sync_service.sync_finding_to_target(
        finding_id=finding.id,
        title=finding.title,
        description=finding.description or "",
        severity=finding.severity.value,
        recommendation=finding.recommendation or "",
        rule_id=finding.question_id or finding.id,
        target=payload.target,
        config=payload.config,
    )

    if result.get("success"):
        record_audit_event(
            db=db,
            org_id=finding.assessment.organization_id,
            action="remediation.synced",
            actor=user.uid,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Ticketing sync failed")
        )

    return result

