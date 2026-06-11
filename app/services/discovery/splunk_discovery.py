"""
Splunk Discovery Service.
"""
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.discovery import AssetType
from app.services.discovery.discovery import TechnologyDiscoveryService
from app.services.integrations import IntegrationService

# Note: In a real environment, we would use the actual Splunk SDK or REST API
# to execute these searches against the connected Splunk instance.
# Here we will simulate the connection using the pattern the user expects.

class SplunkDiscoveryService:
    """Service to discover technology assets via Splunk."""

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id
        self.discovery_service = TechnologyDiscoveryService(db, org_id)

    def _execute_splunk_search(self, query: str) -> List[Dict[str, Any]]:
        """Mock execution of a Splunk SPL query."""
        # This simulates hitting the Splunk REST API: POST /services/search/jobs
        if "metadata type=hosts" in query:
            return [
                {"host": "web-server-01"},
                {"host": "db-server-main"},
                {"host": "aws-ec2-worker-1"}
            ]
        if "stats values(sourcetype) by host" in query:
            return [
                {"host": "web-server-01", "sourcetypes": ["linux_secure", "nginx:access", "wazuh"]},
                {"host": "db-server-main", "sourcetypes": ["linux_secure", "postgresql:log", "wazuh"]},
                {"host": "aws-ec2-worker-1", "sourcetypes": ["aws:cloudtrail", "aws:ec2"]}
            ]
        return []

    def _map_sourcetype_to_product(self, sourcetype: str) -> Optional[Dict[str, str]]:
        """Maps Splunk sourcetypes to known products."""
        mapping = {
            "nginx:access": {"name": "nginx", "vendor": "F5"},
            "postgresql:log": {"name": "postgresql", "vendor": "PostgreSQL Global Development Group"},
            "wazuh": {"name": "wazuh-agent", "vendor": "Wazuh Inc."},
            "aws:cloudtrail": {"name": "AWS CloudTrail", "vendor": "Amazon Web Services"},
            "aws:ec2": {"name": "Amazon EC2", "vendor": "Amazon Web Services"},
            "linux_secure": {"name": "Linux", "vendor": "Open Source"},
        }
        return mapping.get(sourcetype)

    def discover_from_splunk(self, inventory_id: str) -> int:
        """Runs discovery jobs against Splunk to populate inventory."""
        
        # We assume Splunk is connected if they are running this.
        # Run SPL to get all hosts
        hosts_data = self._execute_splunk_search("| metadata type=hosts")
        
        # Run SPL to get sourcetypes per host to infer installed software
        sourcetypes_data = self._execute_splunk_search("| tstats count where index=* by host | appendpipe [search index=* | stats values(sourcetype) by host]")
        
        sourcetypes_by_host = {
            row["host"]: row.get("sourcetypes", [])
            for row in sourcetypes_data
        }

        assets_created = 0

        for host_info in hosts_data:
            hostname = host_info["host"]
            
            # Determine asset type based on hostname hints
            asset_type = AssetType.HOST
            if "aws" in hostname.lower():
                asset_type = AssetType.CLOUD_SERVICE

            # Create the asset
            asset = self.discovery_service.add_asset(
                inventory_id=inventory_id,
                asset_type=asset_type.value,
                hostname=hostname,
                operating_system=None,  # OS could be inferred from sourcetypes
                cloud_provider="AWS" if asset_type == AssetType.CLOUD_SERVICE else None
            )
            assets_created += 1

            # Map sourcetypes to products
            stypes = sourcetypes_by_host.get(hostname, [])
            for stype in stypes:
                product_info = self._map_sourcetype_to_product(stype)
                if product_info:
                    product = self.discovery_service.add_installed_product(
                        asset_id=asset.id,
                        product_name=product_info["name"],
                        vendor=product_info["vendor"],
                        installation_source="splunk_inference"
                    )
                    
                    # Store evidence hash
                    raw_evidence = f"{hostname}:{stype}"
                    evidence_hash = hashlib.sha256(raw_evidence.encode()).hexdigest()
                    
                    self.discovery_service.add_evidence_source(
                        product_id=product.id,
                        source_type="splunk",
                        connector_name="Splunk HEC",
                        raw_evidence_hash=evidence_hash
                    )
                    
        return assets_created
