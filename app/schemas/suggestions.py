"""
Pydantic schemas for question suggestions.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.base import BaseSchema


class SuggestedQuestion(BaseSchema):
    """A single question suggestion with enrichment metadata."""

    id: str = Field(..., description="Question ID (e.g. tl_01)")
    question_text: str = Field(..., description="Human-readable question text")
    domain_id: str = Field(..., description="Parent domain (e.g. telemetry_logging)")
    framework_tags: List[str] = Field(
        ...,
        description="Framework references (NIST-CSF, CIS, OWASP-AI, NIST-AI)",
    )
    maturity_level: str = Field(
        ...,
        description="basic | managed | advanced",
        pattern="^(basic|managed|advanced)$",
    )
    effort_level: str = Field(
        ...,
        description="low | medium | high",
        pattern="^(low|medium|high)$",
    )
    impact_level: str = Field(
        ...,
        description="low | medium | high",
        pattern="^(low|medium|high)$",
    )
    control_function: str = Field(
        ...,
        description="NIST CSF 2.0 function: govern | identify | protect | detect | respond | recover",
        pattern="^(govern|identify|protect|detect|respond|recover)$",
    )


class SuggestionsResponse(BaseSchema):
    """Response wrapper for question suggestions."""

    suggestions: List[SuggestedQuestion]
    total_count: int = Field(..., description="Total suggestions returned")
    org_maturity: Optional[str] = Field(
        None,
        description="Inferred org maturity: basic | managed | advanced",
    )
    weakest_functions: Optional[List[str]] = Field(
        None,
        description="Control functions targeted by suggestions",
    )
