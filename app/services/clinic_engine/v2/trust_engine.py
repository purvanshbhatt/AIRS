"""
Trust Engine

Builds trust context for each moment and the overall trust explanation.
Doctors don't trust 'Confidence: 96%'. They trust 'Because Microsoft synchronized 2 minutes ago.'
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.connector import Connector, ConnectorStatus
from app.services.clinic_engine.v2.contracts import (
    VerificationContext,
    VerificationExplanation,
    VerificationReason,
)
from app.services.clinic_engine.v2.schema import ClinicMoment

# Source name mapping (NEVER expose internal identifiers)
SOURCE_DISPLAY_NAMES = {
    "microsoft": "Microsoft 365",
    "wazuh": "Security Monitor",
    "veeam": "Backup System",
    "splunk": "Security Analytics",
    "okta": "Identity Provider",
    "google_workspace": "Google Workspace",
    "crowdstrike": "CrowdStrike",
    "datto": "Datto Backup",
}

class TrustEngine:
    """Builds trust context and explanations for clinic readiness."""
    
    def __init__(self, db: Session):
        """Initialize with a database session.
        
        Args:
            db (Session): SQLAlchemy database session.
        """
        self.db = db
        self._connector_cache = {}
    
    def build_verification_context(self, moment: ClinicMoment, org_id: str) -> VerificationContext:
        """Build verification metadata for a single moment.
        
        Args:
            moment (ClinicMoment): The clinic moment to build verification for.
            org_id (str): The organization ID.
            
        Returns:
            VerificationContext: The verification metadata for the moment.
        """
        # Infer source connector from capability_id or automation_type
        source_system = "unknown"
        if "unauthorized_access" in moment.capability_id or "disable_account" in moment.capability_id:
            source_system = "microsoft"
        elif "device_compromise" in moment.capability_id or "remediate_device" in moment.capability_id:
            source_system = "wazuh"
        elif "recovery_readiness" in moment.capability_id or "verify_backup" in moment.capability_id:
            source_system = "veeam"
            
        # Try to extract from moment's first action if available
        if moment.actions and moment.actions[0].automation_type:
            auto_type = moment.actions[0].automation_type
            if auto_type.startswith("m365_"):
                source_system = "microsoft"
            elif auto_type.startswith("wazuh_"):
                source_system = "wazuh"
                
        # Look up the connector in the DB (using cache to prevent N+1)
        if org_id not in self._connector_cache:
            try:
                connectors = self.db.query(Connector).filter(
                    Connector.org_id == org_id
                ).all()
                self._connector_cache[org_id] = {
                    (c.connector_type.value if hasattr(c.connector_type, 'value') else str(c.connector_type)): c 
                    for c in connectors
                }
            except Exception:
                self._connector_cache[org_id] = {}
                
        connector = self._connector_cache[org_id].get(source_system)
        
        confidence = 100
        verification_status = "unverified"
        connector_health = "unreachable"
        last_sync = None
        
        if connector:
            last_sync = connector.last_sync_at
            connector_health = connector.health_status or "unknown"
            
            if connector_health != "healthy":
                confidence -= 20
                
            if last_sync:
                if last_sync.tzinfo is None:
                    last_sync = last_sync.replace(tzinfo=timezone.utc)
                hours_since = (datetime.now(timezone.utc) - last_sync).total_seconds() / 3600.0
                penalty = int(hours_since * 5)
                penalty = min(penalty, 30) # max -30
                confidence -= penalty
                
                if hours_since < 2:
                    verification_status = "verified"
                else:
                    verification_status = "stale"
            
        # Floor at 10
        confidence = max(confidence, 10)
        
        data_age = self._humanize_data_age(last_sync) if last_sync else "Unknown"
        
        return VerificationContext(
            verification_source=self._humanize_source(source_system),
            last_verified_at=last_sync,
            connector_health=connector_health,
            confidence_pct=confidence,
            verification_status=verification_status,
            data_age_description=f"Checked {data_age}" if last_sync else "Not recently checked",
            can_reverify=True,
            verification_method="Cached from last sync" if last_sync else "Unknown"
        )
    
    def build_overall_verification(self, org_id: str) -> VerificationExplanation:
        """Build the overall verification explanation for the report.
        
        Args:
            org_id (str): The organization ID.
            
        Returns:
            VerificationExplanation: The overall verification explanation.
        """
        try:
            connectors = self.db.query(Connector).filter(
                Connector.org_id == org_id,
                Connector.status == ConnectorStatus.active
            ).order_by(Connector.display_name).all()
        except Exception:
            connectors = []
        
        reasons = []
        total_confidence = 0
        
        if not connectors:
            return VerificationExplanation(
                confidence_pct=0,
                reasons=[VerificationReason(icon="warning", text="No active security monitoring connected.")]
            )
            
        has_failures = False
            
        for conn in connectors:
            # Build trust reason per connector
            conn_name = self._humanize_source(conn.connector_type.value if hasattr(conn.connector_type, 'value') else conn.connector_type)
            health = conn.health_status
            
            if health == "healthy" and conn.last_sync_at:
                age = self._humanize_data_age(conn.last_sync_at)
                reasons.append(VerificationReason(icon="check", text=f"{conn_name} synchronized {age}."))
                total_confidence += 100
            else:
                has_failures = True
                reasons.append(VerificationReason(icon="error", text=f"{conn_name} is currently {health or 'unavailable'}."))
                total_confidence += 50
                
        if not has_failures:
            reasons.append(VerificationReason(icon="check", text="No connector failures detected."))
            
        avg_confidence = int(total_confidence / len(connectors))
        
        return VerificationExplanation(
            confidence_pct=avg_confidence,
            reasons=reasons
        )
    
    def _humanize_data_age(self, dt: datetime) -> str:
        """Convert a datetime to 'X minutes/hours/days ago'.
        
        Args:
            dt (datetime): The datetime to humanize.
            
        Returns:
            str: Human-readable time elapsed.
        """
        if not dt:
            return "unknown time ago"
            
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        delta = now - dt
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = int(seconds / 60)
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
    
    def _humanize_source(self, source_system: str) -> str:
        """Convert internal source name to customer-facing name.
        
        Args:
            source_system (str): Internal source system identifier.
            
        Returns:
            str: Customer-facing display name.
        """
        if not isinstance(source_system, str):
            source_system = str(source_system)
        return SOURCE_DISPLAY_NAMES.get(source_system, source_system.replace('_', ' ').title())
