from abc import ABC, abstractmethod
from typing import Any, Dict, List
from app.sentinel.evidence.models import TelemetryEvidence

class EvidenceAdapter(ABC):
    """
    Abstract base class for all Evidence Adapters.
    Adapters are responsible for taking arbitrary payloads from a specific source
    (like Splunk, SentinelOne) and converting them into the canonical TelemetryEvidence schema.
    """
    
    @abstractmethod
    def parse_payload(self, raw_data: Any, org_id: str, connector_id: str) -> List[TelemetryEvidence]:
        """
        Parses the raw transport data into a list of canonical TelemetryEvidence items.
        """
        pass
