"""
Organization API routes.

All endpoints enforce tenant isolation using Firebase user UID.
Users can only access their own organizations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from app.services.organization import OrganizationService

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
