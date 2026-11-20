from sqlalchemy.orm import Session
from app.models.connector import Connector, ConnectorStatus
from app.services.clinic_engine.v2.contracts import CoverageReport, CoverageArea

# Define ALL possible security areas a clinic might need monitored
ALL_COVERAGE_AREAS = [
    ("Users & Identities", ["microsoft", "okta", "google_workspace"]),
    # No capability produces an email check yet, so no connector counts as
    # covering this area. Listing Microsoft 365 here made reports say email
    # security was "Monitored" when nothing looked at it.
    ("Email Security", ["email_security_gateway"]),  # Future
    ("Multi-Factor Authentication", ["microsoft", "okta"]),
    ("Devices & Endpoints", ["microsoft", "wazuh", "crowdstrike"]),
    ("Backup & Recovery", ["veeam", "datto"]),
    ("Firewall", ["firewall"]),  # Future
    ("Medical Devices", ["medical_device_monitor"]),  # Future
    ("Network Security", ["wazuh", "firewall"]),
    ("Vulnerability Scanning", ["wazuh", "qualys"]),
    # The AWS connector is registered under either "aws" or "aws_security_hub".
    ("Cloud Security", ["aws_security_hub", "aws", "azure_security_center", "gcp_scc"]),
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
    "aws": "Amazon Web Services",
    "crowdstrike": "CrowdStrike",
    "datto": "Datto Backup"
}

def connected_connectors(db: Session, org_id: str) -> list:
    """Connectors that are delivering data for this organization.

    ``active`` connectors, plus a connector that is in the middle of a sync
    (``syncing``) and has completed a sync before. A sync flips the status to
    ``syncing`` until it finishes; counting only ``active`` made a report
    generated during a sync say nothing was connected (coverage "not
    monitored", verification confidence 0, readiness score 0). A connector
    still on its first sync has delivered nothing yet and is not counted.
    """
    rows = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.status.in_([ConnectorStatus.active, ConnectorStatus.syncing]),
    ).order_by(Connector.display_name).all()

    def _status(c) -> str:
        return c.status.value if hasattr(c.status, 'value') else str(c.status)

    return [c for c in rows if _status(c) == ConnectorStatus.active.value or c.last_sync_at is not None]


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
        active_connectors = connected_connectors(self.db, org_id)
        
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
