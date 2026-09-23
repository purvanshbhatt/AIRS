"""
Pydantic schemas for Agent Audit endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentAuditCreateRequest(BaseModel):
    audit_window: str = Field(default="48h", description="Duration of observation window (e.g., 48h)")
    source_type: str = Field(default="splunk", description="Data source: splunk, multi_source, agent_trace, upload")
    agent_name: Optional[str] = Field(default="Customer Support Agent", description="Primary agent under audit")
    environment: Optional[str] = Field(default="Production", description="Environment: Production, Staging, Development")
    business_context: Optional[str] = Field(default=None, description="Operational business context")


class AgentTelemetryIngestRequest(BaseModel):
    events: List[Dict[str, Any]] = Field(default_factory=list, description="List of raw or normalized agent telemetry events")


class AgentAuditExplanationResponse(BaseModel):
    audit_id: str
    explanation: str
    synthesized_at: str
