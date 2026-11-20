"""
Pydantic schemas for Compliance Applicability Engine.
"""

from pydantic import BaseModel
from typing import List, Optional


class ApplicableFramework(BaseModel):
    """A single applicable compliance framework."""
    framework: str                     # e.g. "HIPAA", "SOC 2", "PCI-DSS"
    reason: str                        # e.g. "Organization processes PHI"
    mandatory: bool = True             # Whether compliance is mandatory vs. recommended
    reference_url: Optional[str] = None
    jurisdiction: Optional[str] = None   # e.g. "European Union", "Saudi Arabia"
    # Which ResilAI checks can support this framework, and what it does not cover.
    evidence_note: Optional[str] = None


class ComplianceApplicabilityResponse(BaseModel):
    """Response for applicable frameworks endpoint."""
    org_id: str
    frameworks: List[ApplicableFramework] = []
    total: int = 0
