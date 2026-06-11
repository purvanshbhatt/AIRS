"""
Microsoft Graph Discovery Service.
"""
import hashlib
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.discovery import AssetType
from app.services.discovery.discovery import TechnologyDiscoveryService

class GraphDiscoveryService:
    """Service to discover technology assets via Microsoft Graph."""

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id
        self.discovery_service = TechnologyDiscoveryService(db, org_id)

    def _execute_mock_graph_discovery(self, inventory_id: str) -> int:
        """Mock discovery representing Microsoft Intune and Defender data."""
        
        # Simulating Intune managed devices
        devices = [
            {
                "id": "device-101",
                "deviceName": "desktop-sales-01",
                "operatingSystem": "Windows",
                "osVersion": "10.0.22631",
                "ipAddress": "192.168.1.50"
            },
            {
                "id": "device-102",
                "deviceName": "laptop-eng-04",
                "operatingSystem": "macOS",
                "osVersion": "14.2.1",
                "ipAddress": "192.168.1.65"
            }
        ]
        
        # Simulating Defender detected software
        software_inventory = {
            "device-101": [
                {"name": "chrome", "vendor": "Google", "version": "121.0"},
                {"name": "windows-11-client", "vendor": "Microsoft", "version": "10.0.22631"}
            ],
            "device-102": [
                {"name": "firefox", "vendor": "Mozilla", "version": "122.0"},
                {"name": "node.js", "vendor": "Node.js Foundation", "version": "22"},
                {"name": "python", "vendor": "Python Software Foundation", "version": "3.11"}
            ]
        }

        assets_created = 0

        for device in devices:
            device_id = device["id"]
            
            os_string = f"{device.get('operatingSystem', '')} {device.get('osVersion', '')}".strip()
            
            asset = self.discovery_service.add_asset(
                inventory_id=inventory_id,
                asset_type=AssetType.HOST.value,
                hostname=device.get("deviceName"),
                operating_system=os_string,
                ip_address=device.get("ipAddress")
            )
            assets_created += 1
            
            software_list = software_inventory.get(device_id, [])
            for sw in software_list:
                product = self.discovery_service.add_installed_product(
                    asset_id=asset.id,
                    product_name=sw["name"],
                    vendor=sw.get("vendor"),
                    version=sw.get("version"),
                    installation_source="microsoft_defender"
                )
                
                raw_evidence = f"{device_id}:{sw['name']}:{sw.get('version')}"
                evidence_hash = hashlib.sha256(raw_evidence.encode()).hexdigest()
                
                self.discovery_service.add_evidence_source(
                    product_id=product.id,
                    source_type="ms_graph",
                    connector_name="Microsoft Intune",
                    raw_evidence_hash=evidence_hash
                )
                
        return assets_created

    def discover_from_graph(self, inventory_id: str) -> int:
        """Runs discovery jobs against Microsoft Graph to populate inventory."""
        # For now, this is exclusively mock implementation.
        return self._execute_mock_graph_discovery(inventory_id)
