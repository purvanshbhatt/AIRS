"""
Pydantic schemas for the Onboarding Status API.

Provides a stable contract for the frontend to understand
organization onboarding progress without inferring state.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class OnboardingStep(BaseModel):
    """A single step in the onboarding flow."""
    step_id: str
    label: str
    completed: bool
    required: bool = True


class EvidenceStatus(BaseModel):
    """Current evidence/connector status for the organization."""
    connected_sources: int = 0
    verified: bool = False
    last_sync_at: Optional[datetime] = None


class OnboardingStatus(BaseModel):
    """Overall onboarding progress."""
    completed: bool = False
    current_step: str = "create_organization"
    steps: List[OnboardingStep] = []
    progress_pct: int = 0


class OnboardingResponse(BaseModel):
    """Full onboarding response for GET /api/orgs/{org_id}/onboarding."""
    organization_id: str
    organization_name: str
    mode: str  # pilot, demo, production
    onboarding: OnboardingStatus
    evidence: EvidenceStatus
    report_available: bool = False
    created_at: Optional[datetime] = None
