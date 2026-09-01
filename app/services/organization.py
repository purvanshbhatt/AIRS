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
from app.core.regulatory import determine_regulatory_profile

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
        """Create a new organization owned by the current user.

        Persistence contract:
          1. Commit to SQLite (local cache for current Cloud Run instance).
          2. Write to Firestore (authoritative, durable persistence).
          3. Only if BOTH succeed does the API return 201.

        If Firestore is unavailable the exception propagates and the caller
        receives an error — the API must never tell a design partner their
        organization is safely provisioned when it isn't.
        """
        org_data = data.model_dump()

        # Compute regulatory profile deterministically
        org_data["regulatory_profile"] = determine_regulatory_profile(
            country=org_data.get("country"),
            industry=org_data.get("industry"),
            size=org_data.get("size")
        )
        if not org_data.get("org_mode"):
            org_data["org_mode"] = "production"
        if not org_data.get("deployment_mode"):
            org_data["deployment_mode"] = "production"

        org = Organization(**org_data, owner_uid=self.owner_uid)
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)

        logger.info(
            "Organization created (SQLite): id=%s, name=%s, owner_uid=%s, mode=%s",
            org.id, org.name, self.owner_uid, org.org_mode,
        )

        # Durable write to Firestore — MUST succeed for the creation to be valid.
        # firestore_save_org() raises FirestoreUnavailableError on failure.
        firestore_save_org(org)

        logger.info(
            "Organization persisted (Firestore): id=%s",
            org.id,
        )

        return org
    
    def _base_query(self):
        """Get base query filtered by owner_uid if set."""
        query = self.db.query(Organization)
        if self.owner_uid:
            query = query.filter(Organization.owner_uid == self.owner_uid)
        return query
    
    def get(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID (scoped to current user).
        
        If not found in the local SQLite cache (e.g. cold start or multi-container
        Cloud Run instance), attempts a fallback lookup to authoritative Firestore.
        """
        if not org_id:
            return None

        org = self._base_query().filter(Organization.id == org_id).first()
        if org:
            return org

        # Fallback to Firestore if local cache misses
        try:
            from app.db.firestore import firestore_get_org, is_firestore_available
            if is_firestore_available():
                doc = firestore_get_org(org_id)
                if doc:
                    doc_owner = doc.get("owner_uid")
                    # Tenant isolation check
                    if self.owner_uid and doc_owner and doc_owner != self.owner_uid:
                        return None

                    # Restore to local SQLite cache
                    from datetime import datetime
                    new_org = Organization(id=org_id)
                    for key, value in doc.items():
                        if key in ("created_at", "updated_at"):
                            if value:
                                try:
                                    value = datetime.fromisoformat(value)
                                except (ValueError, TypeError):
                                    continue
                        if hasattr(new_org, key):
                            setattr(new_org, key, value)
                    if not new_org.name:
                        new_org.name = f"Organization ({org_id[:8]})"

                    self.db.add(new_org)
                    self.db.commit()
                    self.db.refresh(new_org)
                    logger.info("Restored organization %s from Firestore to SQLite", org_id)
                    return new_org
        except Exception as exc:
            logger.warning("Firestore fallback lookup failed for org %s: %s", org_id, exc)

        return None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all organizations (scoped to current user).
        
        If local cache has 0 orgs for an authenticated user, attempts to sync
        from Firestore to ensure newly provisioned orgs are available.
        """
        orgs = self._base_query().offset(skip).limit(limit).all()
        if not orgs and self.owner_uid:
            try:
                from app.db.firestore import firestore_get_all_orgs, is_firestore_available
                if is_firestore_available():
                    docs = firestore_get_all_orgs(owner_uid=self.owner_uid)
                    if docs:
                        from app.db.firestore import sync_orgs_from_firestore
                        sync_orgs_from_firestore(self.db)
                        orgs = self._base_query().offset(skip).limit(limit).all()
            except Exception as exc:
                logger.warning("Firestore get_all sync failed: %s", exc)

        return orgs
    
    def update(self, org_id: str, data: OrganizationUpdate) -> Optional[Organization]:
        """Update an organization (scoped to current user)."""
        org = self.get(org_id)
        if not org:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(org, key, value)
            
        # Re-compute regulatory profile if relevant fields changed
        if "country" in update_data or "industry" in update_data or "size" in update_data:
            org.regulatory_profile = determine_regulatory_profile(
                country=org.country,
                industry=org.industry,
                size=org.size
            )
        
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
