"""
Audit Calendar API routes.

CRUD for audit calendar entries + pre-audit risk forecast.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.auth import require_auth, User
from app.services.organization import OrganizationService
from app.services.audit_calendar import AuditCalendarService
from app.schemas.audit_calendar import (
    AuditCalendarCreate,
    AuditCalendarUpdate,
    AuditCalendarResponse,
    AuditCalendarListResponse,
    AuditForecast,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _verify_org(db: Session, user: User, org_id: str):
    """Verify org exists and belongs to user."""
    service = OrganizationService(db, owner_uid=user.uid if user else None)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}",
        )
    return org


@router.get(
    "/{org_id}/audit-calendar",
    response_model=AuditCalendarListResponse,
    summary="List Audit Calendar",
    description="List all audit calendar entries for an organization.",
)
async def list_entries(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/{org_id}/audit-calendar"""
    _verify_org(db, user, org_id)
    svc = AuditCalendarService(db, org_id)
    entries = svc.list_all()
    enriched = [svc.enrich_response(e) for e in entries]
    upcoming = sum(1 for e in enriched if e.is_upcoming)
    return AuditCalendarListResponse(
        entries=enriched,
        upcoming_count=upcoming,
        total=len(enriched),
    )


@router.post(
    "/{org_id}/audit-calendar",
    response_model=AuditCalendarResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Audit Calendar Entry",
)
async def create_entry(
    org_id: str,
    data: AuditCalendarCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """POST /api/governance/{org_id}/audit-calendar"""
    _verify_org(db, user, org_id)
    svc = AuditCalendarService(db, org_id)
    entry = svc.create(data)
    return svc.enrich_response(entry)


@router.put(
    "/{org_id}/audit-calendar/{entry_id}",
    response_model=AuditCalendarResponse,
    summary="Update Audit Calendar Entry",
)
async def update_entry(
    org_id: str,
    entry_id: str,
    data: AuditCalendarUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """PUT /api/governance/{org_id}/audit-calendar/{entry_id}"""
    _verify_org(db, user, org_id)
    svc = AuditCalendarService(db, org_id)
    entry = svc.update(entry_id, data)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit calendar entry not found: {entry_id}",
        )
    return svc.enrich_response(entry)


@router.delete(
    "/{org_id}/audit-calendar/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Audit Calendar Entry",
)
async def delete_entry(
    org_id: str,
    entry_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """DELETE /api/governance/{org_id}/audit-calendar/{entry_id}"""
    _verify_org(db, user, org_id)
    svc = AuditCalendarService(db, org_id)
    if not svc.delete(entry_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit calendar entry not found: {entry_id}",
        )


@router.get(
    "/{org_id}/audit-calendar/{entry_id}/forecast",
    response_model=AuditForecast,
    summary="Pre-Audit Risk Forecast",
    description=(
        "Cross-reference organization findings with the audit framework "
        "to generate a deterministic pre-audit risk assessment."
    ),
)
async def audit_forecast(
    org_id: str,
    entry_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/{org_id}/audit-calendar/{entry_id}/forecast"""
    _verify_org(db, user, org_id)
    svc = AuditCalendarService(db, org_id)
    entry = svc.get(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit calendar entry not found: {entry_id}",
        )
    return svc.get_forecast(entry)
