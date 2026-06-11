import uuid
import hashlib
import logging
from sqlalchemy.orm import Session
from app.sentinel.db.models import SentinelTelemetryEvent
from .connector import get_splunk_config
from .client import SplunkNativeClient

logger = logging.getLogger("airs.sentinel_splunk.service")

async def ingest_telemetry(db: Session, org_id: str, query: str = 'search index=main source="WinEventLog:Security" (EventCode=4624 OR EventCode=4625 OR EventCode=4672) | head 5') -> int:
    """
    Executes a search against the live Splunk instance and persists results
    to the Sentinel isolated database.
    """
    config = get_splunk_config()
    client = SplunkNativeClient(config)
    
    try:
        search_resp = await client.search(query)
        events_ingested = 0
        
        for event in search_resp.events:
            # Prevent duplicates by hashing payload since _bkt isn't strictly unique across restarts
            payload_str = event.model_dump_json()
            payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
            
            existing = None
            if hasattr(SentinelTelemetryEvent, 'payload_hash'):
                existing = db.query(SentinelTelemetryEvent).filter(
                    SentinelTelemetryEvent.org_id == org_id,
                    SentinelTelemetryEvent.source_system == "splunk",
                    SentinelTelemetryEvent.payload_hash == payload_hash
                ).first()
            
            if not existing:
                existing_fallback = db.query(SentinelTelemetryEvent).filter(
                    SentinelTelemetryEvent.org_id == org_id,
                    SentinelTelemetryEvent.source_system == "splunk",
                    SentinelTelemetryEvent.source_event_id == event.id
                ).first()
                if existing_fallback:
                    continue

            if not existing:
                severity = event.parsed_fields.get("severity", "high")
                event_code = event.parsed_fields.get("EventCode", "")
                
                # Demo Mapping: Map real Windows Security events to Sentinel Evidence Types
                if event_code == "4624" or event_code == "4625":
                    event_type = "missing_mfa"
                elif event_code == "4672":
                    event_type = "logging_gap"
                else:
                    event_type = event.parsed_fields.get("evidence_type", "splunk_alert")
                
                tel_event = SentinelTelemetryEvent(
                    id=str(uuid.uuid4()),
                    org_id=org_id,
                    event_type=event_type,
                    source_system="splunk",
                    source_event_id=event.id,
                    payload=event.parsed_fields,
                    severity=severity,
                    processed=False
                )
                
                if hasattr(tel_event, 'payload_hash'):
                    tel_event.payload_hash = payload_hash

                db.add(tel_event)
                events_ingested += 1
                
        if events_ingested > 0:
            db.commit()
            logger.info(f"Ingested {events_ingested} new Splunk telemetry events for org {org_id}")
            
        return events_ingested
        
    except Exception as e:
        logger.error(f"Failed to ingest Splunk telemetry: {e}")
        return 0

async def push_test_evidence(evidence_type: str, severity: str, title: str) -> bool:
    """Pushes a structured JSON event to Splunk HEC for testing ingestion pipelines."""
    config = get_splunk_config()
    client = SplunkNativeClient(config)
    
    event_data = {
        "evidence_type": evidence_type,
        "severity": severity,
        "title": title,
        "description": "Auto-generated test event"
    }
    
    return await client.send_hec_event(event_data)

async def fetch_recent_security_events(minutes_back: int = 15) -> list[dict]:
    """
    Connects to the Splunk Management REST API using env vars,
    executes a search query, and maps returned events to a dictionary
    representing the TelemetryEvidence model.
    """
    query = 'search index=* "SENTINEL_HACKATHON_TEST" OR "MFA Disabled" OR "Ransomware" | head 5'
    config = get_splunk_config()
    client = SplunkNativeClient(config)
    
    try:
        search_resp = await client.search(query, earliest_time=f"-{minutes_back}m")
        results = []
        for event in search_resp.events:
            # Map to internal TelemetryEvidence dictionary representation
            evidence = {
                "timestamp": event.time,
                "host": event.host,
                "raw_text": event.raw
            }
            results.append(evidence)
        return results
    except Exception as e:
        logger.error(f"Splunk API Error in fetch_recent_security_events: {e}")
        return []
