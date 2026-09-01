from sqlalchemy.orm import Session
from app.models.connector import Connector, ConnectorStatus
from app.services.clinic_engine.v2.contracts import CoverageReport, CoverageArea

# Define ALL possible security areas a clinic might need monitored
ALL_COVERAGE_AREAS = [
    ("Users & Identities", ["microsoft", "okta", "google_workspace"]),
    ("Email Security", ["microsoft", "google_workspace"]),
    ("Multi-Factor Authentication", ["microsoft", "okta"]),
    ("Devices & Endpoints", ["microsoft", "wazuh", "crowdstrike"]),
    ("Backup & Recovery", ["veeam", "datto"]),
    ("Firewall", ["firewall"]),  # Future
    ("Medical Devices", ["medical_device_monitor"]),  # Future
    ("Network Security", ["wazuh", "firewall"]),
    ("Vulnerability Scanning", ["wazuh", "qualys"]),
    ("Cloud Security", ["aws_security_hub", "azure_security_center", "gcp_scc"]),
    ("Security Analytics", ["splunk"]),
    ("Local Backups", ["local_backup_monitor"]),  # Future
]

SOURCE_MAPPING = {
    "microsoft": "Microsoft 365",
    "wazuh": "Security Monitor",
    "veeam": "Backup System",
    "splunk": "Security Analytics",
    "okta": "Identity Provider",
    "google_workspace": "Google Workspace",
    "aws_security_hub": "AWS Security Hub",
    "crowdstrike": "CrowdStrike",
    "datto": "Datto Backup"
}

class CoverageEngine:
    """Coverage Engine calculates visibility gaps in clinic monitoring."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def assess_coverage(self, org_id: str) -> CoverageReport:
        """
        Determine what we monitor and what we don't for this org.
        
        Args:
            org_id: The organization ID to assess coverage for.
            
        Returns:
            CoverageReport detailing monitored and unmonitored security areas.
        """
        active_connectors = self.db.query(Connector).filter(
            Connector.org_id == org_id,
            Connector.status == ConnectorStatus.active
        ).all()
        
        active_types = {c.connector_type.value if hasattr(c.connector_type, 'value') else str(c.connector_type) for c in active_connectors}
        
        monitored = []
        not_monitored = []
        
        for area_name, required_types in ALL_COVERAGE_AREAS:
            matched_type = None
            for req_type in required_types:
                if req_type in active_types:
                    matched_type = req_type
                    break
            
            if matched_type:
                monitored.append(CoverageArea(
                    area=area_name,
                    monitored=True,
                    source=SOURCE_MAPPING.get(matched_type, matched_type)
                ))
            else:
                not_monitored.append(CoverageArea(
                    area=area_name,
                    monitored=False,
                    source=None
                ))
                
        total = len(ALL_COVERAGE_AREAS)
        coverage_pct = int((len(monitored) / total) * 100) if total > 0 else 0
        
        return CoverageReport(
            coverage_pct=coverage_pct,
            monitored=monitored,
            not_monitored=not_monitored
        )
