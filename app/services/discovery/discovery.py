"""
CRUD service for Technology Discovery.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.discovery import (
    TechnologyInventory,
    HostAsset,
    InstalledProduct,
    EvidenceSource
)

class TechnologyDiscoveryService:
    """Service layer for managing Technology Discovery models."""

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    def get_latest_inventory(self) -> Optional[TechnologyInventory]:
        """Gets the most recently discovered inventory for the organization."""
        return (
            self.db.query(TechnologyInventory)
            .filter(TechnologyInventory.org_id == self.org_id)
            .order_by(TechnologyInventory.last_discovered_at.desc())
            .first()
        )

    def create_inventory(self, source: str, confidence_score: float = 1.0) -> TechnologyInventory:
        """Creates a new inventory snapshot."""
        inv = TechnologyInventory(
            org_id=self.org_id,
            discovery_source=source,
            confidence_score=confidence_score
        )
        self.db.add(inv)
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def add_asset(
        self,
        inventory_id: str,
        asset_type: str,
        hostname: Optional[str] = None,
        operating_system: Optional[str] = None,
        ip_address: Optional[str] = None,
        cloud_provider: Optional[str] = None
    ) -> HostAsset:
        asset = HostAsset(
            org_id=self.org_id,
            inventory_id=inventory_id,
            asset_type=asset_type,
            hostname=hostname,
            operating_system=operating_system,
            ip_address=ip_address,
            cloud_provider=cloud_provider
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def add_installed_product(
        self,
        asset_id: str,
        product_name: str,
        vendor: Optional[str] = None,
        version: Optional[str] = None,
        installation_source: Optional[str] = None,
        eol_status: Optional[str] = None
    ) -> InstalledProduct:
        product = InstalledProduct(
            asset_id=asset_id,
            product_name=product_name,
            vendor=vendor,
            version=version,
            installation_source=installation_source,
            eol_status=eol_status
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def add_evidence_source(
        self,
        product_id: str,
        source_type: str,
        connector_name: Optional[str] = None,
        raw_evidence_hash: Optional[str] = None
    ) -> EvidenceSource:
        evidence = EvidenceSource(
            product_id=product_id,
            source_type=source_type,
            connector_name=connector_name,
            raw_evidence_hash=raw_evidence_hash
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence
