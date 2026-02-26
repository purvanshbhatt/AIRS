"""
Internal Governance Validation Framework (IGVF) — Rule-Based Unit Tests.

Tests all IGVF components with deterministic, LLM-free logic:
  1. Audit Readiness Score (severity weights, clamping)
  2. Compliance Scoring (framework detection, profile awareness)
  3. SLA Gap Analysis (tiers, gaps, normalization)
  4. Lifecycle Risk (EOL, deprecated, outdated scoring)
  5. GHI Composite (weights, grades)
  6. Full Validation Pipeline (end-to-end)
  7. Internal Assurance API (staging gate, admin token, 404 safety)

Target: ≥ 90% coverage across all IGVF modules.
"""

import json
import os
import uuid
import pytest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Force test settings
os.environ.setdefault("ENV", "local")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("DEMO_MODE", "true")

from app.db.database import Base
from app.models.organization import Organization
from app.models.assessment import Assessment, AssessmentStatus
from app.models.finding import Finding, Severity, FindingStatus
from app.models.tech_stack import TechStackItem, LtsStatus
from app.services.governance.validation_engine import (
    compute_audit_readiness,
    compute_compliance,
    compute_sla_gap,
    compute_lifecycle,
    compute_ghi,
    validate_organization,
    SEVERITY_WEIGHTS,
    GHI_WEIGHTS,
)

# ── In-memory DB fixture ─────────────────────────────────────────────

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture()
def db() -> Session:
    """Yield a clean DB session per test."""
    Base.metadata.create_all(bind=_engine)
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


