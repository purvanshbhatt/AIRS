"""
Organization API routes.

All endpoints in this router require authentication when AUTH_REQUIRED=true.
"""

from fastapi import APIRouter, Depends, HTTPException, status
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


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new organization to associate with assessments.",
    responses={
        201: {"description": "Organization created successfully"},
        401: {"description": "Authentication required (when AUTH_REQUIRED=true)"}
    }
)
async def create_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Create a new organization."""
    service = OrganizationService(db)
    org = service.create(data)
    event_logger.organization_created(organization_id=org.id, name=org.name)
    return org


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List all organizations."""
    service = OrganizationService(db)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{org_id}", response_model=OrganizationWithAssessments)
async def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get organization by ID with assessment count."""
    service = OrganizationService(db)
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
    """Update an organization."""
    service = OrganizationService(db)
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
    """Delete an organization."""
    service = OrganizationService(db)
    if not service.delete(org_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )
