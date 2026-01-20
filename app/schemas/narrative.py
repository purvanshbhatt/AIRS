"""
Pydantic schemas for LLM Narrative generation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class NarrativeType(str, Enum):
    """Types of narratives available."""
    EXECUTIVE_SUMMARY = "executive_summary"
    ROADMAP = "roadmap"
    FINDING_REWRITE = "finding_rewrite"
    ALL = "all"


class NarrativeRequest(BaseModel):
    """Request for narrative generation."""
    narrative_types: List[NarrativeType] = Field(
        default=[NarrativeType.ALL],
        description="Which narratives to generate"
    )
    include_finding_rewrites: bool = Field(
        default=False,
        description="Also rewrite findings in business tone"
    )


class NarrativeContent(BaseModel):
    """Single narrative content."""
    narrative_type: str
    content: str
    llm_generated: bool = False
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None


class FindingRewrite(BaseModel):
    """Rewritten finding in business tone."""
    original_title: str
    original_severity: str
    business_content: str
    llm_generated: bool = False


class NarrativeResponse(BaseModel):
    """Response with generated narratives."""
    assessment_id: str
    llm_enabled: bool
    executive_summary: Optional[NarrativeContent] = None
    roadmap: Optional[NarrativeContent] = None
    finding_rewrites: List[FindingRewrite] = []
    
    # Preserve original deterministic data (read-only)
    original_score: float
    original_maturity_level: int
    original_maturity_name: str


class LLMStatusResponse(BaseModel):
    """LLM feature status."""
    enabled: bool
    available: bool
    model: Optional[str] = None
    message: str