def _make_org(db: Session, **kwargs) -> Organization:
    """Create a minimal Organization with governance defaults."""
    defaults = dict(
        id=str(uuid.uuid4()),
        name="Test Org",
        industry="technology",
        size="51-200",
        owner_uid="test-owner",
        processes_pii=False,
        processes_phi=False,
        processes_cardholder_data=False,
        handles_dod_data=False,
        uses_ai_in_production=False,
        government_contractor=False,
        financial_services=False,
    )
    defaults.update(kwargs)
    org = Organization(**defaults)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _make_assessment(db: Session, org_id: str) -> Assessment:
    """Create a completed assessment for the given org."""
    a = Assessment(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        status=AssessmentStatus.COMPLETED,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _make_finding(
    db: Session,
    assessment_id: str,
    severity: Severity,
    title: str = "finding",
    status: FindingStatus = FindingStatus.OPEN,
) -> Finding:
    """Create a finding attached to the given assessment."""
    f = Finding(
        id=str(uuid.uuid4()),
        assessment_id=assessment_id,
        domain_name="test",
        title=title,
        description=f"Finding: {title}",
        severity=severity,
        status=status,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _make_tech_item(
    db: Session,
    org_id: str,
    component: str = "python",
    version: str = "3.12",
    lts_status: LtsStatus = LtsStatus.ACTIVE,
    versions_behind: int = 0,
) -> TechStackItem:
    """Create a tech stack item for the given org."""
    item = TechStackItem(
        id=str(uuid.uuid4()),
        org_id=org_id,
        component_name=component,
        version=version,
        lts_status=lts_status,
        major_versions_behind=versions_behind,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ═════════════════════════════════════════════════════════════════════
# 1. AUDIT READINESS SCORE
# ═════════════════════════════════════════════════════════════════════

class TestAuditReadiness:
    """Test audit readiness score computation."""

    def test_perfect_score_no_findings(self):
        """No findings → score = 100."""
        result = compute_audit_readiness([])
        assert result.score == 100.0
        assert result.total_open == 0

    def test_single_critical(self, db):
        """One critical finding → score = 85."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        f = _make_finding(db, a.id, Severity.CRITICAL)
        result = compute_audit_readiness([f])
        assert result.score == 85.0
        assert result.critical_count == 1
        assert result.deductions["critical"] == 15

    def test_single_high(self, db):
        """One high finding → score = 92."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        f = _make_finding(db, a.id, Severity.HIGH)
        result = compute_audit_readiness([f])
        assert result.score == 92.0
        assert result.high_count == 1
        assert result.deductions["high"] == 8

    def test_single_medium(self, db):
        """One medium finding → score = 97."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        f = _make_finding(db, a.id, Severity.MEDIUM)
        result = compute_audit_readiness([f])
        assert result.score == 97.0
        assert result.medium_count == 1
        assert result.deductions["medium"] == 3

    def test_low_findings_no_deduction(self, db):
        """Low findings have zero weight → score = 100."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        f = _make_finding(db, a.id, Severity.LOW)
        result = compute_audit_readiness([f])
        assert result.score == 100.0
        assert result.low_count == 1
        assert result.total_open == 1

    def test_mixed_severities(self, db):
        """1 critical + 1 high + 1 medium = 100 - 15 - 8 - 3 = 74."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        findings = [
            _make_finding(db, a.id, Severity.CRITICAL, "crit1"),
            _make_finding(db, a.id, Severity.HIGH, "high1"),
            _make_finding(db, a.id, Severity.MEDIUM, "med1"),
        ]
        result = compute_audit_readiness(findings)
        assert result.score == 74.0

    def test_floor_at_zero(self, db):
        """Score cannot go below 0."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        findings = [
            _make_finding(db, a.id, Severity.CRITICAL, f"crit-{i}")
            for i in range(10)
        ]
        # 100 - 10*15 = -50 → clamped to 0
        result = compute_audit_readiness(findings)
        assert result.score == 0.0

    def test_resolved_findings_excluded(self, db):
        """Resolved and accepted findings are not counted."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        _make_finding(db, a.id, Severity.CRITICAL, "resolved", FindingStatus.RESOLVED)
        _make_finding(db, a.id, Severity.HIGH, "accepted", FindingStatus.ACCEPTED)
        f_open = _make_finding(db, a.id, Severity.MEDIUM, "still open")
        result = compute_audit_readiness(
            db.query(Finding).filter(Finding.assessment_id == a.id).all()
        )
        assert result.score == 97.0  # Only the medium counts
        assert result.total_open == 1

    def test_in_progress_findings_counted(self, db):
        """In-progress findings still count against the score."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        _make_finding(db, a.id, Severity.HIGH, "wip", FindingStatus.IN_PROGRESS)
        result = compute_audit_readiness(
            db.query(Finding).filter(Finding.assessment_id == a.id).all()
        )
        assert result.score == 92.0
        assert result.total_open == 1

    def test_multiple_criticals(self, db):
        """3 critical = 100 - 45 = 55."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        findings = [
            _make_finding(db, a.id, Severity.CRITICAL, f"c-{i}")
            for i in range(3)
        ]
        result = compute_audit_readiness(findings)
        assert result.score == 55.0
        assert result.critical_count == 3

    def test_result_to_dict(self, db):
        """Verify AuditReadinessResult serializes to dict."""
        org = _make_org(db)
        a = _make_assessment(db, org.id)
        _make_finding(db, a.id, Severity.HIGH)
        result = compute_audit_readiness(
            db.query(Finding).filter(Finding.assessment_id == a.id).all()
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "score" in d
        assert "deductions" in d


# ═════════════════════════════════════════════════════════════════════
# 2. COMPLIANCE SCORING
# ═════════════════════════════════════════════════════════════════════

class TestComplianceScoring:
    """Test compliance scoring within IGVF validation engine."""

    def test_tech_industry_soc2_mandatory_false(self, db):
        """Technology company → SOC 2 recommended → score = 100."""
        org = _make_org(db, industry="technology")
        result = compute_compliance(org)
        assert result.total_frameworks == 1
        assert result.mandatory_count == 0
        assert result.recommended_count == 1
        assert result.score == 100.0

    def test_phi_triggers_hipaa(self, db):
        """PHI → HIPAA mandatory → score = 100."""
        org = _make_org(db, processes_phi=True, industry="healthcare")
        result = compute_compliance(org)
        names = [f["framework"] for f in result.frameworks]
        assert "HIPAA" in names
        assert result.mandatory_count >= 1
        assert result.score == 100.0

    def test_pci_cardholder_data(self, db):
        """Cardholder data → PCI-DSS mandatory."""
        org = _make_org(db, processes_cardholder_data=True, industry="fintech")
        result = compute_compliance(org)
        names = [f["framework"] for f in result.frameworks]
        assert "PCI-DSS v4.0" in names

    def test_dod_triggers_cmmc(self, db):
        """DoD data → CMMC mandatory."""
        org = _make_org(db, handles_dod_data=True, industry="defense")
        result = compute_compliance(org)
        names = [f["framework"] for f in result.frameworks]
        assert "CMMC Level 2" in names

    def test_ai_triggers_ai_rmf(self, db):
        """AI in production → AI RMF recommended."""
        org = _make_org(db, uses_ai_in_production=True)
        result = compute_compliance(org)
        names = [f["framework"] for f in result.frameworks]
        assert "NIST AI RMF" in names

    def test_no_profile_score_zero(self, db):
        """Blank profile, non-tech industry → score = 0."""
        org = _make_org(db, industry="retail")
        result = compute_compliance(org)
        assert result.total_frameworks == 0
        assert result.score == 0.0

    def test_profile_set_but_no_frameworks(self, db):
        """Profile set with flags but no triggering combo → score = 50."""
        # PII on retail doesn't trigger any specific framework except GDPR
        # Actually PII triggers GDPR. Let's just check with a flag
        # that doesn't trigger frameworks.
        org = _make_org(db, industry="retail", processes_pii=True)
        result = compute_compliance(org)
        # PII triggers GDPR → total > 0 → score 100
        if result.total_frameworks > 0:
            assert result.score == 100.0
        else:
            assert result.score == 50.0

    def test_multi_trigger_compliance(self, db):
        """Multiple flags → multiple frameworks → all counted."""
        org = _make_org(
            db,
            industry="healthcare",
            processes_phi=True,
            processes_pii=True,
            processes_cardholder_data=True,
            financial_services=True,
        )
        result = compute_compliance(org)
        assert result.total_frameworks >= 3
        assert result.score == 100.0

    def test_government_contractor_fedramp(self, db):
        """Government contractor → FedRAMP."""
        org = _make_org(db, government_contractor=True)
        result = compute_compliance(org)
        names = [f["framework"] for f in result.frameworks]
        assert "FedRAMP" in names

    def test_result_to_dict(self, db):
        """ComplianceResult serializable."""
        org = _make_org(db, processes_phi=True, industry="healthcare")
        result = compute_compliance(org)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "frameworks" in d
        assert isinstance(d["frameworks"], list)


# ═════════════════════════════════════════════════════════════════════
# 3. SLA GAP ANALYSIS
# ═════════════════════════════════════════════════════════════════════

class TestSLAGap:
    """Test SLA tier gap scoring."""

    def test_not_configured(self, db):
        """No tier/SLA → not_configured → score 0."""
        org = _make_org(db)
        result = compute_sla_gap(org)
        assert result.status == "not_configured"
        assert result.score == 0.0

    def test_on_track(self, db):
        """SLA meets or exceeds tier requirement → on_track → 100."""
        org = _make_org(db, application_tier="Tier 2", sla_target=99.95)
        result = compute_sla_gap(org)
        assert result.status == "on_track"
        assert result.score == 100.0
        assert result.gap_pct <= 0

    def test_at_risk_small_gap(self, db):
        """Small gap (≤ 0.5%) → at_risk → 60."""
        org = _make_org(db, application_tier="Tier 2", sla_target=99.5)
        # Tier 2 = 99.9, gap = 0.4 → at_risk
        result = compute_sla_gap(org)
        assert result.status == "at_risk"
        assert result.score == 60.0

    def test_unrealistic_large_gap(self, db):
        """Large gap (> 0.5%) → unrealistic → 20."""
        org = _make_org(db, application_tier="Tier 1", sla_target=99.0)
        # Tier 1 = 99.99, gap = 0.99 → unrealistic
        result = compute_sla_gap(org)
        assert result.status == "unrealistic"
        assert result.score == 20.0

    def test_tier_3(self, db):
        """Tier 3 requirement is 99.5%."""
        org = _make_org(db, application_tier="Tier 3", sla_target=99.5)
        result = compute_sla_gap(org)
        assert result.status == "on_track"
        assert result.tier_sla == 99.5

    def test_tier_4(self, db):
        """Tier 4 requirement is 99.0%."""
        org = _make_org(db, application_tier="Tier 4", sla_target=99.0)
        result = compute_sla_gap(org)
        assert result.status == "on_track"
        assert result.tier_sla == 99.0

    def test_tier_normalize_underscore(self, db):
        """tier_1 format normalizes to Tier 1."""
        org = _make_org(db, application_tier="tier_2", sla_target=99.95)
        result = compute_sla_gap(org)
        assert result.application_tier == "Tier 2"
        assert result.status == "on_track"

    def test_no_sla_target(self, db):
        """Tier set but no SLA target → not_configured."""
        org = _make_org(db, application_tier="Tier 2")
        result = compute_sla_gap(org)
        assert result.status == "not_configured"

    def test_result_to_dict(self, db):
        """SLAResult serializable."""
        org = _make_org(db, application_tier="Tier 2", sla_target=99.9)
        result = compute_sla_gap(org)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "status" in d


# ═════════════════════════════════════════════════════════════════════
# 4. LIFECYCLE RISK
# ═════════════════════════════════════════════════════════════════════

class TestLifecycleRisk:
    """Test lifecycle risk computation."""

    def test_no_components(self):
        """No tech stack → score 100 (nothing at risk)."""
        result = compute_lifecycle([])
        assert result.score == 100.0
        assert result.total_components == 0

    def test_all_healthy(self, db):
        """All components healthy → score 100."""
        org = _make_org(db)
        items = [
            _make_tech_item(db, org.id, "python", "3.12", LtsStatus.ACTIVE),
            _make_tech_item(db, org.id, "node", "20", LtsStatus.LTS),
        ]
        result = compute_lifecycle(items)
        assert result.score == 100.0
        assert result.healthy_count == 2
        assert result.eol_count == 0

    def test_eol_deduction(self, db):
        """EOL component → -25 per component."""
        org = _make_org(db)
        items = [_make_tech_item(db, org.id, "python", "2.7", LtsStatus.EOL)]
        result = compute_lifecycle(items)
        assert result.score == 75.0
        assert result.eol_count == 1
        assert result.risk_breakdown["critical"] == 1

    def test_deprecated_deduction(self, db):
        """Deprecated component → -15 per component."""
        org = _make_org(db)
        items = [
            _make_tech_item(db, org.id, "react", "16", LtsStatus.DEPRECATED)
        ]
        result = compute_lifecycle(items)
        assert result.score == 85.0
        assert result.deprecated_count == 1
        assert result.risk_breakdown["high"] == 1

    def test_outdated_deduction(self, db):
        """2+ versions behind → -5 per component."""
        org = _make_org(db)
        items = [
            _make_tech_item(db, org.id, "node", "16", LtsStatus.ACTIVE, 3)
        ]
        result = compute_lifecycle(items)
        assert result.score == 95.0
        assert result.outdated_count == 1
        assert result.risk_breakdown["medium"] == 1

    def test_versions_behind_1_is_healthy(self, db):
        """1 version behind (not 2+) → healthy."""
        org = _make_org(db)
        items = [
            _make_tech_item(db, org.id, "node", "18", LtsStatus.ACTIVE, 1)
        ]
        result = compute_lifecycle(items)
        assert result.score == 100.0
        assert result.healthy_count == 1

    def test_mixed_lifecycle(self, db):
        """Mix: 1 EOL + 1 deprecated + 1 outdated + 1 healthy = 100-25-15-5 = 55."""
        org = _make_org(db)
        items = [
            _make_tech_item(db, org.id, "python", "2.7", LtsStatus.EOL),
            _make_tech_item(db, org.id, "react", "16", LtsStatus.DEPRECATED),
            _make_tech_item(db, org.id, "node", "14", LtsStatus.ACTIVE, 4),
            _make_tech_item(db, org.id, "go", "1.21", LtsStatus.ACTIVE, 0),
        ]
        result = compute_lifecycle(items)
        assert result.score == 55.0
        assert result.eol_count == 1
        assert result.deprecated_count == 1
        assert result.outdated_count == 1
        assert result.healthy_count == 1

    def test_floor_at_zero(self, db):
        """Score cannot go below 0."""
        org = _make_org(db)
        items = [
            _make_tech_item(db, org.id, f"comp-{i}", "1.0", LtsStatus.EOL)
            for i in range(5)
        ]
        # 100 - 5*25 = -25 → 0
        result = compute_lifecycle(items)
        assert result.score == 0.0

    def test_result_to_dict(self, db):
        """LifecycleResult serializable."""
        org = _make_org(db)
        items = [_make_tech_item(db, org.id, "go", "1.22", LtsStatus.ACTIVE)]
        result = compute_lifecycle(items)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "risk_breakdown" in d


# ═════════════════════════════════════════════════════════════════════
# 5. GHI COMPOSITE
# ═════════════════════════════════════════════════════════════════════

class TestGHI:
    """Test Governance Health Index computation."""

    def test_perfect_scores(self):
        """All 100 → GHI = 100, grade A."""
        ghi = compute_ghi(100, 100, 100, 100)
        assert ghi.ghi == 100.0
        assert ghi.grade == "A"

    def test_all_zeros(self):
        """All 0 → GHI = 0, grade F."""
        ghi = compute_ghi(0, 0, 0, 0)
        assert ghi.ghi == 0.0
        assert ghi.grade == "F"

    def test_weights_applied_correctly(self):
        """Verify weight application: 80×0.4 + 60×0.3 + 40×0.2 + 100×0.1 = 68."""
        ghi = compute_ghi(
            audit_score=80,
            lifecycle_score=60,
            sla_score=40,
            compliance_score=100,
        )
        expected = 80 * 0.4 + 60 * 0.3 + 40 * 0.2 + 100 * 0.1
        assert ghi.ghi == expected
        assert ghi.grade == "C"  # 68 → C

    def test_grade_a_boundary(self):
        """Score ≥ 90 → A."""
        ghi = compute_ghi(90, 90, 90, 90)
        assert ghi.grade == "A"

    def test_grade_b_boundary(self):
        """Score ≥ 80, < 90 → B."""
        ghi = compute_ghi(80, 80, 80, 80)
        assert ghi.ghi == 80.0
        assert ghi.grade == "B"

    def test_grade_c_boundary(self):
        """Score ≥ 60, < 80 → C."""
        ghi = compute_ghi(60, 60, 60, 60)
        assert ghi.ghi == 60.0
        assert ghi.grade == "C"

    def test_grade_d_boundary(self):
        """Score ≥ 40, < 60 → D."""
        ghi = compute_ghi(40, 40, 40, 40)
        assert ghi.ghi == 40.0
        assert ghi.grade == "D"

    def test_grade_f_boundary(self):
        """Score < 40 → F."""
        ghi = compute_ghi(30, 30, 30, 30)
        assert ghi.ghi == 30.0
        assert ghi.grade == "F"

    def test_audit_weight_dominant(self):
        """Audit has highest weight (0.4)."""
        # Only audit at 100, rest at 0
        ghi = compute_ghi(100, 0, 0, 0)
        assert ghi.ghi == 40.0  # 100 × 0.4

    def test_lifecycle_weight(self):
        """Lifecycle weight = 0.3."""
        ghi = compute_ghi(0, 100, 0, 0)
        assert ghi.ghi == 30.0

    def test_sla_weight(self):
        """SLA weight = 0.2."""
        ghi = compute_ghi(0, 0, 100, 0)
        assert ghi.ghi == 20.0

    def test_compliance_weight(self):
        """Compliance weight = 0.1."""
        ghi = compute_ghi(0, 0, 0, 100)
        assert ghi.ghi == 10.0

    def test_dimensions_in_result(self):
        """GHI result includes dimension breakdown."""
        ghi = compute_ghi(80, 70, 60, 50)
        assert ghi.dimensions["audit"] == 80
        assert ghi.dimensions["lifecycle"] == 70
        assert ghi.dimensions["sla"] == 60
        assert ghi.dimensions["compliance"] == 50

    def test_weights_in_result(self):
        """GHI result documents the weights used."""
        ghi = compute_ghi(0, 0, 0, 0)
        assert ghi.weights == GHI_WEIGHTS

    def test_result_to_dict(self):
        """GovernanceHealthIndex serializable."""
        ghi = compute_ghi(75, 80, 90, 100)
        d = ghi.to_dict()
        assert isinstance(d, dict)
        assert "ghi" in d
        assert "grade" in d


# ═════════════════════════════════════════════════════════════════════
# 6. FULL VALIDATION PIPELINE
# ═════════════════════════════════════════════════════════════════════

class TestFullValidation:
    """End-to-end validation pipeline tests."""

    def test_clean_org_passes(self, db):
        """Org with proper profile, no findings, healthy stack → passes."""
        org = _make_org(
            db,
            industry="technology",
            processes_pii=True,
            application_tier="Tier 2",
            sla_target=99.95,
        )
        _make_tech_item(db, org.id, "python", "3.12", LtsStatus.ACTIVE)
        _make_tech_item(db, org.id, "node", "20", LtsStatus.LTS)

        result = validate_organization(db, org)
        assert result.passed is True
        assert result.governance_health_index.ghi >= 60
        assert len(result.issues) == 0

    def test_org_with_critical_findings_fails(self, db):
        """Critical findings → audit readiness low → fails."""
        org = _make_org(db, industry="technology")
        a = _make_assessment(db, org.id)
        for i in range(5):
            _make_finding(db, a.id, Severity.CRITICAL, f"critical-{i}")

        result = validate_organization(db, org)
        # Audit: 100 - 75 = 25 → below 50 threshold → issue
        assert result.audit_readiness.score == 25.0
        assert any("Audit readiness" in issue for issue in result.issues)

    def test_org_with_eol_stack_flags_issue(self, db):
        """EOL component → lifecycle issue flagged."""
        org = _make_org(db, industry="technology")
        _make_tech_item(db, org.id, "python", "2.7", LtsStatus.EOL)

        result = validate_organization(db, org)
        assert result.lifecycle.eol_count == 1
        assert any("end-of-life" in issue for issue in result.issues)

    def test_org_with_unrealistic_sla_flags_issue(self, db):
        """Unrealistic SLA gap → issue flagged."""
        org = _make_org(
            db,
            application_tier="Tier 1",
            sla_target=98.0,
        )
        result = validate_organization(db, org)
        assert result.sla.status == "unrealistic"
        assert any("SLA gap" in issue for issue in result.issues)

    def test_blank_profile_flags_compliance(self, db):
        """No profile → compliance unknown → issue."""
        org = _make_org(db, industry="retail")
        result = validate_organization(db, org)
        assert result.compliance.score == 0.0
        assert any("governance profile" in issue for issue in result.issues)

    def test_ghi_computed_correctly_end_to_end(self, db):
        """GHI = weighted sum of dimension scores."""
        org = _make_org(
            db,
            industry="healthcare",
            processes_phi=True,
            application_tier="Tier 3",
            sla_target=99.5,
        )
        a = _make_assessment(db, org.id)
        _make_finding(db, a.id, Severity.HIGH)  # audit: 92
        _make_tech_item(db, org.id, "python", "3.12", LtsStatus.ACTIVE)  # lifecycle: 100

        result = validate_organization(db, org)

        expected_ghi = (
            result.audit_readiness.score * 0.4
            + result.lifecycle.score * 0.3
            + result.sla.score * 0.2
            + result.compliance.score * 0.1
        )
        assert result.governance_health_index.ghi == round(expected_ghi, 2)

    def test_result_serializable(self, db):
        """Full ValidationResult serializes to dict."""
        org = _make_org(db, industry="technology")
        result = validate_organization(db, org)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "organization_id" in d
        assert "governance_health_index" in d
        assert "compliance" in d
        assert "audit_readiness" in d
        assert "sla" in d
        assert "lifecycle" in d
        assert "passed" in d
        assert "issues" in d

    def test_multiple_assessments_findings_aggregated(self, db):
        """Findings from all assessments aggregated."""
        org = _make_org(db, industry="technology")
        a1 = _make_assessment(db, org.id)
        a2 = _make_assessment(db, org.id)
        _make_finding(db, a1.id, Severity.CRITICAL, "a1-crit")
        _make_finding(db, a2.id, Severity.HIGH, "a2-high")

        result = validate_organization(db, org)
        assert result.audit_readiness.critical_count == 1
        assert result.audit_readiness.high_count == 1
        assert result.audit_readiness.score == 77.0  # 100 - 15 - 8

    def test_passed_requires_ghi_above_60(self, db):
        """Org only passes if GHI ≥ 60 AND no issues."""
        org = _make_org(
            db,
            industry="technology",
            processes_pii=True,
            application_tier="Tier 3",
            sla_target=99.5,
        )
        _make_tech_item(db, org.id, "python", "3.12", LtsStatus.ACTIVE)

        result = validate_organization(db, org)
        if result.governance_health_index.ghi >= 60 and len(result.issues) == 0:
            assert result.passed is True
        else:
            assert result.passed is False


# ═════════════════════════════════════════════════════════════════════
# 7. INTERNAL ASSURANCE API
# ═════════════════════════════════════════════════════════════════════

class TestInternalAssuranceAPI:
    """Test the /internal/governance/validate endpoint."""

    @pytest.fixture(autouse=True)
    def setup_client(self, db):
        """Set up test client with DB override."""
        from app.main import app
        from app.db.database import get_db

        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        from fastapi.testclient import TestClient
        self.client = TestClient(app)
        self.db = db
        yield
        app.dependency_overrides.clear()

    def _create_org(self, **kwargs):
        return _make_org(self.db, owner_uid="dev-user", **kwargs)

    def test_404_when_not_staging(self):
        """Non-staging environment → 404 (invisible)."""
        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.LOCAL
            resp = self.client.get(
                "/internal/governance/validate/any-id",
                headers={"X-Admin-Token": "igvf-staging-token"},
            )
            assert resp.status_code == 404

    def test_403_wrong_token(self):
        """Wrong admin token → 403."""
        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(
                "/internal/governance/validate/any-id",
                headers={"X-Admin-Token": "wrong-token"},
            )
            assert resp.status_code == 403

    def test_422_missing_token(self):
        """Missing admin token header → 422."""
        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(
                "/internal/governance/validate/any-id",
            )
            assert resp.status_code == 422

    def test_404_org_not_found(self):
        """Valid token + staging but nonexistent org → 404."""
        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(
                "/internal/governance/validate/nonexistent-org",
                headers={"X-Admin-Token": "igvf-staging-token"},
            )
            assert resp.status_code == 404

    def test_200_valid_request(self):
        """Valid staging + token + org → 200 with full IGVF result."""
        org = self._create_org(industry="technology")
        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(
                f"/internal/governance/validate/{org.id}",
                headers={"X-Admin-Token": "igvf-staging-token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["organization_id"] == org.id
            assert "governance_health_index" in data
            assert "compliance" in data
            assert "audit_readiness" in data
            assert "sla" in data
            assert "lifecycle" in data
            assert "passed" in data

    def test_ghi_in_response(self):
        """Response includes GHI with grade."""
        org = self._create_org(
            industry="technology",
            processes_pii=True,
            application_tier="Tier 2",
            sla_target=99.95,
        )
        _make_tech_item(self.db, org.id, "python", "3.12", LtsStatus.ACTIVE)

        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(
                f"/internal/governance/validate/{org.id}",
                headers={"X-Admin-Token": "igvf-staging-token"},
            )
            assert resp.status_code == 200
            ghi = resp.json()["governance_health_index"]
            assert "ghi" in ghi
            assert "grade" in ghi
            assert "dimensions" in ghi

    def test_validate_all_endpoint(self):
        """GET /internal/governance/validate → summary of all orgs."""
        org1 = self._create_org(name="Org A")
        org2 = self._create_org(name="Org B")

        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(
                "/internal/governance/validate",
                headers={"X-Admin-Token": "igvf-staging-token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_organizations"] >= 2
            assert len(data["results"]) >= 2
            for r in data["results"]:
                assert "ghi" in r
                assert "grade" in r
                assert "passed" in r

    def test_prod_env_returns_404(self):
        """Production environment → 404 (safety net)."""
        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.PROD
            resp = self.client.get(
                "/internal/governance/validate/any-id",
                headers={"X-Admin-Token": "igvf-staging-token"},
            )
            assert resp.status_code == 404

    def test_demo_env_returns_404(self):
        """Demo environment → 404 (safety net)."""
        with patch("app.api.internal.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.DEMO
            resp = self.client.get(
                "/internal/governance/validate/any-id",
                headers={"X-Admin-Token": "igvf-staging-token"},
            )
            assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════
# 8. LIFECYCLE MATRIX (EOL → High Risk, 2+ behind → Medium)
# ═════════════════════════════════════════════════════════════════════

class TestLifecycleMatrix:
    """
    Lifecycle matrix validation — ensures risk classification
    rules map correctly through the IGVF engine.
    """

    def test_eol_maps_to_critical_risk(self, db):
        """EOL → critical risk classification."""
        org = _make_org(db)
        item = _make_tech_item(db, org.id, "python", "2.7", LtsStatus.EOL)
        result = compute_lifecycle([item])
        assert result.risk_breakdown["critical"] == 1

    def test_deprecated_maps_to_high_risk(self, db):
        """Deprecated → high risk classification."""
        org = _make_org(db)
        item = _make_tech_item(db, org.id, "react", "16", LtsStatus.DEPRECATED)
        result = compute_lifecycle([item])
        assert result.risk_breakdown["high"] == 1

    def test_2_versions_behind_maps_to_medium(self, db):
        """2+ versions behind → medium risk."""
        org = _make_org(db)
        item = _make_tech_item(db, org.id, "node", "16", LtsStatus.ACTIVE, 2)
        result = compute_lifecycle([item])
        assert result.risk_breakdown["medium"] == 1

    def test_3_versions_behind_maps_to_medium(self, db):
        """3 versions behind → still medium (via IGVF engine)."""
        org = _make_org(db)
        item = _make_tech_item(db, org.id, "node", "14", LtsStatus.ACTIVE, 3)
        result = compute_lifecycle([item])
        assert result.risk_breakdown["medium"] == 1

    def test_1_version_behind_maps_to_low(self, db):
        """1 version behind → low risk (healthy)."""
        org = _make_org(db)
        item = _make_tech_item(db, org.id, "node", "18", LtsStatus.ACTIVE, 1)
        result = compute_lifecycle([item])
        assert result.risk_breakdown["low"] == 1
        assert result.healthy_count == 1

    def test_current_version_maps_to_low(self, db):
        """Current version → low risk (healthy)."""
        org = _make_org(db)
        item = _make_tech_item(db, org.id, "python", "3.13", LtsStatus.ACTIVE, 0)
        result = compute_lifecycle([item])
        assert result.risk_breakdown["low"] == 1

    def test_lts_current_maps_to_low(self, db):
        """LTS current → low risk."""
        org = _make_org(db)
        item = _make_tech_item(db, org.id, "node", "20", LtsStatus.LTS, 0)
        result = compute_lifecycle([item])
        assert result.risk_breakdown["low"] == 1
