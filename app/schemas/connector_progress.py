"""
Connector Progress Schemas — Request/Response models for tracking live connector connection progress.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ConnectorProgressState(str, Enum):
    CONNECTING = "CONNECTING"
    AUTHENTICATING = "AUTHENTICATING"
    FETCHING_DEVICES = "FETCHING_DEVICES"
    FETCHING_VULNERABILITIES = "FETCHING_VULNERABILITIES"
    NORMALIZING = "NORMALIZING"
    VERIFYING_CONTROLS = "VERIFYING_CONTROLS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

class ConnectorProgressEvent(BaseModel):
    """Event payload emitted during connector sync/connect step progression."""
    type: str = Field("connector_progress", description="Message type identifier for WebSocket parsing")
    org_id: str = Field(..., description="Target organization identifier")
    connector_type: str = Field(..., description="Platform type (e.g. 'wazuh')")
    state: ConnectorProgressState = Field(..., description="Current state in the connection lifecycle")
    status_message: str = Field(..., description="Human-readable description of current step status")
    details: Dict[str, Any] = Field(default_factory=dict, description="Metadata payloads (e.g. counts or errors)")
    timestamp: str = Field(..., description="ISO-formatted UTC timestamp of status check")

    model_config = {
        "use_enum_values": True,
        "json_schema_extra": {
            "example": {
                "type": "connector_progress",
                "org_id": "org-123",
                "connector_type": "wazuh",
                "state": "CONNECTING",
                "status_message": "Connecting to Wazuh Manager...",
                "details": {},
                "timestamp": "2026-05-30T23:10:00Z"
            }
        }
    }
