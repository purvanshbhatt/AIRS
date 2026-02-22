"""
Organization API routes.

All endpoints enforce tenant isolation using Firebase user UID.
Users can only access their own organizations.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.core.logging import event_logger
from app.core.auth import require_auth, User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationWithAssessments
)
from app.schemas.audit import AuditEventResponse
from app.models.audit_event import AuditEvent
from app.services.organization import OrganizationService
from app.services.demo_seed import ensure_demo_seed_data

router = APIRouter()
logger = logging.getLogger(__name__)


def get_org_service(db: Session, user: User) -> OrganizationService:
    """Get organization service with tenant isolation."""
    return OrganizationService(db, owner_uid=user.uid if user else None)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new organization owned by the authenticated user.",
    responses={
        201: {"description": "Organization created successfully"},
        401: {"description": "Authentication required"}
    }
)
async def create_organization(
    request: Request,
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Create a new organization owned by the current user."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(
        f"[{request_id}] POST /api/orgs - Creating organization: name={data.name}, "
        f"user={user.uid}"
    )
    
    try:
        service = get_org_service(db, user)
        org = service.create(data)
        event_logger.organization_created(organization_id=org.id, name=org.name)
        logger.info(f"[{request_id}] POST /api/orgs -> 201 Created: org_id={org.id}")
        return org
    except Exception as e:
        logger.error(
            f"[{request_id}] POST /api/orgs -> 500 Error: {type(e).__name__}: {str(e)}"
        )
        raise


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List organizations owned by the current user."""
    ensure_demo_seed_data(db, user.uid if user else None)
    service = get_org_service(db, user)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{org_id}", response_model=OrganizationWithAssessments)
async def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get organization by ID (must be owned by current user)."""
    service = get_org_service(db, user)
    result = service.get_with_assessment_count(org_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )
    return result


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Update an organization (must be owned by current user)."""
    service = get_org_service(db, user)
    org = service.update(org_id, data)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Delete an organization (must be owned by current user)."""
    service = get_org_service(db, user)
    if not service.delete(org_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )


@router.get("/{org_id}/audit", response_model=List[AuditEventResponse])
async def list_organization_audit_events(
    org_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """List recent audit events for an organization owned by the current user."""
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}",
        )

    safe_limit = max(1, min(limit, 500))
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.org_id == org_id)
        .order_by(AuditEvent.timestamp.desc())
        .limit(safe_limit)
        .all()
    )
    return events


# ---------------------------------------------------------------------------
# Phase 5: Analytics toggle
# ---------------------------------------------------------------------------

from pydantic import BaseModel


class AnalyticsToggleRequest(BaseModel):
    analytics_enabled: bool


@router.patch(
    "/{org_id}/analytics",
    response_model=OrganizationResponse,
    summary="Toggle Analytics",
    description=(
        "Enable or disable anonymised telemetry for an organization. "
        "When disabled, the backend suppresses telemetry events and "
        "behavioral analytics logging for all assessments belonging to "
        "this organization."
    ),
)
async def toggle_analytics(
    org_id: str,
    body: AnalyticsToggleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """PATCH /api/orgs/{org_id}/analytics — update analytics_enabled flag."""
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Organization not found: {org_id}")

    org.analytics_enabled = body.analytics_enabled
    db.commit()
    db.refresh(org)
    return org


# ---------------------------------------------------------------------------
# Phase 7: Audit export
# ---------------------------------------------------------------------------

@router.get(
    "/{org_id}/audit/export",
    summary="Export Audit Trail",
    description="Download all audit events for an organization as a JSON file.",
)
async def export_audit_trail(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/orgs/{org_id}/audit/export — downloadable JSON audit log."""
    service = get_org_service(db, user)
    org = service.get(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Organization not found: {org_id}")

    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.org_id == org_id)
        .order_by(AuditEvent.timestamp.asc())
        .all()
    )

    payload = {
        "organization_id": org_id,
        "organization_name": org.name,
        "exported_events": len(events),
        "events": [
            {
                "id": e.id,
                "action": e.action,
                "actor": e.actor,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ],
    }
    json_bytes = json.dumps(payload, indent=2).encode("utf-8")
    filename = f"audit_{org_id[:8]}.json"
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
