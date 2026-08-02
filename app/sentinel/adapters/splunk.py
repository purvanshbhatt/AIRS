import uuid
import hashlib
from typing import Any, Dict, List
from .base import EvidenceAdapter
from app.sentinel.evidence.models import TelemetryEvidence

class SplunkAdapter(EvidenceAdapter):
    """
    Adapter for converting Splunk search results (both from MCP and HEC)
    into standard TelemetryEvidence format.
    """
    
    def parse_payload(self, raw_data: Any, org_id: str, connector_id: str) -> List[TelemetryEvidence]:
        results = []
        # Support both a single dict and a list of dicts (from HEC / MCP)
        events = raw_data if isinstance(raw_data, list) else [raw_data]
        
        for event in events:
            # Normalize Splunk event shape
            # Splunk HEC usually wraps data in {"event": {...}}
            actual_event = event.get("event", event)
            
            # For MCP, it might be an object that was converted to a dict, or already parsed
            if hasattr(actual_event, "parsed_fields"):
                fields = actual_event.parsed_fields
                source_id = getattr(actual_event, "id", str(uuid.uuid4()))
            else:
                fields = actual_event
                source_id = fields.get("id") or str(uuid.uuid4())
                
            payload_str = str(fields)
            payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
            
            severity = fields.get("severity", "info")
            event_type = fields.get("evidence_type", "splunk_alert")
            
            tel_event = TelemetryEvidence(
                id=str(uuid.uuid4()),
                org_id=org_id,
                connector_id=connector_id,
                event_type=event_type,
                source_system="splunk",
                source_event_id=source_id,
                payload_hash=payload_hash,
                payload=fields,
                severity=severity,
                processed=False
            )
            results.append(tel_event)
            
        return results
