"""
Organization service - business logic for organizations.

All operations are scoped by owner_uid for tenant isolation.
Dual-writes to Cloud Firestore for persistence across Cloud Run cold starts.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.organization import Organization
from app.models.assessment import Assessment
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.db.firestore import firestore_save_org, firestore_delete_org

import logging

logger = logging.getLogger("airs.org_service")


class OrganizationService:
    """Service for organization operations with tenant isolation."""
    
    def __init__(self, db: Session, owner_uid: Optional[str] = None):
        """
        Initialize service.
        
        Args:
            db: Database session
            owner_uid: Firebase user UID for tenant isolation. If None, operations
                      will not filter by owner (for backwards compatibility during
                      migration period).
        """
        self.db = db
        self.owner_uid = owner_uid
    
    def create(self, data: OrganizationCreate) -> Organization:
        """Create a new organization owned by the current user."""
        org = Organization(**data.model_dump(), owner_uid=self.owner_uid)
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        # Dual-write to Firestore for persistence
        firestore_save_org(org)
        return org
    
    def _base_query(self):
        """Get base query filtered by owner_uid if set."""
        query = self.db.query(Organization)
        if self.owner_uid:
            query = query.filter(Organization.owner_uid == self.owner_uid)
        return query
    
    def get(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID (scoped to current user)."""
        return self._base_query().filter(Organization.id == org_id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all organizations (scoped to current user)."""
        return self._base_query().offset(skip).limit(limit).all()
    
    def update(self, org_id: str, data: OrganizationUpdate) -> Optional[Organization]:
        """Update an organization (scoped to current user)."""
        org = self.get(org_id)
        if not org:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(org, key, value)
        
        self.db.commit()
        self.db.refresh(org)
        # Dual-write to Firestore for persistence
        firestore_save_org(org)
        return org
    
    def delete(self, org_id: str) -> bool:
        """Delete an organization (scoped to current user)."""
        org = self.get(org_id)
        if not org:
            return False
        
        self.db.delete(org)
        self.db.commit()
        # Remove from Firestore too
        firestore_delete_org(org_id)
        return True
    
    def get_with_assessment_count(self, org_id: str) -> Optional[dict]:
        """Get organization with assessment count (scoped to current user)."""
        org = self.get(org_id)
        if not org:
            return None
        
        # Also filter assessments by owner_uid for accurate count
        count_query = self.db.query(func.count(Assessment.id)).filter(
            Assessment.organization_id == org_id
        )
        if self.owner_uid:
            count_query = count_query.filter(Assessment.owner_uid == self.owner_uid)
        count = count_query.scalar()
        
        return {
            **org.__dict__,
            "assessment_count": count
        }
