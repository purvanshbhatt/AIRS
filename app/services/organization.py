"""
Organization service - business logic for organizations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.organization import Organization
from app.models.assessment import Assessment
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    """Service for organization operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: OrganizationCreate) -> Organization:
        """Create a new organization."""
        org = Organization(**data.model_dump())
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        return org
    
    def get(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID."""
        return self.db.query(Organization).filter(Organization.id == org_id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all organizations."""
        return self.db.query(Organization).offset(skip).limit(limit).all()
    
    def update(self, org_id: str, data: OrganizationUpdate) -> Optional[Organization]:
        """Update an organization."""
        org = self.get(org_id)
        if not org:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(org, key, value)
        
        self.db.commit()
        self.db.refresh(org)
        return org
    
    def delete(self, org_id: str) -> bool:
        """Delete an organization."""
        org = self.get(org_id)
        if not org:
            return False
        
        self.db.delete(org)
        self.db.commit()
        return True
    
    def get_with_assessment_count(self, org_id: str) -> Optional[dict]:
        """Get organization with assessment count."""
        org = self.get(org_id)
        if not org:
            return None
        
        count = self.db.query(func.count(Assessment.id)).filter(
            Assessment.organization_id == org_id
        ).scalar()
        
        return {
            **org.__dict__,
            "assessment_count": count
        }
