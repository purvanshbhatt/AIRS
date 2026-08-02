"""
Pydantic schemas for Sprint 1.8 — Readiness Drivers & Ledger API.

Strict typing per the spec's directive: "Ensure TypeScript interfaces
perfectly map to Pydantic schemas, especially for the new
ReadinessDriver and EvidenceConfidence models."
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReadinessDriver(BaseModel):
    """A single readiness impact driver surfaced for executive review."""

    driver_type: str = Field(..., description="Structural category (kev|eol|coverage_gap|...).")
    driver_item: Optional[str] = Field(
        None, description="Identifier of the underlying asset/control/item."
    )
    impact: float = Field(..., description="Signed impact contribution to the readiness delta.")
    evidence_source: str = Field(..., description="Evidence origin family (telemetry|deployment|vendor|...).")


class ReadinessDriversResponse(BaseModel):
    """Response shape for ``GET /api/v1/readiness/drivers``."""

    org_id: str
    positive_drivers: List[ReadinessDriver] = Field(default_factory=list)
    negative_drivers: List[ReadinessDriver] = Field(default_factory=list)


class ExecutiveAction(BaseModel):
    """A Monday-morning action rendered from a negative driver."""

    driver_type: str
    item: Optional[str]
    impact: float
    evidence_source: str
    rationale: str


class ExecutiveActionsResponse(BaseModel):
    """Response shape for ``GET /api/v1/readiness/actions``."""

    org_id: str
    actions: List[ExecutiveAction] = Field(default_factory=list)


class ReadinessLedgerEntryResponse(BaseModel):
    """Single-row immutability audit response."""

    id: str
    org_id: str
    timestamp: datetime
    previous_score: float
    new_score: float
    delta: float
    driver_type: Optional[str] = None
    driver_item: Optional[str] = None
    impact: Optional[float] = None
    evidence_source: Optional[str] = None
    created_by: Optional[str] = None


class ReadinessLedgerResponse(BaseModel):
    """Response shape for ``GET /api/v1/readiness/ledger``."""

    org_id: str
    entries: List[ReadinessLedgerEntryResponse] = Field(default_factory=list)
    count: int = 0


class ReadinessTimelinePoint(BaseModel):
    """Time-series point for the dashboard timeline."""

    timestamp: datetime
    new_score: float
    delta: float
    driver_type: Optional[str]


class ReadinessTimelineResponse(BaseModel):
    """Response shape for ``GET /api/v1/readiness/timeline``."""

    org_id: str
    points: List[ReadinessTimelinePoint] = Field(default_factory=list)
    count: int = 0
