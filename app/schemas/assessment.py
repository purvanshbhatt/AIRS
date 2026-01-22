"""
Pydantic schemas for Assessment, Answer, Score, and Finding.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AssessmentStatus(str, Enum):
    """Assessment status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Severity(str, Enum):
    """Finding severity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, Enum):
    """Finding status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"


class LLMMode(str, Enum):
    """LLM operation mode (informational only, does not affect scoring)."""
    DEMO = "demo"      # Demo mode - LLM enabled for presentations
    PROD = "prod"      # Production mode - LLM with strict validation
    DISABLED = "disabled"  # LLM features disabled


# ----- Answer Schemas -----

class AnswerInput(BaseModel):
    """Single answer input."""
    question_id: str = Field(..., pattern="^[a-z]{2}_\\d{2}$")
    value: str = Field(..., min_length=1)
    notes: Optional[str] = None


class AnswerBulkSubmit(BaseModel):
    """Bulk answer submission."""
    answers: List[AnswerInput]


class AnswerResponse(BaseModel):
    """Answer response."""
    id: str
    question_id: str
    value: str
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ----- Score Schemas -----

class ScoreResponse(BaseModel):
    """Score response."""
    id: str
    domain_id: str
    domain_name: str
    score: float = Field(..., ge=0, le=5)
    max_score: float = 5.0
    weight: float
    weighted_score: float
    raw_points: Optional[float] = None
    max_raw_points: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ----- Finding Schemas -----

