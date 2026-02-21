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
    # NIST CSF 2.0 mapping fields
    nist_function: Optional[str] = None   # e.g. "DE", "PR", "RC"
    nist_category: Optional[str] = None   # e.g. "DE.CM-1", "PR.AA-5"
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


class DomainScoreSummary(BaseModel):
    """Domain score for summary endpoint."""
    domain_id: str
    domain_name: str
    score: float
    score_5: float  # Score on 0-5 scale
    weight: float
    earned_points: Optional[float] = None
    max_points: Optional[float] = None
    # NIST CSF 2.0 lifecycle mapping
    nist_function: Optional[str] = None        # e.g. "DE"
    nist_function_name: Optional[str] = None   # e.g. "Detect"
    nist_categories: Optional[List[str]] = None


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


class FrameworkRef(BaseModel):
    """Framework reference with ID and name."""
    id: str
    name: str
    url: Optional[str] = None
    ig_level: Optional[int] = None  # For CIS
    tactic: Optional[str] = None    # For MITRE


class FrameworkRefs(BaseModel):
    """Framework references for a finding."""
    mitre: List[FrameworkRef] = []
    cis: List[FrameworkRef] = []
    owasp: List[FrameworkRef] = []


class FindingSummaryWithFramework(BaseModel):
    """Finding with framework references."""
    id: str
    rule_id: Optional[str] = None
    title: str
    severity: str
    domain: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    description: Optional[str] = None
    framework_refs: Optional[Dict[str, List[Dict]]] = None
    # NIST CSF 2.0 mapping
    nist_function: Optional[str] = None   # e.g. "DE"
    nist_category: Optional[str] = None   # e.g. "DE.CM-1"
    # Remediation timeline tier (Immediate / Near-term / Strategic)
    remediation_timeline: Optional[str] = None
    # Effort vs Impact for prioritisation
    effort: Optional[str] = None   # low | medium | high
    impact: Optional[str] = None   # low | medium | high


class FrameworkMappedFinding(BaseModel):
    """Finding for framework mapping display."""
    finding_id: str
    title: str
    severity: str
    mitre_refs: List[FrameworkRef] = []
    cis_refs: List[FrameworkRef] = []
    owasp_refs: List[FrameworkRef] = []


class FrameworkCoverage(BaseModel):
    """Coverage statistics across frameworks."""
    mitre_techniques_total: int
    cis_controls_total: int
    owasp_total: int
    ig1_coverage_pct: Optional[float] = None
    ig2_coverage_pct: Optional[float] = None
    ig3_coverage_pct: Optional[float] = None


class FrameworkMapping(BaseModel):
    """Complete framework mapping with findings and coverage."""
    findings: List[FrameworkMappedFinding] = []
    coverage: Optional[FrameworkCoverage] = None


class AttackStep(BaseModel):
    """Step in an attack path."""
    step: Optional[int] = None
    action: str
    technique_id: Optional[str] = None


class AttackPath(BaseModel):
    """Attack path enabled by missing controls."""
    id: str
    name: str
    description: Optional[str] = None
    risk_level: str
    techniques: List[Dict[str, str]] = []
    steps: List[AttackStep] = []
    enabling_gaps: List[str] = []
    likelihood: Optional[int] = None
    impact: Optional[int] = None


class GapCategory(BaseModel):
    """Gap category with list of gaps."""
    name: str
    category: Optional[str] = None
    gaps: List[str] = []
    gap_count: Optional[int] = None
    severity: Optional[str] = None
    is_critical: Optional[bool] = None
    description: Optional[str] = None
    findings: List[Dict[str, Any]] = []


class GapAnalysis(BaseModel):
    """Gap analysis structure."""
    categories: List[GapCategory] = []
    total_gaps: Optional[int] = None


class RiskSummary(BaseModel):
    """Risk summary with key findings."""
    overall_risk_level: str
    key_risks: List[str] = []
    mitigating_factors: List[str] = []
    attack_paths_enabled: Optional[int] = None
    total_gaps_identified: Optional[int] = None
    severity_counts: Dict[str, int] = {}
    findings_count: Optional[int] = None
    total_risk_score: Optional[int] = None


