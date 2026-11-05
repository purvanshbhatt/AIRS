"""
AWS Discovery Service.
"""
import hashlib
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.discovery import AssetType
from app.services.discovery.discovery import TechnologyDiscoveryService

class AWSDiscoveryService:
    """Service to discover technology assets via AWS APIs."""

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id
        self.discovery_service = TechnologyDiscoveryService(db, org_id)

    def _execute_mock_aws_discovery(self, inventory_id: str) -> int:
        """Mock discovery representing AWS EC2 and RDS instances."""
        
        # Simulating AWS resources
        resources = [
            {
                "id": "i-0abcd1234efgh5678",
                "type": AssetType.CLOUD_SERVICE.value,
                "name": "EKS-Worker-Node-1",
                "os": "Amazon Linux 2023",
                "ip": "10.0.10.5",
                "software": [
                    {"name": "docker", "vendor": "Docker Inc.", "version": "27.4.1"},
                    {"name": "kubernetes", "vendor": "Cloud Native Computing Foundation", "version": "1.30"},
                    {"name": "aws-cli", "vendor": "Amazon", "version": "2.15.0"}
                ]
            },
            {
                "id": "db-abc123def456ghi",
                "type": AssetType.CLOUD_SERVICE.value,
                "name": "production-postgres-rds",
                "os": None,
                "ip": "10.0.20.10",
                "software": [
                    {"name": "postgresql", "vendor": "PostgreSQL Global Development Group", "version": "16.4"}
                ]
            }
        ]
        
        assets_created = 0

        for res in resources:
            res_id = res["id"]
            
            asset = self.discovery_service.add_asset(
                inventory_id=inventory_id,
                asset_type=res["type"],
                hostname=res["name"],
                operating_system=res.get("os"),
                ip_address=res.get("ip"),
                cloud_provider="AWS"
            )
            assets_created += 1
            
            for sw in res["software"]:
                product = self.discovery_service.add_installed_product(
                    asset_id=asset.id,
                    product_name=sw["name"],
                    vendor=sw.get("vendor"),
                    version=sw.get("version"),
                    installation_source="aws_systems_manager"
                )
                
                raw_evidence = f"{res_id}:{sw['name']}:{sw.get('version')}"
                evidence_hash = hashlib.sha256(raw_evidence.encode()).hexdigest()
                
                self.discovery_service.add_evidence_source(
                    product_id=product.id,
                    source_type="aws",
                    connector_name="AWS Config",
                    raw_evidence_hash=evidence_hash
                )
                
        return assets_created

    def discover_from_aws(self, inventory_id: str) -> int:
        """Runs discovery jobs against AWS to populate inventory."""
        # For now, this is exclusively mock implementation.
        return self._execute_mock_aws_discovery(inventory_id)
