"""
Connector Pydantic Schemas — Request/Response models for connector APIs.

Credentials are NEVER exposed in responses — only connector metadata.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================

class WazuhConnectRequest(BaseModel):
    """Schema for POST /api/v1/connectors/wazuh/connect strictly matching frontend."""
    org_id: str = Field(..., description="Organization ID")
    manager_host: str = Field(..., description="Wazuh manager hostname/IP")
    port: int = Field(55000, description="Wazuh API port")
    credentials: str = Field(..., min_length=8, description="Wazuh API key or credentials")


class ConnectorCreateRequest(BaseModel):
    """Register a new telemetry connector."""
    connector_type: str = Field(..., description="Platform type (github, wazuh, aws_security_hub, etc.)")
    display_name: str = Field(..., description="Human-readable connector name")
    auth_method: str = Field(..., description="Authentication method (api_key, oauth, iam_role, webhook)")
    credentials: Dict[str, Any] = Field(..., description="Credential payload (encrypted at rest)")
    config: Optional[Dict[str, Any]] = Field(None, description="Platform-specific configuration")
    sync_interval_minutes: int = Field(60, description="Auto-sync cadence in minutes")


class ConnectorUpdateRequest(BaseModel):
    """Update connector configuration (partial update)."""
    display_name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    sync_interval_minutes: Optional[int] = None
    status: Optional[str] = None


# =============================================================================
# Response Schemas
# =============================================================================

class ConnectorResponse(BaseModel):
    """Connector details — credentials are NEVER included."""
    id: str
    org_id: str
    connector_type: str
    display_name: str
    auth_method: str
    status: str
    last_sync_at: Optional[datetime] = None
    sync_interval_minutes: int
    health_status: Optional[str] = None
    permissions_validated: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}


class ConnectorListResponse(BaseModel):
    """Paginated connector listing."""
    connectors: List[ConnectorResponse]
    total: int


class ConnectorSyncResponse(BaseModel):
    """Sync operation result."""
    success: bool
    events_ingested: int = 0
    errors_count: int = 0
    duration_ms: int = 0
    error_details: Optional[str] = None


class ConnectorHealthResponse(BaseModel):
    """Health check result."""
    status: str
    latency_ms: Optional[int] = None
    message: str = ""
    checked_at: str = ""


class ConnectorSyncLogResponse(BaseModel):
    """Single sync audit log entry."""
    id: str
    connector_id: str
    sync_started_at: Optional[datetime] = None
    sync_completed_at: Optional[datetime] = None
    status: str
    events_ingested: int = 0
    errors_count: int = 0
    duration_ms: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
