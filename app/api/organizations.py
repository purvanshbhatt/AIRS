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
    OrganizationWithAssessments,
    EnrichmentRequest,
    EnrichmentResponse
)
from app.services.organization import OrganizationService
from app.services.enrichment import EnrichmentService
from datetime import datetime
import json

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


@router.post("/{org_id}/enrich", response_model=EnrichmentResponse)
async def enrich_organization(
    org_id: str,
    request: EnrichmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Enrich organization profile from website URL.
    
    Fetches the URL safely (SSRF protected), extracts metadata,
    and infers a suggested baseline profile.
    """
    # 1. Verify ownership/existence
    org_service = get_org_service(db, user)
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )
    
    # 2. Perform enrichment
    enrichment_service = EnrichmentService()
    result = enrichment_service.enrich_from_url(request.website_url)
    
    # 3. Update organization
    # Create profile JSON
    profile_data = {
        "title": result.title,
        "description": result.description,
        "keywords": result.keywords,
        "confidence": result.confidence,
        "source_url": result.source_url
    }
    
    org_data = OrganizationUpdate(
        website_url=request.website_url,
        baseline_suggestion=result.baseline_suggestion,
        # We manually update plain fields that are not in Schema or special types
    )
    
    # Apply regular updates
    updated_org = org_service.update(org_id, org_data)
    
    # Apply special fields (JSON and datetime)
    # Re-fetch or attach to session if needed, but update() commits.
    # We can just manually update the ORM object and commit again using service generic approach?
    # No, OrganizationUpdate schema doesn't have enriched_at or org_profile as input fields usually.
    # Let's manually update the DB object since we are in the API layer and have the DB session via service or dependency.
    # Actually simpler: Add org_profile to OrganizationUpdate? No, it's internal logic.
    # Let's use the DB session directly or extend service.
    
    # Direct DB update for fields not in OrganizationUpdate public schema
    org.org_profile = json.dumps(profile_data)
    org.enriched_at = datetime.utcnow()
    db.commit()
    db.refresh(org)
    
    return result


@router.get("/{org_id}/trend")
async def get_organization_score_trend(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Get score trend history for an organization.
    Returns list of data points with date and overall score.
    """
    from app.models.assessment import Assessment, AssessmentStatus
    
    # Verify access
    service = get_org_service(db, user)
    if not service.get(org_id):
        raise HTTPException(status_code=404, detail="Organization not found")
        
    # Fetch completed assessments
    assessments = db.query(Assessment).filter(
        Assessment.organization_id == org_id,
        Assessment.status == AssessmentStatus.COMPLETED,
        Assessment.overall_score.isnot(None)
    ).order_by(Assessment.created_at.asc()).all()
    
    trend_data = []
    for a in assessments:
        trend_data.append({
            "date": a.created_at.isoformat(),
            "score": a.overall_score,
            "assessment_id": a.id,
            "name": a.title or "Untitled Assessment"
        })
        
    return trend_data

