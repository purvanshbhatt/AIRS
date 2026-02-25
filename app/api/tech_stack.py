"""
Tech Stack Lifecycle Registry API routes.

CRUD for tech stack items + summary/risk classification.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.auth import require_auth, User
from app.services.organization import OrganizationService
from app.services.governance.tech_stack import TechStackService
from app.schemas.tech_stack import (
    TechStackItemCreate,
    TechStackItemUpdate,
    TechStackItemResponse,
    TechStackListResponse,
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
    "/{org_id}/tech-stack",
    response_model=TechStackListResponse,
    summary="List Tech Stack",
    description="List all tech stack items with risk classification and summary.",
)
async def list_items(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/{org_id}/tech-stack"""
    _verify_org(db, user, org_id)
    svc = TechStackService(db, org_id)
    items = svc.list_all()
    enriched = [svc.enrich_response(i) for i in items]
    summary = svc.get_summary(items)
    return TechStackListResponse(
        items=enriched,
        summary=summary,
        total=len(enriched),
    )


@router.post(
    "/{org_id}/tech-stack",
    response_model=TechStackItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Tech Stack Item",
)
async def create_item(
    org_id: str,
    data: TechStackItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """POST /api/governance/{org_id}/tech-stack"""
    _verify_org(db, user, org_id)
    svc = TechStackService(db, org_id)
    item = svc.create(data)
    return svc.enrich_response(item)


@router.put(
    "/{org_id}/tech-stack/{item_id}",
    response_model=TechStackItemResponse,
    summary="Update Tech Stack Item",
)
async def update_item(
    org_id: str,
    item_id: str,
    data: TechStackItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """PUT /api/governance/{org_id}/tech-stack/{item_id}"""
    _verify_org(db, user, org_id)
    svc = TechStackService(db, org_id)
    item = svc.update(item_id, data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tech stack item not found: {item_id}",
        )
    return svc.enrich_response(item)


@router.delete(
    "/{org_id}/tech-stack/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Tech Stack Item",
)
async def delete_item(
    org_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """DELETE /api/governance/{org_id}/tech-stack/{item_id}"""
    _verify_org(db, user, org_id)
    svc = TechStackService(db, org_id)
    if not svc.delete(item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tech stack item not found: {item_id}",
        )
