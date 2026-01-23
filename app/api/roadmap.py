
"""
Roadmap API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.auth import get_current_user, User, require_auth
from app.models.roadmap_item import RoadmapItem
from app.models.organization import Organization
from app.schemas.roadmap import (
    RoadmapItemCreate,
    RoadmapItemUpdate,
    RoadmapItemResponse,
    RoadmapListResponse
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def verify_org_access(org_id: str, db: Session, user: User):
    """Verify organization exists and user has access."""
    # Simple check for now - assume all authenticated users can access for demo
    # In real app, check user.uid against org.owner_uid or team table
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}"
        )
    return org

@router.get("/orgs/{org_id}/roadmap", response_model=RoadmapListResponse)
def list_roadmap_items(
    org_id: str,
    status: str = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List roadmap items for an organization."""
    verify_org_access(org_id, db, user)
    
    query = db.query(RoadmapItem).filter(RoadmapItem.organization_id == org_id)
    
    if status:
        query = query.filter(RoadmapItem.status == status)
        
    # Sort by due date (nulls last) then priority (hacky sort) then created_at desc
    # Actually just created_at desc for now for simplicity, or priority
    # Custom sort: High > Medium > Low
    items = query.order_by(RoadmapItem.created_at.desc()).all()
    
    return {"items": items, "total": len(items)}

@router.post("/orgs/{org_id}/roadmap", response_model=RoadmapItemResponse)
def create_roadmap_item(
    org_id: str,
    item: RoadmapItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Create a new roadmap item."""
    verify_org_access(org_id, db, user)
    
    db_item = RoadmapItem(
        organization_id=org_id,
        owner_uid=user.uid,
        **item.model_dump()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.patch("/roadmap/{item_id}", response_model=RoadmapItemResponse)
def update_roadmap_item(
    item_id: str,
    update: RoadmapItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Update a roadmap item."""
    item = db.query(RoadmapItem).filter(RoadmapItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # Access check (owner or generic auth)
    
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
        
    db.commit()
    db.refresh(item)
    return item

@router.delete("/roadmap/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_roadmap_item(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Delete a roadmap item."""
    item = db.query(RoadmapItem).filter(RoadmapItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    db.delete(item)
    db.commit()
