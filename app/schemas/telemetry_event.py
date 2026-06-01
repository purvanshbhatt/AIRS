"""
Telemetry Event Pydantic Schemas — Batch ingestion and query models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================

class TelemetryEventIngest(BaseModel):
    """Single event within a batch ingest request."""
    event_type: str = Field(..., description="Event classification")
    source_system: str = Field(..., description="Source platform identifier")
    source_event_id: str = Field(..., description="Native event ID from source")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Raw event payload")
    severity: Optional[str] = Field(None, description="Severity level")


class TelemetryBatchIngestRequest(BaseModel):
    """Batch telemetry event ingestion."""
    events: List[TelemetryEventIngest] = Field(..., description="Events to ingest")


# =============================================================================
# Response Schemas
# =============================================================================

class TelemetryEventResponse(BaseModel):
    """Single telemetry event detail."""
    id: str
    org_id: str
    connector_id: Optional[str] = None
    event_type: str
    source_system: str
    source_event_id: str
    payload_hash: str
    severity: Optional[str] = None
    processed: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TelemetryEventListResponse(BaseModel):
    """Paginated telemetry event listing."""
    events: List[TelemetryEventResponse]
    total: int


class TelemetryBatchIngestResponse(BaseModel):
    """Result of a batch ingest operation."""
    ingested: int = 0
    duplicates_skipped: int = 0
    errors: int = 0


class TelemetryStatsResponse(BaseModel):
    """Aggregated telemetry statistics."""
    total_events: int = 0
    events_24h: int = 0
    events_7d: int = 0
    by_source: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_severity: Dict[str, int] = Field(default_factory=dict)
