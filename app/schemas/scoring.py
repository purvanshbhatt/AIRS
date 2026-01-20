"""
Pydantic schemas for scoring API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from app.schemas.base import BaseSchema


class AssessmentAnswers(BaseModel):
    """Input schema for assessment answers."""
    
    answers: Dict[str, Any] = Field(
        ...,
        description="Mapping of question_id to answer value",
        example={
            "tl_01": True,
            "tl_02": True,
            "tl_03": False,
            "tl_04": True,
            "tl_05": 90,
            "tl_06": True,
            "dc_01": 85,
            "dc_02": True,
            "dc_03": True,
            "dc_04": False,
            "dc_05": True,
            "dc_06": True,
            "iv_01": False,
            "iv_02": True,
            "iv_03": True,
            "iv_04": False,
            "iv_05": False,
            "iv_06": True,
            "ir_01": True,
            "ir_02": False,
            "ir_03": True,
            "ir_04": True,
            "ir_05": True,
            "ir_06": False,
            "rs_01": True,
            "rs_02": True,
            "rs_03": False,
            "rs_04": True,
            "rs_05": 24,
            "rs_06": True
        }
    )


class QuestionScore(BaseSchema):
    """Score details for a single question."""
    
    question_id: str
    question_text: str
    answer: Optional[Any]
    points_earned: float
    points_possible: float


class DomainScore(BaseSchema):
    """Score details for a domain."""
    
    domain_id: str
    domain_name: str
    weight: int
    raw_points: float
    max_raw_points: int
    score: float = Field(..., ge=0, le=5, description="Score on 0-5 scale")
    max_score: int = 5
    questions: List[QuestionScore]


class ScoringSummary(BaseSchema):
    """Summary statistics for the assessment."""
    
    total_questions: int
    questions_answered: int
    strongest_domain: str
    weakest_domain: str


class ScoringResult(BaseSchema):
    """Complete scoring result."""
    
    overall_score: float = Field(..., ge=0, le=100, description="Score on 0-100 scale")
    max_score: int = 100
    maturity_level: int = Field(..., ge=1, le=5)
    maturity_name: str
    maturity_description: str
    domains: List[DomainScore]
    summary: ScoringSummary


class Recommendation(BaseSchema):
    """A single recommendation."""
    
    priority: int
    domain: str
    domain_id: str
    question_id: str
    finding: str
    current_answer: Optional[Any]
    points_gap: float
    impact: str = Field(..., pattern="^(high|medium|low)$")


class RecommendationsResponse(BaseSchema):
    """Response containing recommendations."""
    
    recommendations: List[Recommendation]
    total_count: int


class ValidationResult(BaseSchema):
    """Validation result for answers."""
    
    valid: bool
    errors: List[str]
    warnings: List[str]
    questions_expected: int
    questions_provided: int