class AnalyticsSummary(BaseModel):
    """Analytics with attack paths and gap analysis."""
    attack_paths: List[AttackPath] = []
    detection_gaps: Optional[GapAnalysis] = None
    response_gaps: Optional[GapAnalysis] = None
    identity_gaps: Optional[GapAnalysis] = None
    risk_distribution: Dict[str, int] = {}
    risk_summary: Optional[RiskSummary] = None
    top_risks: List[str] = []
    improvement_recommendations: List[str] = []
    # Contract-integrity fields (v2 additions — additive, non-breaking)
    gap_category: Optional[str] = None   # Primary gap category from GapAnalysis
    maturity_tier: Optional[str] = None  # Overall maturity tier label (Initial/Developing/…)


class DetailedRoadmapItem(BaseModel):
    """Detailed roadmap item with full metadata."""
    id: str
    title: str
    action: str
    priority: str
    phase: str
    # Enterprise timeline labels: Immediate | Near-term | Strategic
    timeline_label: Optional[str] = None
    timeline_range: Optional[str] = None
    effort: str
    effort_estimate: Optional[str] = None
    # Risk Reduction Impact: low | medium | high
    risk_impact: Optional[str] = None
    domain: Optional[str] = None
    finding_id: Optional[str] = None
    nist_category: Optional[str] = None
    owner: Optional[str] = None
    dependencies: List[str] = []
    milestones: List[str] = []
    success_criteria: Optional[str] = None
    status: str = "not_started"


class DetailedRoadmapPhase(BaseModel):
    """Roadmap phase with items."""
    title: str
    description: Optional[str] = None
    items: List[DetailedRoadmapItem] = []


class DetailedRoadmapSummary(BaseModel):
    """Summary of roadmap metrics."""
    total_items: int
    day30_count: int
    day60_count: int
    day90_count: int
    by_priority: Dict[str, int] = {}
    by_effort: Dict[str, int] = {}
    generated_at: str


class DetailedRoadmap(BaseModel):
    """Complete detailed roadmap."""
    phases: List[DetailedRoadmapPhase] = []
    summary: Optional[DetailedRoadmapSummary] = None


class AssessmentSummaryResponse(BaseModel):
    """Comprehensive assessment summary for executive dashboard."""
    # API version for forward compatibility
    api_version: str = "1.0"
    product: Dict[str, Optional[str]]
    
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
    
    # Findings with framework refs
    findings: List[FindingSummaryWithFramework]
    findings_count: int
    critical_high_count: int
    
    # Simple roadmap (legacy)
    roadmap: Roadmap
    
    # Executive summary (deterministic, no LLM)
    executive_summary: str
    
    # AI-generated narratives (optional, LLM-powered)
    executive_summary_text: Optional[str] = None
    roadmap_narrative_text: Optional[str] = None
    
    # Baseline profiles for comparison
    baselines_available: List[str] = []
    baseline_profiles: Dict[str, Dict[str, float]] = {}
    
    # Framework mapping with MITRE ATT&CK, CIS, OWASP refs
    framework_mapping: Optional[FrameworkMapping] = None
    
    # Analytics with attack paths and gap analysis
    analytics: Optional[AnalyticsSummary] = None
    
    # Detailed 30/60/90 roadmap with effort and impact
    detailed_roadmap: Optional[DetailedRoadmap] = None
    
    # LLM metadata (informational only - does NOT affect scoring)
    # These fields indicate the current LLM configuration status
    llm_enabled: bool = False
    llm_provider: Optional[str] = None  # e.g., "google", "openai"
    llm_model: Optional[str] = None     # e.g., "gemini-3-flash-preview"
    llm_mode: LLMMode = LLMMode.DISABLED  # "demo" | "prod" | "disabled"
    llm_status: Optional[str] = None       # "pending" | "completed" | "failed"

