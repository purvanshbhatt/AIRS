"""
Splunk Connector implementation for health monitoring and setup.
"""
from sqlalchemy.orm import Session
from app.models.connector import Connector, ConnectorType, ConnectorStatus
from app.services.audit import record_connector_audit

def initialize_splunk_connector(db: Session, org_id: str, mcp_url: str, api_key: str, created_by: str) -> Connector:
    """Initialize or update a Splunk connector for an organization."""
    connector = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.connector_type == ConnectorType.splunk
    ).first()
    
    if not connector:
        connector = Connector(
            org_id=org_id,
            connector_type=ConnectorType.splunk,
            display_name="Splunk Enterprise Security",
            auth_method="api_key",
            status=ConnectorStatus.active,
            config={"mcp_url": mcp_url},
            health_status="healthy",
            created_by=created_by
        )
        db.add(connector)
    else:
        connector.config = {"mcp_url": mcp_url}
        connector.status = ConnectorStatus.active
        connector.health_status = "healthy"
        
    db.commit()
    db.refresh(connector)
    
    record_connector_audit(
        db=db,
        org_id=org_id,
        action="configured",
        actor=created_by,
        connector_type="splunk",
        status="success"
    )
    
    return connector