class FindingCreate(BaseModel):
    """Finding creation (manual)."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Severity
    domain_id: Optional[str] = None
    question_id: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None


class FindingResponse(BaseModel):
    """Finding response."""
    id: str
    title: str
    description: Optional[str] = None
    severity: Severity
    status: FindingStatus
    domain_id: Optional[str] = None
    domain_name: Optional[str] = None
    question_id: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    priority: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FindingUpdate(BaseModel):
    """Finding update."""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[Severity] = None
    status: Optional[FindingStatus] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None


# ----- Assessment Schemas -----

class AssessmentCreate(BaseModel):
    """Assessment creation."""
    organization_id: str
    title: Optional[str] = None
    version: Optional[str] = "1.0.0"


class AssessmentUpdate(BaseModel):
    """Assessment update."""
    title: Optional[str] = None
    status: Optional[AssessmentStatus] = None


class AssessmentResponse(BaseModel):
    """Assessment response."""
    id: str
    organization_id: str
    title: Optional[str] = None
    version: str
    status: AssessmentStatus
    overall_score: Optional[float] = None
    maturity_level: Optional[int] = None
    maturity_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AssessmentDetail(AssessmentResponse):
    """Assessment with related data."""
    answers: List[AnswerResponse] = []
    scores: List[ScoreResponse] = []
    findings: List[FindingResponse] = []
    organization_name: Optional[str] = None


class AssessmentSummary(BaseModel):
    """Assessment summary for lists."""
    id: str
    organization_id: str
    organization_name: Optional[str] = None
    title: Optional[str] = None
    status: AssessmentStatus
    overall_score: Optional[float] = None
    maturity_level: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ----- Scoring Schemas -----

class ComputeScoreResponse(BaseModel):
    """Response after computing scores."""
    assessment_id: str
    overall_score: float
    maturity_level: int
    maturity_name: str
    domain_scores: List[ScoreResponse]
    findings_count: int
    high_severity_count: int


# ----- Summary Schema -----

class RoadmapItem(BaseModel):
    """Roadmap item for remediation."""
    title: str
    action: str
    severity: str
    domain: Optional[str] = None


class Roadmap(BaseModel):
    """30/60/90 day remediation roadmap."""
    day30: List[RoadmapItem] = []
    day60: List[RoadmapItem] = []
    day90: List[RoadmapItem] = []


# ----- Framework Mapping Schemas -----

class MitreRef(BaseModel):
    """MITRE ATT&CK technique reference."""
    id: str  # e.g., "T1566"
    name: str  # e.g., "Phishing"
    tactic: str  # e.g., "Initial Access"
    url: str


class CISRef(BaseModel):
    """CIS Controls v8 reference."""
    id: str  # e.g., "CIS-4.1"
    name: str  # e.g., "Establish and Maintain a Secure Configuration Process"
    ig_level: int  # Implementation Group: 1, 2, or 3


class OWASPRef(BaseModel):
    """OWASP Top 10 reference."""
    id: str  # e.g., "A01:2021"
    name: str  # e.g., "Broken Access Control"


class FrameworkMappedFinding(BaseModel):
    """Finding with full framework mappings."""
    finding_id: str
    title: str
    severity: str
    domain: str
    mitre_refs: List[MitreRef] = []
    cis_refs: List[CISRef] = []
    owasp_refs: List[OWASPRef] = []
    impact_score: int = 5


class FrameworkCoverage(BaseModel):
    """Framework coverage summary."""
    mitre_techniques_enabled: int
    mitre_techniques_total: int
    mitre_coverage_pct: float
    cis_controls_met: int
    cis_controls_total: int
    cis_coverage_pct: float
    ig1_coverage_pct: float
    ig2_coverage_pct: float
    ig3_coverage_pct: float


class FrameworkMapping(BaseModel):
    """Complete framework mapping for assessment."""
    findings: List[FrameworkMappedFinding] = []
    coverage: Optional[FrameworkCoverage] = None


# ----- Analytics Schemas -----

class AttackPathTechnique(BaseModel):
    """A MITRE technique in an attack path."""
    id: str
    name: str


class AttackPath(BaseModel):
    """An enabled attack path based on missing controls."""
    id: str
    name: str
    description: str
    risk_level: str  # critical, high, medium, low
    entry_point: str
    techniques: List[AttackPathTechnique] = []
    enabling_findings: List[str] = []
    enablement_percentage: int = 0
    impact: str


class GapFinding(BaseModel):
    """A finding within a gap category."""
    rule_id: str
    title: str
    severity: str


class GapCategoryItem(BaseModel):
    """A single gap category with its findings."""
    category: str
    description: str = ""
    gap_count: int = 0
    is_critical: bool = False
    findings: List[GapFinding] = []


class DetectionGaps(BaseModel):
    """Detection capability gaps analysis."""
    total_gaps: int = 0
    critical_categories: int = 0
    categories: List[GapCategoryItem] = []
    coverage_score: float = 100.0


class ResponseGaps(BaseModel):
    """Incident response gaps analysis."""
    total_gaps: int = 0
    critical_categories: int = 0
    categories: List[GapCategoryItem] = []
    readiness_score: float = 100.0


class IdentityGaps(BaseModel):
    """Identity and access management gaps analysis."""
    total_gaps: int = 0
    categories: List[GapCategoryItem] = []


class Analytics(BaseModel):
    """Full analytics for an assessment."""
    attack_paths: List[AttackPath] = []
    detection_gaps: Optional[DetectionGaps] = None
    response_gaps: Optional[ResponseGaps] = None
    identity_gaps: Optional[IdentityGaps] = None
    framework_summary: Optional[Dict[str, Any]] = None
    top_risks: List[str] = []
    recommended_priorities: List[str] = []


# ----- Detailed Roadmap Schemas -----

class DetailedRoadmapItem(BaseModel):
    """Detailed remediation item with milestones."""
    finding_id: str
    title: str
    action: str
    effort: str  # low, medium, high
    severity: str
    domain: str
    owner: str
    milestones: List[str] = []
    success_criteria: str = ""


class RoadmapPhase(BaseModel):
    """A phase of the roadmap (30/60/90 days)."""
    name: str
    description: str
    item_count: int
    effort_hours: int
    risk_reduction: int
    items: List[DetailedRoadmapItem] = []


class DetailedRoadmap(BaseModel):
    """Comprehensive 30/60/90+ day roadmap."""
    summary: Dict[str, Any] = {}
    phases: Dict[str, RoadmapPhase] = {}


class DomainScoreSummary(BaseModel):
    """Domain score for summary endpoint."""
    domain_id: str
    domain_name: str
    score: float
    score_5: float  # Score on 0-5 scale
    weight: float
    earned_points: Optional[float] = None
    max_points: Optional[float] = None


class FindingSummary(BaseModel):
    """Finding for summary endpoint."""
    id: str
    title: str
    severity: str
    domain: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    description: Optional[str] = None


class ReadinessTier(BaseModel):
    """Readiness tier info."""
    label: str  # Critical, Needs Work, Good, Strong
    min_score: int
    max_score: int
    color: str  # danger, warning, primary, success


class AssessmentSummaryResponse(BaseModel):
    """Comprehensive assessment summary for executive dashboard."""
    # API version for forward compatibility
    api_version: str = "1.0"
    
    # Metadata
    id: str
    title: Optional[str] = None
    organization_id: str
    organization_name: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    
    # Scores
    overall_score: float
    tier: ReadinessTier
    domain_scores: List[DomainScoreSummary]
    
    # Findings
    findings: List[FindingSummary]
    findings_count: int
    critical_high_count: int
    
    # Roadmap (basic)
    roadmap: Roadmap
    
    # Detailed roadmap with milestones and effort
    detailed_roadmap: Optional[DetailedRoadmap] = None
    
    # Framework mapping (MITRE/CIS/OWASP)
    framework_mapping: Optional[FrameworkMapping] = None
    
    # Derived analytics (attack paths, gaps)
    analytics: Optional[Analytics] = None
    
    # Executive summary (deterministic, no LLM)
    executive_summary: str
    
    # AI-generated narratives (optional, LLM-powered)
    executive_summary_text: Optional[str] = None
    roadmap_narrative_text: Optional[str] = None
    
    # Baseline profiles for comparison
    baselines_available: List[str] = []
    baseline_profiles: Dict[str, Dict[str, float]] = {}
    
    # LLM metadata (informational only - does NOT affect scoring)
    # These fields indicate the current LLM configuration status
    llm_enabled: bool = False
    llm_provider: Optional[str] = None  # e.g., "google", "openai"
    llm_model: Optional[str] = None     # e.g., "gemini-2.0-flash"
    llm_mode: LLMMode = LLMMode.DISABLED  # "demo" | "prod" | "disabled"
