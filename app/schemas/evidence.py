from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import hashlib
import json

class EvidenceSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ProviderTransport(str, Enum):
    MCP = "mcp"
    HEC = "hec"
    REST = "rest"
    GRAPHQL = "graphql"
    SDK = "sdk"
    WEBHOOK = "webhook"

class EvidenceConfidence(BaseModel):
    """
    Measures the veracity and quality of the collected evidence.
    Each dimension is a score from 0-100.
    """
    freshness: int = Field(default=100, description="How recent is the data?")
    completeness: int = Field(default=100, description="Are all expected fields present?")
    integrity: int = Field(default=100, description="Is the data signed or hashed by the source?")
    availability: int = Field(default=100, description="Reliability of the connection.")
    overall_confidence: int = 100

class NormalizedEvidence(BaseModel):
    """
    The transport-agnostic representation of an event or state
    from a downstream security tool.
    """
    source_connector: str
    asset_id: Optional[str] = None
    control_id: Optional[str] = None
    event_type: str
    severity: EvidenceSeverity = EvidenceSeverity.INFO
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Traceability
    evidence_hash: str = ""
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    confidence: EvidenceConfidence = Field(default_factory=EvidenceConfidence)
    
    def compute_hash(self) -> str:
        """Deterministically hash the payload for the immutable ledger."""
        payload_str = json.dumps(self.raw_payload, sort_keys=True, default=str)
        # Include source and timestamp in hash for uniqueness
        base_string = f"{self.source_connector}|{self.timestamp.isoformat()}|{payload_str}"
        self.evidence_hash = hashlib.sha256(base_string.encode()).hexdigest()
        return self.evidence_hash

class EvidenceCollectionResult(BaseModel):
    provider_name: str
    transport: ProviderTransport
    evidence_count: int
    errors: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    evidence: List[NormalizedEvidence] = Field(default_factory=list)

class ConnectorConfidenceDetail(BaseModel):
    connector_name: str
    confidence_score: float
    factors: Dict[str, Any]

class OrgConfidenceResponse(BaseModel):
    org_id: str
    aggregate_score: float
    # Per-connector confidence detail. Originally named ``details``
    # in earlier drafts; renamed to ``connectors`` to match the
    # documented response shape used by the Dashboard Evidence
    # Confidence gauge.
    connectors: List[ConnectorConfidenceDetail]

