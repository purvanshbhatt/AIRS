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
