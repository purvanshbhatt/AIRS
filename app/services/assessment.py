"""
Assessment service - business logic for assessments, answers, scoring, and findings.

All operations are scoped by owner_uid for tenant isolation.
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.assessment import Assessment, AssessmentStatus
from app.models.answer import Answer
from app.models.score import Score
from app.models.finding import Finding, Severity
from app.models.organization import Organization
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    AnswerInput,
    FindingCreate,
)
from app.services.scoring import calculate_scores, get_recommendations
from app.core.rubric import get_rubric, get_question
from app.services.ai_narrative import generate_narrative

logger = logging.getLogger("airs.assessment")


def get_severity_value(severity: Union[Severity, str]) -> str:
    """
    Get severity value as a string, handling both Enum and string types.
    
    This handles the schema mismatch where:
    - Model uses SQLEnum(Severity) 
    - Migration uses String(20)
    
    SQLAlchemy may return either type depending on database backend.
    """
    if isinstance(severity, str):
        return severity.lower()
    return severity.value.lower() if hasattr(severity, 'value') else str(severity).lower()


def load_baseline_profiles() -> Dict[str, Dict[str, float]]:
    """Load baseline profiles from baselines.json. Returns empty dict if file doesn't exist."""
    baselines_path = Path(__file__).parent.parent / "core" / "baselines.json"
    try:
        if baselines_path.exists():
            with open(baselines_path, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


class AssessmentService:
    """Service for assessment operations with tenant isolation."""
    
    def __init__(self, db: Session, owner_uid: Optional[str] = None):
        """
        Initialize service.
        
        Args:
            db: Database session
            owner_uid: Firebase user UID for tenant isolation. If None, operations
                      will not filter by owner (for backwards compatibility during
                      migration period).
        """
        self.db = db
        self.owner_uid = owner_uid
    
    def _base_query(self):
        """Get base query filtered by owner_uid if set."""
        query = self.db.query(Assessment)
        if self.owner_uid:
            query = query.filter(Assessment.owner_uid == self.owner_uid)
        return query
    
    def _verify_org_ownership(self, org_id: str) -> Organization:
        """Verify the organization exists and belongs to current user."""
        query = self.db.query(Organization).filter(Organization.id == org_id)
        if self.owner_uid:
            query = query.filter(Organization.owner_uid == self.owner_uid)
        org = query.first()
        if not org:
            raise ValueError(f"Organization not found: {org_id}")
        return org
    
    def create(self, data: AssessmentCreate) -> Assessment:
        """Create a new assessment owned by the current user."""
        # Verify organization exists AND belongs to current user
        org = self._verify_org_ownership(data.organization_id)
        
        assessment = Assessment(
            organization_id=data.organization_id,
            owner_uid=self.owner_uid,  # Set owner for tenant isolation
            title=data.title or f"Assessment for {org.name}",
            version=data.version or "1.0.0",
            status=AssessmentStatus.DRAFT
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def get(self, assessment_id: str) -> Optional[Assessment]:
        """Get assessment by ID (scoped to current user)."""
        return self._base_query().filter(Assessment.id == assessment_id).first()
    
    def get_all(self, organization_id: Optional[str] = None, 
                skip: int = 0, limit: int = 100) -> List[Assessment]:
        """Get all assessments (scoped to current user), optionally filtered by organization."""
        query = self._base_query()
        if organization_id:
            query = query.filter(Assessment.organization_id == organization_id)
        return query.order_by(Assessment.created_at.desc()).offset(skip).limit(limit).all()
    
    def update(self, assessment_id: str, data: AssessmentUpdate) -> Optional[Assessment]:
        """Update an assessment (scoped to current user)."""
        assessment = self.get(assessment_id)
        if not assessment:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(assessment, key, value)
        
        self.db.commit()
        self.db.refresh(assessment)
        return assessment
    
    def delete(self, assessment_id: str) -> bool:
        """Delete an assessment (scoped to current user)."""
        assessment = self.get(assessment_id)
        if not assessment:
            return False
        
        self.db.delete(assessment)
        self.db.commit()
        return True
    
    # ----- Answer Management -----
    
    def submit_answers(self, assessment_id: str, answers: List[AnswerInput]) -> List[Answer]:
        """Submit answers for an assessment (scoped to current user)."""
        assessment = self.get(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment not found: {assessment_id}")
        
        # Update status to in_progress if draft
        if assessment.status == AssessmentStatus.DRAFT:
            assessment.status = AssessmentStatus.IN_PROGRESS
        
        saved_answers = []
        for answer_input in answers:
            # Check if answer already exists
            existing = self.db.query(Answer).filter(
                Answer.assessment_id == assessment_id,
                Answer.question_id == answer_input.question_id
            ).first()
            
            if existing:
                # Update existing
                existing.value = answer_input.value
                existing.notes = answer_input.notes
                saved_answers.append(existing)
            else:
                # Create new
                answer = Answer(
                    assessment_id=assessment_id,
                    question_id=answer_input.question_id,
                    value=answer_input.value,
                    notes=answer_input.notes
                )
                self.db.add(answer)
                saved_answers.append(answer)
        
        # Invalidate cached summary when answers change
        assessment.summary_version = (assessment.summary_version or 0) + 1
        assessment.summary_json = None
        assessment.summary_computed_at = None
        
        self.db.commit()
        for answer in saved_answers:
            self.db.refresh(answer)
        
        return saved_answers
    
    def get_answers(self, assessment_id: str) -> List[Answer]:
        """Get all answers for an assessment."""
        return self.db.query(Answer).filter(Answer.assessment_id == assessment_id).all()
    
    def get_answers_dict(self, assessment_id: str) -> Dict[str, Any]:
        """Get answers as a dict for scoring service."""
        answers = self.get_answers(assessment_id)
        return {a.question_id: a.get_typed_value() for a in answers}
    
    # ----- Scoring -----
    
    def compute_score(self, assessment_id: str) -> Dict[str, Any]:
        """Compute and persist scores and findings for an assessment."""
        assessment = self.get(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment not found: {assessment_id}")
        
        # Get answers as dict
        answers_dict = self.get_answers_dict(assessment_id)
        
        # Calculate scores using scoring service
        scoring_result = calculate_scores(answers_dict)
        
        # Clear existing scores and findings
        self.db.query(Score).filter(Score.assessment_id == assessment_id).delete()
        self.db.query(Finding).filter(Finding.assessment_id == assessment_id).delete()
        
        # Save domain scores
        saved_scores = []
        for domain_result in scoring_result["domains"]:
            score = Score(
                assessment_id=assessment_id,
                domain_id=domain_result["domain_id"],
                domain_name=domain_result["domain_name"],
                score=domain_result["score"],
                max_score=domain_result["max_score"],
                weight=domain_result["weight"],
                weighted_score=(domain_result["score"] / 5) * domain_result["weight"],
                raw_points=domain_result["raw_points"],
                max_raw_points=domain_result["max_raw_points"]
            )
            self.db.add(score)
            saved_scores.append(score)
        
        # Generate and save findings from recommendations
        recommendations = get_recommendations(scoring_result)
        saved_findings = []
        for rec in recommendations:
            # Map impact to severity
            severity_map = {
                "high": Severity.HIGH,
                "medium": Severity.MEDIUM,
                "low": Severity.LOW
            }
            
            # Get question details for better finding
            question_info, _ = get_question(rec["question_id"])
            
            finding = Finding(
                assessment_id=assessment_id,
                title=f"Gap: {rec['finding'][:100]}",
                description=rec["finding"],
                severity=severity_map.get(rec["impact"], Severity.MEDIUM),
                domain_id=rec["domain_id"],
                domain_name=rec["domain"],
                question_id=rec["question_id"],
                evidence=f"Current value: {rec['current_answer']}",
                recommendation=self._generate_recommendation(rec),
                priority=str(rec["priority"])
            )
            self.db.add(finding)
            saved_findings.append(finding)
        
        # Update assessment with overall scores
        assessment.overall_score = scoring_result["overall_score"]
        assessment.maturity_level = scoring_result["maturity_level"]
        assessment.maturity_name = scoring_result["maturity_name"]
        assessment.status = AssessmentStatus.COMPLETED
        assessment.completed_at = datetime.utcnow()
        
        # Invalidate cached summary (force recompute on next GET /summary)
        assessment.summary_version = (assessment.summary_version or 0) + 1
        assessment.summary_json = None
        assessment.summary_computed_at = None
        
        self.db.commit()
        
        # Refresh all objects
        for score in saved_scores:
            self.db.refresh(score)
        for finding in saved_findings:
            self.db.refresh(finding)
        self.db.refresh(assessment)
        
        return {
            "assessment_id": assessment_id,
            "overall_score": assessment.overall_score,
            "maturity_level": assessment.maturity_level,
            "maturity_name": assessment.maturity_name,
            "domain_scores": saved_scores,
            "findings_count": len(saved_findings),
            "high_severity_count": sum(1 for f in saved_findings if f.severity == Severity.HIGH)
        }
    
    def _generate_recommendation(self, rec: Dict[str, Any]) -> str:
        """Generate a recommendation based on the gap."""
        question_id = rec["question_id"]
        current = rec["current_answer"]
        
        # Generic recommendations based on domain
        domain_recs = {
            "telemetry_logging": "Implement centralized logging and increase retention to meet compliance requirements.",
            "detection_coverage": "Expand EDR coverage and ensure detection rules are regularly updated.",
            "identity_visibility": "Enforce MFA across all accounts and implement privileged access management.",
            "ir_process": "Develop and test incident response playbooks with regular tabletop exercises.",
            "resilience": "Implement immutable backups and regularly test restoration procedures."
        }
        
        base_rec = domain_recs.get(rec["domain_id"], "Address this gap to improve security posture.")
        
        if current is None or current == "" or current is False:
            return f"This control is not currently implemented. {base_rec}"
        
        return f"Current implementation is partial. {base_rec}"
    
    # ----- Findings -----
    
    def get_findings(self, assessment_id: str) -> List[Finding]:
        """Get all findings for an assessment."""
        return self.db.query(Finding).filter(
            Finding.assessment_id == assessment_id
        ).order_by(Finding.priority).all()
    
    def add_finding(self, assessment_id: str, data: FindingCreate) -> Finding:
        """Add a manual finding."""
        assessment = self.get(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment not found: {assessment_id}")
        
        # Get domain name if domain_id provided
        domain_name = None
        if data.domain_id:
            rubric = get_rubric()
            domain = rubric["domains"].get(data.domain_id)
            if domain:
                domain_name = domain["name"]
        
        finding = Finding(
            assessment_id=assessment_id,
            title=data.title,
            description=data.description,
            severity=Severity(data.severity.value),
            domain_id=data.domain_id,
            domain_name=domain_name,
            question_id=data.question_id,
            evidence=data.evidence,
            recommendation=data.recommendation
        )
        self.db.add(finding)
        self.db.commit()
        self.db.refresh(finding)
        return finding
    
    # ----- Detail View -----
    
    def get_detail(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get assessment with all related data."""
        assessment = self.get(assessment_id)
        if not assessment:
            return None
        
        org = self.db.query(Organization).filter(
            Organization.id == assessment.organization_id
        ).first()
        
        return {
            "id": assessment.id,
            "organization_id": assessment.organization_id,
            "organization_name": org.name if org else None,
            "title": assessment.title,
            "version": assessment.version,
            "status": assessment.status,
            "overall_score": assessment.overall_score,
            "maturity_level": assessment.maturity_level,
            "maturity_name": assessment.maturity_name,
            "created_at": assessment.created_at,
            "updated_at": assessment.updated_at,
            "completed_at": assessment.completed_at,
            "answers": assessment.answers,
            "scores": assessment.scores,
            "findings": assessment.findings
        }

    # ----- Summary View -----
    
    def get_summary(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive summary for executive dashboard.
        
        Uses cached summary if available and valid. Cache is invalidated when:
        - Answers are submitted (submit_answers)
        - Scoring is run (compute_score)
        
        LLM narratives are cached separately and only regenerated when
        assessment version changes.
        """
        start_time = time.perf_counter()
        
        assessment = self.get(assessment_id)
        if not assessment:
            return None
        
        # Check if we have a valid cached summary
        if assessment.summary_json and assessment.summary_computed_at:
            cache_age_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Summary cache HIT for {assessment_id[:8]} (computed at {assessment.summary_computed_at})")
            try:
                cached = json.loads(assessment.summary_json)
                # Update LLM metadata (may change between requests based on config)
                cached.update(self._get_llm_metadata())
                logger.info(f"Summary returned from cache in {cache_age_ms:.1f}ms")
                return cached
            except json.JSONDecodeError:
                logger.warning(f"Invalid cached summary JSON for {assessment_id[:8]}, recomputing")
        
        logger.info(f"Summary cache MISS for {assessment_id[:8]}, computing fresh summary")
        
        # Compute fresh summary
        summary = self._compute_summary(assessment)
        
        # Cache the computed summary (without LLM metadata which can change)
        cache_payload = {k: v for k, v in summary.items() if k not in ('llm_enabled', 'llm_provider', 'llm_model', 'llm_mode')}
        try:
            assessment.summary_json = json.dumps(cache_payload, default=str)
            assessment.summary_computed_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Summary cached for {assessment_id[:8]}")
        except Exception as e:
            logger.warning(f"Failed to cache summary for {assessment_id[:8]}: {e}")
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Summary computed and cached in {elapsed_ms:.1f}ms")
        
        return summary
    
    def _compute_summary(self, assessment: Assessment) -> Dict[str, Any]:
        """Compute comprehensive summary for executive dashboard (internal)."""
        org = self.db.query(Organization).filter(
            Organization.id == assessment.organization_id
        ).first()
        
        # Get overall score (default to 0 if not scored yet)
        overall_score = assessment.overall_score or 0
        
        # Determine readiness tier
        tier = self._get_readiness_tier(overall_score)
        
        # Build domain scores with 0-5 scale
        domain_scores = []
        for score in assessment.scores:
            # score.score is already on 0-5 scale from scoring service
            domain_scores.append({
                "domain_id": score.domain_id,
                "domain_name": score.domain_name,
                "score": score.score * 20,  # Convert to percentage for compatibility
                "score_5": score.score,  # Original 0-5 scale
                "weight": score.weight,
                "earned_points": score.raw_points,
                "max_points": score.max_raw_points
            })
        
        # Build findings list sorted by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(
            assessment.findings,
            key=lambda f: severity_order.get(get_severity_value(f.severity), 4)
        )
        
        findings = []
        for f in sorted_findings:
            findings.append({
                "id": f.id,
                "title": f.title,
                "severity": get_severity_value(f.severity),
                "domain": f.domain_name,
                "evidence": f.evidence,
                "recommendation": f.recommendation,
                "description": f.description
            })
        
        # Count critical + high
        critical_high_count = sum(
            1 for f in assessment.findings 
            if get_severity_value(f.severity) in ("critical", "high")
        )
        
        # Build 30/60/90 day roadmap
        roadmap = self._build_roadmap(sorted_findings)
        
        # Generate framework mapping, analytics, and detailed roadmap
        framework_mapping = self._build_framework_mapping(sorted_findings)
        analytics = self._build_analytics(sorted_findings)
        detailed_roadmap = self._build_detailed_roadmap(sorted_findings)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            tier=tier,
            overall_score=overall_score,
            findings=sorted_findings[:3],
            org_name=org.name if org else "the organization"
        )
        
        # Load baseline profiles
        baseline_profiles = load_baseline_profiles()
        baselines_available = list(baseline_profiles.keys())
        
        # Build summary payload for AI narrative generation
        narrative_payload = {
            "overall_score": overall_score,
            "tier": tier,
            "domain_scores": domain_scores,
            "findings": findings[:5],  # Top 5 findings for narrative
            "organization_name": org.name if org else "the organization",
            "baseline_profiles": baseline_profiles,
        }
        
        # Get narratives (cached or fresh)
        narratives = self._get_or_generate_narratives(assessment, narrative_payload)
        
        # Build LLM metadata (informational only - does NOT affect scoring)
        llm_metadata = self._get_llm_metadata()
        
        return {
            "api_version": "1.0",
            "id": assessment.id,
            "title": assessment.title,
            "organization_id": assessment.organization_id,
            "organization_name": org.name if org else None,
            "created_at": assessment.created_at,
            "completed_at": assessment.completed_at,
            "status": assessment.status.value,
            "overall_score": overall_score,
            "tier": tier,
            "domain_scores": domain_scores,
            "findings": findings,
            "findings_count": len(findings),
            "critical_high_count": critical_high_count,
            "roadmap": roadmap,
            "detailed_roadmap": detailed_roadmap,
            "framework_mapping": framework_mapping,
            "analytics": analytics,
            "executive_summary": executive_summary,
            "executive_summary_text": narratives.get("executive_summary_text"),
            "roadmap_narrative_text": narratives.get("roadmap_narrative_text"),
            "baselines_available": baselines_available,
            "baseline_profiles": baseline_profiles,
            # LLM metadata (informational only)
            "llm_enabled": llm_metadata["llm_enabled"],
            "llm_provider": llm_metadata["llm_provider"],
            "llm_model": llm_metadata["llm_model"],
            "llm_mode": llm_metadata["llm_mode"],
            # LLM narrative status: "ready" | "pending" | "disabled"
            "llm_status": narratives.get("llm_status", "disabled"),
        }
    
    def _get_llm_metadata(self) -> Dict[str, Any]:
        """
        Get LLM configuration metadata (informational only).
        
        This metadata indicates the current LLM status for the frontend.
        It does NOT affect scoring, findings, or any assessment data.
        """
        from app.core.config import settings
        
        # Determine LLM mode
        if not settings.AIRS_USE_LLM:
            llm_mode = "disabled"
        elif settings.is_demo_mode:
            llm_mode = "demo"
        else:
            llm_mode = "prod"
        
        # Check if LLM is actually enabled (considers demo mode)
        llm_enabled = settings.is_llm_enabled
        
        # Provider and model (only if enabled)
        llm_provider = "google" if llm_enabled else None
        llm_model = settings.LLM_MODEL if llm_enabled else None
        
        return {
            "llm_enabled": llm_enabled,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "llm_mode": llm_mode,
        }
    
    def _get_or_generate_narratives(self, assessment: Assessment, payload: Dict[str, Any], blocking: bool = False) -> Dict[str, Any]:
        """
        Get cached LLM narratives or return pending status.
        
        Non-blocking by default: If narratives aren't cached, returns immediately
        with llm_status="pending" and the caller should trigger background generation.
        
        Args:
            assessment: The assessment to get narratives for
            payload: Data for narrative generation
            blocking: If True, wait for narrative generation (legacy behavior)
        
        Returns:
            Dict with narrative texts and llm_status:
            - llm_status: "ready" | "pending" | "disabled"
            - executive_summary_text: str | None
            - roadmap_narrative_text: str | None
        """
        from app.core.config import settings
        
        # Check if LLM is disabled
        if not settings.is_llm_enabled:
            return {
                "executive_summary_text": None,
                "roadmap_narrative_text": None,
                "llm_status": "disabled",
            }
        
        current_version = assessment.summary_version or 0
        cached_version = assessment.narrative_version or 0
        
        # Check if we have valid cached narratives
        if (assessment.narrative_executive or assessment.narrative_roadmap) and cached_version >= current_version:
            logger.info(f"Narrative cache HIT for {assessment.id[:8]} (version {cached_version})")
            return {
                "executive_summary_text": assessment.narrative_executive,
                "roadmap_narrative_text": assessment.narrative_roadmap,
                "llm_status": "ready",
            }
        
        logger.info(f"Narrative cache MISS for {assessment.id[:8]} (cached v{cached_version}, current v{current_version})")
        
        # Non-blocking mode: return pending status immediately
        if not blocking:
            logger.info(f"Non-blocking mode: returning pending status for {assessment.id[:8]}")
            return {
                "executive_summary_text": None,
                "roadmap_narrative_text": None,
                "llm_status": "pending",
            }
        
        # Blocking mode: generate synchronously (legacy/refresh behavior)
        return self._generate_narratives_sync(assessment, payload)
    
    def _generate_narratives_sync(self, assessment: Assessment, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate narratives synchronously and cache them.
        
        Used for blocking refresh requests.
        """
        current_version = assessment.summary_version or 0
        
        logger.info(f"Generating narratives synchronously for {assessment.id[:8]}")
        start_time = time.perf_counter()
        narratives = generate_narrative(payload)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Narratives generated in {elapsed_ms:.1f}ms")
        
        # Cache the narratives
        try:
            assessment.narrative_executive = narratives.get("executive_summary_text")
            assessment.narrative_roadmap = narratives.get("roadmap_narrative_text")
            assessment.narrative_version = current_version
            assessment.narrative_generated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Narratives cached for {assessment.id[:8]} at version {current_version}")
        except Exception as e:
            logger.warning(f"Failed to cache narratives for {assessment.id[:8]}: {e}")
        
        return {
            "executive_summary_text": narratives.get("executive_summary_text"),
            "roadmap_narrative_text": narratives.get("roadmap_narrative_text"),
            "llm_status": "ready",
        }
    
    def refresh_narratives(self, assessment_id: str) -> Dict[str, Any]:
        """
        Force refresh narratives for an assessment.
        
        Called by POST /assessments/{id}/refresh-narrative endpoint.
        Generates narratives synchronously and returns the result.
        """
        assessment = self.get(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment not found: {assessment_id}")
        
        # Build payload for narrative generation
        org = self.db.query(Organization).filter(
            Organization.id == assessment.organization_id
        ).first()
        
        overall_score = assessment.overall_score or 0
        tier = self._get_readiness_tier(overall_score)
        
        domain_scores = []
        for score in assessment.scores:
            domain_scores.append({
                "domain_id": score.domain_id,
                "domain_name": score.domain_name,
                "score": score.score * 20,
                "score_5": score.score,
                "weight": score.weight,
            })
        
        findings = []
        for f in assessment.findings[:5]:
            findings.append({
                "id": f.id,
                "title": f.title,
                "severity": get_severity_value(f.severity),
                "domain": f.domain_name,
            })
        
        payload = {
            "overall_score": overall_score,
            "tier": tier,
            "domain_scores": domain_scores,
            "findings": findings,
            "organization_name": org.name if org else "the organization",
            "baseline_profiles": load_baseline_profiles(),
        }
        
        # Generate synchronously
        return self._generate_narratives_sync(assessment, payload)
    
    def _get_readiness_tier(self, score: float) -> Dict[str, Any]:
        """Determine readiness tier based on overall score."""
        tiers = [
            {"label": "Critical", "min_score": 0, "max_score": 39, "color": "danger"},
            {"label": "Needs Work", "min_score": 40, "max_score": 59, "color": "warning"},
            {"label": "Good", "min_score": 60, "max_score": 79, "color": "primary"},
            {"label": "Strong", "min_score": 80, "max_score": 100, "color": "success"},
        ]
        for tier in tiers:
            if tier["min_score"] <= score <= tier["max_score"]:
                return tier
        return tiers[0]  # Default to Critical if score is out of range
    
    def _build_roadmap(self, sorted_findings: List[Finding]) -> Dict[str, List[Dict]]:
        """Build 30/60/90 day roadmap from findings by severity."""
        roadmap = {"day30": [], "day60": [], "day90": []}
        
        critical = [f for f in sorted_findings if get_severity_value(f.severity) == "critical"]
        high = [f for f in sorted_findings if get_severity_value(f.severity) == "high"]
        medium = [f for f in sorted_findings if get_severity_value(f.severity) == "medium"]
        low = [f for f in sorted_findings if get_severity_value(f.severity) == "low"]
        
        # 30-day: Critical findings (up to 3)
        for f in critical[:3]:
            roadmap["day30"].append({
                "title": f.title,
                "action": f.recommendation or "Address immediately",
                "severity": get_severity_value(f.severity),
                "domain": f.domain_name
            })
        
        # 60-day: High findings (up to 3)
        for f in high[:3]:
            roadmap["day60"].append({
                "title": f.title,
                "action": f.recommendation or "Remediate within 60 days",
                "severity": get_severity_value(f.severity),
                "domain": f.domain_name
            })
        
        # 90-day: Medium and Low (up to 3 total)
        remaining = (medium + low)[:3]
        for f in remaining:
            roadmap["day90"].append({
                "title": f.title,
                "action": f.recommendation or "Plan for remediation",
                "severity": get_severity_value(f.severity),
                "domain": f.domain_name
            })
        
        return roadmap
    
    def _build_framework_mapping(self, findings: List[Finding]) -> Dict[str, Any]:
        """Build framework mapping data (MITRE ATT&CK, CIS Controls, OWASP)."""
        from app.core.frameworks import (
            get_all_framework_refs,
            get_technique_coverage,
            get_cis_coverage_summary,
            MITRE_TECHNIQUES,
            TOTAL_MITRE_TECHNIQUES,
            CIS_CONTROLS,
            OWASP_REFS,
        )
        
        mapped_findings = []
        # Track unique refs across all findings for accurate counts
        all_mitre_ids = set()
        all_cis_ids = set()
        all_owasp_ids = set()
        
        for f in findings:
            refs = get_all_framework_refs(f.question_id) if f.question_id else {}
            
            # Collect unique IDs
            for m in refs.get("mitre", []):
                all_mitre_ids.add(m["id"])
            for c in refs.get("cis", []):
                all_cis_ids.add(c["id"])
            for o in refs.get("owasp", []):
                all_owasp_ids.add(o["id"])
            
            mapped_findings.append({
                "finding_id": f.id,
                "title": f.title,
                "severity": get_severity_value(f.severity),
                "domain": f.domain_name,
                "mitre_refs": refs.get("mitre", []),
                "cis_refs": refs.get("cis", []),
                "owasp_refs": refs.get("owasp", []),
                "impact_score": 5,  # Default impact score
            })
        
        # Build coverage stats based on findings (gaps indicate missing controls)
        question_ids = [f.question_id for f in findings if f.question_id]
        
        # Simple coverage calculation
        mitre_coverage = get_technique_coverage(question_ids) if question_ids else {}
        cis_coverage = get_cis_coverage_summary(question_ids) if question_ids else {}
        
        # Get top techniques/controls for display
        mitre_ref_list = sorted(all_mitre_ids)[:10]  # Top 10
        cis_ref_list = sorted(all_cis_ids)[:10]
        owasp_ref_list = sorted(all_owasp_ids)[:10]
        
        return {
            "findings": mapped_findings,
            "coverage": {
                # MITRE ATT&CK
                "mitre_techniques_referenced": len(all_mitre_ids),
                "mitre_techniques_total": TOTAL_MITRE_TECHNIQUES,
                "mitre_coverage_pct": (len(all_mitre_ids) / TOTAL_MITRE_TECHNIQUES * 100) if TOTAL_MITRE_TECHNIQUES > 0 else 0,
                "mitre_techniques_referenced_list": mitre_ref_list,
                # CIS Controls
                "cis_controls_referenced": len(all_cis_ids),
                "cis_controls_total": len(CIS_CONTROLS),
                "cis_controls_met": cis_coverage.get("met", 0),
                "cis_coverage_pct": cis_coverage.get("coverage_pct", 0.0),
                "cis_controls_referenced_list": cis_ref_list,
                "ig1_coverage_pct": cis_coverage.get("ig1_pct", 0.0),
                "ig2_coverage_pct": cis_coverage.get("ig2_pct", 0.0),
                "ig3_coverage_pct": cis_coverage.get("ig3_pct", 0.0),
                # OWASP
                "owasp_referenced": len(all_owasp_ids),
                "owasp_total": len(OWASP_REFS),
                "owasp_coverage_pct": (len(all_owasp_ids) / len(OWASP_REFS) * 100) if len(OWASP_REFS) > 0 else 0,
                "owasp_referenced_list": owasp_ref_list,
            }
        }
    
    def _build_analytics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Build derived analytics (attack paths, gaps)."""
        from app.services.analytics import get_full_analytics
        from app.services.findings import Finding as FindingData, Severity as FindingSeverity, get_rule_id_for_question
        
        # Convert DB findings to service findings format
        finding_data = []
        for f in findings:
            # Map DB Severity to service Severity
            severity_map = {
                "critical": FindingSeverity.CRITICAL,
                "high": FindingSeverity.HIGH,
                "medium": FindingSeverity.MEDIUM,
                "low": FindingSeverity.LOW,
                "info": FindingSeverity.INFO,
            }
            
            # Map question_id to rule_id if possible, otherwise use question_id
            rule_id = f.question_id or f.id
            if f.question_id:
                mapped_rule_id = get_rule_id_for_question(f.question_id)
                if mapped_rule_id:
                    rule_id = mapped_rule_id
            
            finding_data.append(FindingData(
                rule_id=rule_id,
                title=f.title,
                severity=severity_map.get(get_severity_value(f.severity), FindingSeverity.MEDIUM),
                domain_id=f.domain_id,
                domain_name=f.domain_name,
                evidence=f.evidence or "",
                recommendation=f.recommendation,
            ))
        
        return get_full_analytics(finding_data)
    
    def get_edit_context(self, assessment_id: str) -> Dict[str, Any]:
        """
        Get assessment context for editing (details + simple answers map).
        """
        assessment = self.get(assessment_id)
        if not assessment:
            return None
            
        answers = self.get_answers(assessment_id)
        
        # Convert list of answers to simplified map {question_id: value}
        answers_map = {}
        for a in answers:
            # Handle type conversion if needed, though schema likely handles it
             answers_map[a.question_id] = a.value_boolean if a.value_boolean is not None else (
                a.value_numeric if a.value_numeric is not None else a.value_text
            )

        return {
            "assessment": {
                "id": assessment.id,
                "title": assessment.title,
                "organization_id": assessment.organization_id,
                "status": assessment.status
            },
            "answers_map": answers_map
        }

    def _build_detailed_roadmap(self, findings: List[Finding]) -> Dict[str, Any]:
        """Build detailed 30/60/90+ day roadmap with milestones."""
        from app.services.roadmap import generate_roadmap
        from app.services.findings import Finding as FindingData, Severity as FindingSeverity
        
        # Convert DB findings to service findings format
        finding_data = []
        for f in findings:
            # Map DB Severity to service Severity
            severity_map = {
                "critical": FindingSeverity.CRITICAL,
                "high": FindingSeverity.HIGH,
                "medium": FindingSeverity.MEDIUM,
                "low": FindingSeverity.LOW,
                "info": FindingSeverity.INFO,
            }
            
            finding_data.append(FindingData(
                rule_id=f.question_id or f.id,
                title=f.title,
                severity=severity_map.get(get_severity_value(f.severity), FindingSeverity.MEDIUM),
                domain_id=f.domain_id,
                domain_name=f.domain_name,
                evidence=f.evidence or "",
                recommendation=f.recommendation,
            ))
        
        return generate_roadmap(finding_data)

    def _generate_executive_summary(
        self, 
        tier: Dict[str, Any], 
        overall_score: float, 
        findings: List[Finding],
        org_name: str
    ) -> str:
        """Generate deterministic executive summary (no LLM)."""
        tier_label = tier["label"]
        score_int = int(round(overall_score))
        
        # Opening based on tier
        openings = {
            "Critical": f"{org_name}'s AI incident readiness posture requires immediate attention.",
            "Needs Work": f"{org_name}'s AI incident readiness posture has significant gaps that should be addressed.",
            "Good": f"{org_name} demonstrates a solid foundation for AI incident readiness.",
            "Strong": f"{org_name} exhibits a mature and comprehensive AI incident readiness posture."
        }
        opening = openings.get(tier_label, openings["Critical"])
        
        # Score context
        score_context = f"With an overall score of {score_int}/100, the organization is rated as '{tier_label}'."
        
        # Top findings summary
        if not findings:
            findings_summary = "No critical gaps were identified during this assessment."
        else:
            finding_titles = [f.title.replace("Gap: ", "") for f in findings[:3]]
            if len(finding_titles) == 1:
                findings_summary = f"The primary area requiring attention is: {finding_titles[0]}."
            elif len(finding_titles) == 2:
                findings_summary = f"Key areas requiring attention include: {finding_titles[0]} and {finding_titles[1]}."
            else:
                findings_summary = f"Key areas requiring attention include: {finding_titles[0]}, {finding_titles[1]}, and {finding_titles[2]}."
        
        # Closing recommendation based on tier
        closings = {
            "Critical": "Immediate executive sponsorship and resource allocation is recommended to address these security gaps before deploying AI systems to production.",
            "Needs Work": "A focused remediation effort over the next 60 days is recommended to strengthen the organization's readiness for AI-related incidents.",
            "Good": "Continued investment in monitoring and process refinement will help maintain and improve the organization's incident response capabilities.",
            "Strong": "The organization should maintain its current practices and consider sharing learnings across teams to sustain this level of readiness."
        }
        closing = closings.get(tier_label, closings["Critical"])
        
        return f"{opening} {score_context} {findings_summary} {closing}"
