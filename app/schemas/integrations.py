"""Schemas for integration APIs (API keys, webhooks, external ingest)."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


ALLOWED_SCOPES = {
    "scores:read", "scores:write",
    "findings:read", "findings:write",
    "reports:read",
    "webhooks:read", "webhooks:write",
}


class ApiKeyCreateRequest(BaseModel):
    scopes: List[str] = Field(default_factory=lambda: ["scores:read"])

    @field_validator("scopes", mode="before")
    @classmethod
    def validate_scopes(cls, v: List[str]) -> List[str]:
        if not v:
            return ["scores:read"]
        for scope in v:
            if scope not in ALLOWED_SCOPES:
                raise ValueError(f"Invalid scope '{scope}'. Allowed: {sorted(ALLOWED_SCOPES)}")
        return v


class ApiKeyCreateResponse(BaseModel):
    id: str
    org_id: str
    prefix: str
    scopes: List[str]
    api_key: str  # Returned once at creation time
    created_at: datetime


class ApiKeyMetadataResponse(BaseModel):
    id: str
    org_id: str
    prefix: str
    scopes: List[str]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


class WebhookCreateRequest(BaseModel):
    url: HttpUrl
    event_types: List[str] = Field(default_factory=lambda: ["assessment.scored"])
    secret: Optional[str] = Field(default=None, max_length=255)


class WebhookResponse(BaseModel):
    id: str
    org_id: str
    url: str
    event_types: List[str]
    is_active: bool
    created_at: datetime


class WebhookTestResponse(BaseModel):
    webhook_id: str
    delivered: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


class WebhookUrlTestRequest(BaseModel):
    url: HttpUrl
    secret: Optional[str] = Field(default=None, max_length=255)
    event_type: str = Field(default="assessment.scored.test", max_length=128)


class WebhookUrlTestResponse(BaseModel):
    delivered: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    event_type: str
    payload: Dict[str, Any]


class ExternalTopFinding(BaseModel):
    id: str
    title: str
    severity: str
    framework_refs: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)


class ExternalLatestScoreResponse(BaseModel):
    org_id: str
    assessment_id: str
    timestamp: datetime
    overall_score: float
    risk_summary: Dict[str, Any] = Field(default_factory=dict)
    top_findings: List[ExternalTopFinding] = Field(default_factory=list)


class SplunkSeedRequest(BaseModel):
    org_id: Optional[str] = None


class SplunkSeedResponse(BaseModel):
    org_id: str
    source: str
    inserted: int
    connected: bool


class ExternalFindingResponse(BaseModel):
    id: str
    org_id: str
    source: str
    title: str
    severity: str
    created_at: datetime
    raw_json: Dict[str, Any]

    class Config:
        from_attributes = True


class SplunkHecConfigRequest(BaseModel):
    """Configure a live Splunk HEC connection for evidence-based verification."""
    base_url: str = Field(..., description="Splunk management URL (e.g. https://splunk.example.com:8089)")
    hec_token: str = Field(..., min_length=8, description="HTTP Event Collector token")


class SplunkEvidenceResult(BaseModel):
    """Result of a single evidence verification check."""
    control: str
    status: str  # verified | partial | not_verified | error | not_configured
    event_count: int = 0
    sample_events: List[Dict[str, Any]] = Field(default_factory=list)
    message: str = ""
    query_used: str = ""
    verified_at: Optional[str] = None


class SplunkEvidenceResponse(BaseModel):
    """All evidence verification results for an organization."""
    org_id: str
    results: List[SplunkEvidenceResult]
    overall_status: str  # verified | partial | not_verified | error
    verified_controls: int = 0
    total_controls: int = 0


# =============================================================================
# Wazuh Integration Schemas (XDR Layer)
# =============================================================================

class WazuhConfigRequest(BaseModel):
    """Request to configure Wazuh integration."""
    wazuh_host: str = Field(..., description="Wazuh manager hostname/IP")
    wazuh_api_key: str = Field(..., min_length=8, description="Wazuh API key")
    wazuh_port: int = Field(default=55000, description="Wazuh API port")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class AgentStatusDTO(BaseModel):
    """Agent status from Wazuh."""
    agent_id: str
    agent_name: str
    ip_address: str
    status: str  # "active", "pending", "never_connected", "disconnected"
    last_keepalive: Optional[str] = None
    os_platform: Optional[str] = None
    os_version: Optional[str] = None


class WazuhAgentStatusResponse(BaseModel):
    """Response for Wazuh agent status endpoint."""
    total_agents: int
    active_agents: int
    disconnected_agents: int
    pending_agents: int
    never_connected_agents: int
    disconnection_rate_percent: float
    agent_list: List[AgentStatusDTO]
    verified_at: str


class VulnerabilityAlertDTO(BaseModel):
    """Vulnerability alert from Wazuh."""
    cve_id: str
    title: str
    severity: str  # "critical", "high", "medium", "low", "info"
    cvss_score: float
    agent_id: str
    agent_name: str
    timestamp: str
    description: Optional[str] = None
    affected_packages: List[str] = []
    remediation: Optional[str] = None


class WazuhVulnerabilitiesResponse(BaseModel):
    """Response for Wazuh vulnerabilities endpoint."""
    total_vulnerabilities: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    vulnerabilities: List[VulnerabilityAlertDTO]
    verified_at: str


class SplunkLoggingHealthResponse(BaseModel):
    """Response for Splunk logging health verification."""
    logging_enabled: bool
    last_event_time: Optional[str] = None
    event_count_24h: int = 0
    event_count_7d: int = 0
    sourcetypes_active: List[str] = []
    indexes_active: List[str] = []
    verified_at: str


class SplunkQueryRequest(BaseModel):
    """Request to run a custom Splunk query."""
    query: str = Field(..., description="SPL query string")
    earliest: str = Field(default="-24h", description="Start time")
    latest: str = Field(default="now", description="End time")
    max_results: int = Field(default=1000, description="Maximum results to return")


class SplunkQueryResponse(BaseModel):
    """Response from custom Splunk query."""
    results: List[Dict[str, Any]]
    total_count: int
    query_used: str


# =============================================================================
# SIEM Integration Status & GHI Enhancement
# =============================================================================

class SIEMIntegrationStatus(BaseModel):
    """Overall SIEM integration health status."""
    wazuh_status: str  # "configured" | "not_configured" | "error"
    wazuh_message: Optional[str] = None
    wazuh_last_successful: Optional[str] = None
    
    splunk_status: str  # "configured" | "not_configured" | "error"
    splunk_message: Optional[str] = None
    splunk_last_successful: Optional[str] = None
    
    siem_verified_controls: int = 0
    siem_verified_percentage: float = 0.0


class SIEMVerifiedFinding(BaseModel):
    """Finding automatically generated from SIEM/XDR data."""
    title: str
    description: str
    severity: str  # "critical", "high", "medium", "low"
    source: str  # "wazuh" or "splunk"
    source_evidence: Dict[str, Any]
    ghi_impact: float = 0.0
    automatically_generated: bool = True


class GHIWithSIEMMultiplier(BaseModel):
    """GHI score enhanced with SIEM verification multiplier."""
    base_ghi: float
    siem_verified: bool
    siem_multiplier: float = 1.2  # If SIEM-verified controls present
    final_ghi: float
    grade: str
    verified_controls_count: int


class RoadmapTrackerItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    phase: str = Field(default="30")
    status: str = Field(default="not_started")
    priority: str = Field(default="medium")
    owner: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    effort: Optional[str] = None


class RoadmapTrackerItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    effort: Optional[str] = None


class RoadmapTrackerItemResponse(BaseModel):
    id: str
    assessment_id: str
    title: str
    description: Optional[str] = None
    phase: str
    status: str
    priority: str
    owner: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    effort: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoadmapTrackerListResponse(BaseModel):
    items: List[RoadmapTrackerItemResponse]
    total: int
