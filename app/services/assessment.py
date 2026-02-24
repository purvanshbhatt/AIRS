"""
Assessment service - business logic for assessments, answers, scoring, and findings.

All operations are scoped by owner_uid for tenant isolation.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
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
from app.core.rubric import get_rubric, get_question, get_domain_nist_function, NIST_FUNCTIONS
from app.services.ai_narrative import generate_narrative
from app.services.analytics import generate_analytics
from app.services.roadmap import generate_detailed_roadmap, generate_simple_roadmap
from app.core.frameworks import get_framework_refs, get_all_unique_techniques
from app.core.product import get_product_info


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
            
            # Extract NIST CSF 2.0 mapping from question
            nist_category = question_info.get("nist_category") if question_info else None
            nist_func_info = get_domain_nist_function(rec["domain_id"])
            nist_function = nist_func_info.get("id") if nist_func_info else None
            
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
                priority=str(rec["priority"]),
                nist_category=nist_category,
                nist_function=nist_function
            )
            self.db.add(finding)
            saved_findings.append(finding)
        
        # Update assessment with overall scores
        assessment.overall_score = scoring_result["overall_score"]
        assessment.maturity_level = scoring_result["maturity_level"]
        assessment.maturity_name = scoring_result["maturity_name"]
        assessment.status = AssessmentStatus.COMPLETED
        assessment.completed_at = datetime.utcnow()
        
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
        """Get comprehensive summary for executive dashboard."""
        assessment = self.get(assessment_id)
        if not assessment:
            return None
        
        org = self.db.query(Organization).filter(
            Organization.id == assessment.organization_id
        ).first()
        
        # Get overall score (default to 0 if not scored yet)
        overall_score = assessment.overall_score or 0
        
        # Determine readiness tier
        tier = self._get_readiness_tier(overall_score)
        
        rubric = get_rubric()
        # Build domain scores with 0-5 scale and NIST CSF 2.0 lifecycle mapping
        domain_scores = []
        for score in assessment.scores:
            nist_info = get_domain_nist_function(score.domain_id)
            rubric_domain = rubric["domains"].get(score.domain_id, {})
            domain_scores.append({
                "domain_id": score.domain_id,
                "domain_name": score.domain_name,
                "score": score.score * 20,  # Convert to percentage for compatibility
                "score_5": score.score,  # Original 0-5 scale
                "weight": score.weight,
                "earned_points": score.raw_points,
                "max_points": score.max_raw_points,
                # NIST CSF 2.0 lifecycle function
                "nist_function": nist_info.get("id"),
                "nist_function_name": nist_info.get("name"),
                "nist_categories": rubric_domain.get("nist_categories", []),
            })
        
        # Build findings list sorted by severity with framework refs
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(
            assessment.findings,
            key=lambda f: severity_order.get(f.severity.value.lower(), 4)
        )
        
        findings = []
        finding_rule_ids = []
        for f in sorted_findings:
            # Get framework refs for this finding
            fw_refs = get_framework_refs(f.domain_id or "")
            # Try rule_id from description/title pattern
            rule_id = None
            if f.title and f.title.startswith("Gap: "):
                # Try to extract rule from related question
                pass
            # Use question_id to infer rule mapping
            rule_id = self._infer_rule_id(f)
            if rule_id:
                fw_refs = get_framework_refs(rule_id)
                finding_rule_ids.append(rule_id)
            
            findings.append({
                "id": f.id,
                "rule_id": rule_id,
                "title": f.title,
                "severity": f.severity.value,
                "domain": f.domain_name,
                "evidence": f.evidence,
                "recommendation": f.recommendation,
                "description": f.description,
                "framework_refs": fw_refs,
                # NIST CSF 2.0 mapping — from DB column (if populated) else domain fallback
                "nist_function": getattr(f, "nist_function", None),
                "nist_category": getattr(f, "nist_category", None),
            })
        
        # Count critical + high
        critical_high_count = sum(
            1 for f in assessment.findings 
            if f.severity.value.lower() in ("critical", "high")
        )
        
        # Build 30/60/90 day roadmap
        roadmap = self._build_roadmap(sorted_findings)
        
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
        
        # Generate AI narratives (uses fallback if LLM disabled)
        narratives = generate_narrative(narrative_payload)
        
        # Build LLM metadata (informational only - does NOT affect scoring)
        llm_metadata = self._get_llm_metadata()
        llm_status = None
        if llm_metadata["llm_enabled"]:
            llm_status = "completed" if narratives.get("llm_generated") else "failed"
        
        # Generate framework mapping with coverage stats
        coverage_stats = get_all_unique_techniques(finding_rule_ids)
        
        # Count unique NIST CSF 2.0 categories from findings
        unique_nist_categories = set()
        for f in findings:
            nist_cat = f.get("nist_category")
            if nist_cat:
                unique_nist_categories.add(nist_cat)
        
        framework_mapping = {
            "findings": [
                {
                    "finding_id": f["id"],
                    "title": f["title"],
                    "severity": f["severity"],
                    "mitre_refs": f["framework_refs"].get("mitre", []),
                    "cis_refs": f["framework_refs"].get("cis", []),
                    "owasp_refs": f["framework_refs"].get("owasp", [])
                }
                for f in findings
            ],
            "coverage": {
                "mitre_techniques_total": coverage_stats["mitre_techniques_total"],
                "cis_controls_total": coverage_stats["cis_controls_total"],
                "owasp_total": coverage_stats["owasp_total"],
                "ig1_coverage_pct": coverage_stats["ig1_coverage_pct"],
                "ig2_coverage_pct": coverage_stats["ig2_coverage_pct"],
                "ig3_coverage_pct": coverage_stats["ig3_coverage_pct"],
                "nist_csf_categories": len(unique_nist_categories)
            }
        }
        
        # Generate analytics (attack paths, gaps)
        analytics = generate_analytics(finding_rule_ids)
        
        # Generate detailed roadmap
        finding_dicts = [
            {
                "rule_id": f.get("rule_id"),
                "title": f["title"],
                "severity": f["severity"],
                "domain_name": f["domain"],
                "recommendation": f["recommendation"],
                "remediation_effort": "medium"  # Default, could be enhanced
            }
            for f in findings
        ]
        detailed_roadmap = generate_detailed_roadmap(finding_dicts)
        
        # Derive maturity_tier from overall_score for contract integrity
        maturity_levels = get_rubric()["maturity_levels"]
        maturity_tier = "Initial"
        for range_key, level_info in maturity_levels.items():
            low, high = map(int, range_key.split("-"))
            if low <= overall_score <= high:
                maturity_tier = level_info["name"]
                break

        # Enrich analytics with gap_category and maturity_tier
        if analytics and isinstance(analytics, dict):
            # Primary gap category: the most severe gap namespace
            top_gap = None
            for gc in (analytics.get("detection_gaps") or {}).get("categories", []):
                if gc.get("is_critical"):
                    top_gap = gc.get("name")
                    break
            if top_gap is None and analytics.get("detection_gaps"):
                cats = analytics["detection_gaps"].get("categories", [])
                top_gap = cats[0].get("name") if cats else None
            analytics["gap_category"] = top_gap
            analytics["maturity_tier"] = maturity_tier

        return {
            "api_version": "1.0",
            "product": get_product_info(),
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
            "executive_summary": executive_summary,
            "executive_summary_text": narratives.get("executive_summary_text"),
            "roadmap_narrative_text": narratives.get("roadmap_narrative_text"),
            "baselines_available": baselines_available,
            "baseline_profiles": baseline_profiles,
            # New: Framework mapping with MITRE, CIS, OWASP refs
            "framework_mapping": framework_mapping,
            # New: Analytics with attack paths and gaps (includes gap_category + maturity_tier)
            "analytics": analytics,
            # New: Detailed roadmap with phases
            "detailed_roadmap": detailed_roadmap,
            # LLM metadata (informational only)
            "llm_enabled": llm_metadata["llm_enabled"],
            "llm_provider": llm_metadata["llm_provider"],
            "llm_model": llm_metadata["llm_model"],
            "llm_mode": llm_metadata["llm_mode"],
            "llm_status": llm_status,
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
        llm_provider = settings.LLM_PROVIDER if llm_enabled else None
        llm_model = settings.LLM_MODEL if llm_enabled else None
        
        return {
            "llm_enabled": llm_enabled,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "llm_mode": llm_mode,
        }
    
    def _infer_rule_id(self, finding: Finding) -> Optional[str]:
        """
        Infer the finding rule_id from question_id or domain patterns.
        
        Maps question_id patterns to rule IDs for framework reference lookup.
        Every question_id maps to a rule to ensure framework refs are always populated.
        """
        question_id = finding.question_id
        domain_id = finding.domain_id
        
        # Complete Question ID to Rule ID mapping - all 30 questions covered
        question_rule_map = {
            # Telemetry & Logging (tl_01 - tl_06)
            "tl_01": "TL-006",  # Network device logging
            "tl_02": "TL-003",  # Endpoint logging
            "tl_03": "TL-004",  # Cloud logging
            "tl_04": "TL-002",  # Centralized logging
            "tl_05": "TL-001",  # Log retention
            "tl_06": "TL-005",  # Auth logging
            # Detection Coverage (dc_01 - dc_06)
            "dc_01": "DC-001",  # EDR coverage
            "dc_02": "DC-003",  # Network monitoring
            "dc_03": "DC-004",  # Detection rules
            "dc_04": "DC-007",  # Custom detection rules
            "dc_05": "DC-005",  # Email security
            "dc_06": "DC-006",  # Alert triage
            # Identity Visibility (iv_01 - iv_06)
            "iv_01": "IV-002",  # Org-wide MFA
            "iv_02": "IV-001",  # Admin MFA
            "iv_03": "IV-003",  # Privileged account inventory
            "iv_04": "IV-004",  # Service accounts
            "iv_05": "IV-005",  # PAM
            "iv_06": "IV-006",  # Failed login monitoring
            # IR Playbooks & Process (ir_01 - ir_06)
            "ir_01": "IR-001",  # IR playbooks
            "ir_02": "IR-002",  # Playbook testing
            "ir_03": "IR-004",  # IR team
            "ir_04": "IR-005",  # Communication templates
            "ir_05": "IR-006",  # Escalation matrix
            "ir_06": "IR-003",  # Tabletop exercises
            # Resilience (rs_01 - rs_06)
            "rs_01": "RS-003",  # Critical backups
            "rs_02": "RS-002",  # Immutable backups
            "rs_03": "RS-001",  # Backup testing
            "rs_04": "RS-005",  # DR plan
            "rs_05": "RS-004",  # RTO
            "rs_06": "RS-006",  # Backup credentials
        }
        
        if question_id and question_id in question_rule_map:
            return question_rule_map[question_id]
        
        # Fallback: map by domain for any unmapped questions
        domain_default_map = {
            "telemetry_logging": "TL-001",
            "detection_coverage": "DC-001",
            "identity_visibility": "IV-001",
            "ir_process": "IR-001",
            "resilience": "RS-001"
        }
        
        if domain_id and domain_id in domain_default_map:
            return domain_default_map[domain_id]
        
        return None
    
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
        
        critical = [f for f in sorted_findings if f.severity.value.lower() == "critical"]
        high = [f for f in sorted_findings if f.severity.value.lower() == "high"]
        medium = [f for f in sorted_findings if f.severity.value.lower() == "medium"]
        low = [f for f in sorted_findings if f.severity.value.lower() == "low"]
        
        # 30-day: Critical findings (up to 3)
        for f in critical[:3]:
            roadmap["day30"].append({
                "title": f.title,
                "action": f.recommendation or "Address immediately",
                "severity": f.severity.value,
                "domain": f.domain_name
            })
        
        # 60-day: High findings (up to 3)
        for f in high[:3]:
            roadmap["day60"].append({
                "title": f.title,
                "action": f.recommendation or "Remediate within 60 days",
                "severity": f.severity.value,
                "domain": f.domain_name
            })
        
        # 90-day: Medium and Low (up to 3 total)
        remaining = (medium + low)[:3]
        for f in remaining:
            roadmap["day90"].append({
                "title": f.title,
                "action": f.recommendation or "Plan for remediation",
                "severity": f.severity.value,
                "domain": f.domain_name
            })
        
        return roadmap
    
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
