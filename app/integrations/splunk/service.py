"""
Splunk telemetry ingestion service for ResilAI Sentinel.
"""
import uuid
import json
from sqlalchemy.orm import Session
from .client import SplunkMCPClient
from app.models.telemetry_event import TelemetryEvent
from app.models.connector import Connector, ConnectorType, ConnectorStatus
import hashlib
import logging

logger = logging.getLogger("airs.splunk_service")

async def ingest_splunk_telemetry(db: Session, org_id: str) -> int:
    """Polls Splunk MCP for recent notable events and ingests them into TelemetryEvent."""
    connector = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.connector_type == ConnectorType.splunk,
        Connector.status == ConnectorStatus.active
    ).first()
    
    if not connector:
        logger.warning(f"No active Splunk connector found for org {org_id}")
        return 0
        
    mcp_url = connector.config.get("mcp_url")
    # For demo, using dummy API key instead of decrypted credential
    client = SplunkMCPClient(mcp_url=mcp_url, api_key="dummy_key")
    
    try:
        search_resp = await client.search('search index=notable')
        
        events_ingested = 0
        for event in search_resp.events:
            # Check if event already exists
            existing = db.query(TelemetryEvent).filter(
                TelemetryEvent.org_id == org_id,
                TelemetryEvent.source_system == "splunk",
                TelemetryEvent.source_event_id == event.id
            ).first()
            
            if not existing:
                payload_str = event.model_dump_json()
                payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
                
                # Derive event type and severity
                severity = event.parsed_fields.get("severity", "info")
                event_type = event.parsed_fields.get("evidence_type", "splunk_alert")
                
                tel_event = TelemetryEvent(
                    id=str(uuid.uuid4()),
                    org_id=org_id,
                    connector_id=connector.id,
                    event_type=event_type,
                    source_system="splunk",
                    source_event_id=event.id,
                    payload_hash=payload_hash,
                    payload=event.model_dump(mode="json"),
                    severity=severity,
                    processed=False
                )
                db.add(tel_event)
                events_ingested += 1
                
        if events_ingested > 0:
            db.commit()
            logger.info(f"Ingested {events_ingested} new Splunk telemetry events for org {org_id}")
            
        return events_ingested
        
    except Exception as e:
        logger.error(f"Failed to ingest Splunk telemetry: {e}")
        connector.health_status = "error"
        connector.error_message = str(e)
        db.commit()
        return 0
