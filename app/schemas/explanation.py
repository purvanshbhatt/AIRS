"""
Pydantic schemas for the Explanation (Business Language) API.

Gemini transforms deterministic facts into business-friendly narratives.
Gemini MUST NOT calculate scores, create findings, or modify framework mappings.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SubjectType(str, Enum):
    """Types of subjects that can be explained."""
    FINDING = "finding"
    READINESS = "readiness"
    CONNECTOR = "connector"
    RECOVERY = "recovery"
    EVIDENCE = "evidence"


class Audience(str, Enum):
    """Target audience for the explanation."""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    BOARD = "board"


class ExplanationRequest(BaseModel):
    """Request body for generating a business-language explanation."""
    subject_type: SubjectType
    subject_id: str = Field(..., min_length=1, max_length=255)
    audience: Audience = Audience.EXECUTIVE


class SourceFact(BaseModel):
    """A deterministic fact that grounds the explanation."""
    fact_type: str  # e.g. "finding_severity", "readiness_score"
    key: str
    value: str
    source: str  # e.g. "deterministic_scoring", "telemetry"


class ExplanationContent(BaseModel):
    """The generated explanation payload."""
    plain_language: str
    business_impact: str
    recommended_action: str


class ExplanationResponse(BaseModel):
    """Response from the explanation endpoint."""
    explanation: ExplanationContent
    source_facts: List[SourceFact]
    generated_at: datetime
    model: str
    subject_type: str
    subject_id: str
    audience: str
