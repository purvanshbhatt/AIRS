"""
Onboarding Status API — Stable frontend contract for organization onboarding.

Provides GET /api/orgs/{org_id}/onboarding so the frontend does not
need to infer business state from random fields.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import require_auth, User
from app.models.organization import Organization
from app.models.connector import Connector
from app.models.report import Report
from app.schemas.onboarding import (
    OnboardingResponse,
    OnboardingStatus,
    OnboardingStep,
    EvidenceStatus,
)

logger = logging.getLogger("airs.api.onboarding")

router = APIRouter()


@router.get(
    "",
    response_model=OnboardingResponse,
    summary="Get Onboarding Status",
    description=(
        "Returns the current onboarding progress for an organization, "
        "including connector status, evidence status, and report availability."
    ),
    responses={
        200: {"description": "Onboarding status"},
        401: {"description": "Authentication required"},
        404: {"description": "Organization not found"},
    },
)
async def get_onboarding_status(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Get the onboarding status for an organization."""
    # Tenant isolation
    org = db.query(Organization).filter(
        Organization.id == org_id,
        Organization.owner_uid == user.uid,
    ).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )

    # Count connected sources
    connectors = db.query(Connector).filter(
        Connector.organization_id == org_id,
    ).all()

    active_connectors = [c for c in connectors if getattr(c, "status", "") == "active"]
    connected_count = len(active_connectors)

    # Check latest sync
    last_sync = None
    for c in active_connectors:
        if c.last_sync_at and (last_sync is None or c.last_sync_at > last_sync):
            last_sync = c.last_sync_at

    verified = connected_count > 0 and last_sync is not None

    # Check report availability
    report_count = db.query(Report).filter(
        Report.organization_id == org_id,
        Report.owner_uid == user.uid,
    ).count()

    # Determine org mode
    org_mode = getattr(org, "org_mode", "pilot") or "pilot"

    # Build onboarding steps
    steps = [
        OnboardingStep(
            step_id="create_organization",
            label="Create Organization",
            completed=True,  # If we got here, org exists
            required=True,
        ),
        OnboardingStep(
            step_id="connect_evidence",
            label="Connect Evidence Source",
            completed=connected_count > 0,
            required=True,
        ),
        OnboardingStep(
            step_id="verify_telemetry",
            label="Verify Telemetry",
            completed=verified,
            required=True,
        ),
        OnboardingStep(
            step_id="generate_report",
            label="Generate First Report",
            completed=report_count > 0,
            required=False,
        ),
    ]

    completed_required = all(s.completed for s in steps if s.required)
    completed_total = sum(1 for s in steps if s.completed)
    progress_pct = int((completed_total / len(steps)) * 100) if steps else 0

    # Determine current step
    current_step = "create_organization"
    for s in steps:
        if not s.completed:
            current_step = s.step_id
            break
    else:
        current_step = "complete"

    return OnboardingResponse(
        organization_id=org.id,
        organization_name=org.name,
        mode=org_mode,
        onboarding=OnboardingStatus(
            completed=completed_required,
            current_step=current_step,
            steps=steps,
            progress_pct=progress_pct,
        ),
        evidence=EvidenceStatus(
            connected_sources=connected_count,
            verified=verified,
            last_sync_at=last_sync,
        ),
        report_available=report_count > 0,
        created_at=org.created_at if hasattr(org, "created_at") else None,
    )
