"""
Pilot Program API — 30-Day Readiness Sprint endpoints.

Manages the pilot lifecycle:
  POST   /governance/orgs/{org_id}/pilot          — Activate pilot
  GET    /governance/orgs/{org_id}/pilot          — Get pilot status
  DELETE /governance/orgs/{org_id}/pilot          — Cancel pilot
  POST   /governance/orgs/{org_id}/pilot/milestone/{milestone_id}  — Complete milestone
  DELETE /governance/orgs/{org_id}/pilot/milestone/{milestone_id}  — Reset milestone
  GET    /governance/orgs/{org_id}/pilot/confidence  — Confidence breakdown
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.core.demo_guard import require_writable
from app.db.database import get_db
from app.services.organization import OrganizationService
from app.services.pilot_program import (
    activate_pilot,
    get_pilot,
    complete_milestone,
    reset_milestone,
    deactivate_pilot,
    get_confidence_breakdown,
)

router = APIRouter()


@router.post("/orgs/{org_id}/pilot", status_code=status.HTTP_201_CREATED)
async def start_pilot(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Activate a 30-day readiness sprint for an organization."""
    svc = OrganizationService(db, owner_uid=user.uid)
    org = svc.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing = get_pilot(org_id)
    if existing and existing["status"] == "active":
        raise HTTPException(status_code=409, detail="Pilot already active for this organization")

    pilot = activate_pilot(org_id, org_name=org.name)
    return pilot


@router.get("/orgs/{org_id}/pilot")
async def get_pilot_status(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Get the current pilot program status."""
    svc = OrganizationService(db, owner_uid=user.uid)
    org = svc.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    pilot = get_pilot(org_id)
    if not pilot:
        return {"org_id": org_id, "status": "not_started", "milestones": [], "confidence_score": 0}

    return pilot


@router.delete("/orgs/{org_id}/pilot", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_pilot(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Cancel an active pilot program."""
    if not deactivate_pilot(org_id):
        raise HTTPException(status_code=404, detail="No active pilot found")


@router.post("/orgs/{org_id}/pilot/milestone/{milestone_id}")
async def mark_milestone_complete(
    org_id: str,
    milestone_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Mark a pilot milestone as completed."""
    pilot = complete_milestone(org_id, milestone_id)
    if not pilot:
        raise HTTPException(status_code=404, detail="Pilot not found or milestone not found")
    return pilot


@router.delete("/orgs/{org_id}/pilot/milestone/{milestone_id}")
async def reset_milestone_status(
    org_id: str,
    milestone_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Reset a pilot milestone to not_started."""
    pilot = reset_milestone(org_id, milestone_id)
    if not pilot:
        raise HTTPException(status_code=404, detail="Pilot not found or milestone not found")
    return pilot


@router.get("/orgs/{org_id}/pilot/confidence")
async def pilot_confidence_breakdown(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Get detailed confidence score breakdown by category."""
    breakdown = get_confidence_breakdown(org_id)
    if not breakdown:
        return {"org_id": org_id, "confidence_score": 0, "confidence_grade": "F", "categories": {}, "completed": 0, "total": 0}
    return breakdown
