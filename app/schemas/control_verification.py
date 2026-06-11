from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class TelemetryIngestRequest(BaseModel):
    control_id: str
    telemetry_event_id: Optional[str] = None
    connector_id: Optional[str] = None
    status: str = "PASS"
    evidence_payload: Optional[Dict[str, Any]] = None


class AttestRequest(BaseModel):
    reason: str


class VerificationDetail(BaseModel):
    control_id: str
    state: str
    confidence_level: str
    last_verified_at: Optional[str]


class VerificationSummaryResponse(BaseModel):
    total_controls: int
    verified: int
    partial: int
    self_attested: int
    not_verified: int
    high_confidence: int
    details: List[VerificationDetail]


class VerificationResultResponse(BaseModel):
    id: str
    control_id: str
    state: str
    confidence_level: str
    
    class Config:
        orm_mode = True
        from_attributes = True
