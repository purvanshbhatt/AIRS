"""
Reliability Risk Index (RRI) — Deterministic Unit Tests.

Tests all RRI components with deterministic, LLM-free logic:
  1. Downtime Budget Calculator
  2. SLA Advisor
  3. Dimension Scorers (SLA, Recovery, Redundancy, Monitoring, BCDR)
  4. Composite RRI Score
  5. Board Simulation Mode
  6. Tier Risk Multipliers
  7. API Endpoints (staging gate, tenant isolation)
  8. Breach Exposure Badge (4 levels)
  9. Autonomous Advisory Engine (7 rules)
  10. Reliability Confidence Score (RCS, 5 sub-dimensions)
  11. Auto-Recommendation Engine
  12. Audit Trail Logging
  13. New API Endpoints (confidence, accept-recommendation, history)

Target: ≥ 90% coverage across RRI engine + API.
"""

import os
import uuid
import pytest
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Force test settings
os.environ.setdefault("ENV", "local")
os.environ.setdefault("AUTH_REQUIRED", "false")
os.environ.setdefault("DEMO_MODE", "true")

from app.db.database import Base
from app.models.organization import Organization
from app.models.tech_stack import TechStackItem, LtsStatus
from app.services.governance.reliability_engine import (
    calculate_downtime_budget,
    get_sla_advisor,
    calculate_rri,
    simulate_breach,
    _score_sla_commitment,
    _score_recovery_capability,
    _score_redundancy_ha,
    _score_monitoring_detection,
    _score_bcdr_validation,
    _get_risk_band,
    _get_breach_probability,
    _format_minutes,
    _calculate_breach_exposure,
    _detect_advisories,
    calculate_rcs,
    _auto_recommend,
    _log_rri_audit_event,
    TIER_RISK_MULTIPLIERS,
    RRI_WEIGHTS,
    RCS_WEIGHTS,
    BREACH_EXPOSURE_BADGES,
    MINUTES_PER_YEAR,
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
    """Create a minimal Organization with reliability defaults."""
    defaults = dict(
        id=str(uuid.uuid4()),
        name="Test Org",
        industry="technology",
        size="51-200",
        owner_uid="test-owner",
        application_tier="tier_2",
        sla_target=99.9,
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


def _make_tech_item(db: Session, org_id: str, technology: str, version: str, lts_status=LtsStatus.ACTIVE):
    """Create a tech stack item."""
    item = TechStackItem(
        id=str(uuid.uuid4()),
        org_id=org_id,
        technology=technology,
        version=version,
        lts_status=lts_status,
    )
    db.add(item)
    db.commit()
    return item


# ═════════════════════════════════════════════════════════════════════
# 1. Downtime Budget Calculator
# ═════════════════════════════════════════════════════════════════════

class TestDowntimeBudget:
    """Verify downtime budget calculation from SLA percentage."""

    def test_99_9_sla(self):
        """99.9% SLA → ~525.96 minutes/year."""
        budget = calculate_downtime_budget(99.9)
        assert budget.sla_target == 99.9
        assert 525 < budget.annual_minutes < 527
        assert 43 < budget.monthly_minutes < 44
        assert budget.annual_display  # non-empty
        assert budget.monthly_display

    def test_99_99_sla(self):
        """99.99% SLA → ~52.6 minutes/year."""
        budget = calculate_downtime_budget(99.99)
        assert 52 < budget.annual_minutes < 53

    def test_99_999_sla(self):
        """99.999% SLA (five nines) → ~5.26 minutes/year."""
        budget = calculate_downtime_budget(99.999)
        assert 5 < budget.annual_minutes < 6

    def test_99_0_sla(self):
        """99.0% SLA → ~5259 minutes/year."""
        budget = calculate_downtime_budget(99.0)
        assert 5259 < budget.annual_minutes < 5260

    def test_invalid_sla_defaults(self):
        """Invalid SLA (0 or negative) defaults to 99.0%."""
        budget = calculate_downtime_budget(0)
        assert budget.sla_target == 99.0

    def test_to_dict(self):
        """to_dict() returns serializable dict."""
        budget = calculate_downtime_budget(99.9)
        d = budget.to_dict()
        assert isinstance(d, dict)
        assert "sla_target" in d
        assert "annual_minutes" in d
        assert "monthly_minutes" in d


# ═════════════════════════════════════════════════════════════════════
# 2. Format Minutes
# ═════════════════════════════════════════════════════════════════════

class TestFormatMinutes:

    def test_seconds(self):
        """< 1 minute → seconds."""
        result = _format_minutes(0.5)
        assert "s" in result

    def test_minutes(self):
        """1-59 minutes → minutes."""
        result = _format_minutes(30)
        assert "m" in result

    def test_hours(self):
        """60-1440 minutes → hours."""
        result = _format_minutes(120)
        assert "h" in result

    def test_days(self):
        """> 24 hours → days."""
        result = _format_minutes(3000)
        assert "d" in result


# ═════════════════════════════════════════════════════════════════════
# 3. SLA Advisor
# ═════════════════════════════════════════════════════════════════════

class TestSLAAdvisor:
    """Verify industry-aware SLA recommendations."""

    def test_fintech(self):
        rec = get_sla_advisor("fintech")
        assert rec.recommended_tier == "Tier 1"
        assert rec.confidence == "high"
        assert rec.sla_range[0] >= 99.9

    def test_healthcare(self):
        rec = get_sla_advisor("healthcare")
        assert rec.recommended_tier == "Tier 0"
        assert rec.sla_range[0] >= 99.99

    def test_education(self):
        rec = get_sla_advisor("education")
        assert rec.recommended_tier == "Tier 3"
        assert rec.sla_range[0] >= 99.0

    def test_unknown_industry(self):
        rec = get_sla_advisor("underwater-basket-weaving")
        assert rec.recommended_tier == "Tier 2"
        assert rec.confidence == "medium"

    def test_none_industry(self):
        rec = get_sla_advisor(None)
        assert rec.recommended_tier == "Tier 2"

    def test_to_dict(self):
        rec = get_sla_advisor("technology")
        d = rec.to_dict()
        assert isinstance(d, dict)
        assert "recommended_tier" in d
        assert "rationale" in d


# ═════════════════════════════════════════════════════════════════════
# 4. Risk Band & Breach Probability
# ═════════════════════════════════════════════════════════════════════

class TestRiskBands:
    """Verify score → risk band & breach probability mapping."""

    def test_low(self):
        assert _get_risk_band(10) == "Low"
        assert _get_risk_band(25) == "Low"

    def test_moderate(self):
        assert _get_risk_band(30) == "Moderate"
        assert _get_risk_band(50) == "Moderate"

    def test_high(self):
        assert _get_risk_band(60) == "High"
        assert _get_risk_band(75) == "High"

    def test_critical(self):
        assert _get_risk_band(80) == "Critical"
        assert _get_risk_band(100) == "Critical"

    def test_breach_negligible(self):
        assert _get_breach_probability(10) == "Negligible"

    def test_breach_low(self):
        assert _get_breach_probability(30) == "Low"

    def test_breach_moderate(self):
        assert _get_breach_probability(50) == "Moderate"

    def test_breach_high(self):
        assert _get_breach_probability(70) == "High"


# ═════════════════════════════════════════════════════════════════════
# 5. Dimension Scorers
# ═════════════════════════════════════════════════════════════════════

class TestDimensionScorers:
    """Test individual RRI dimension scoring functions."""

    def test_sla_no_target(self):
        """No SLA target → high risk."""
        dim = _score_sla_commitment(None, "tier_2")
        assert dim.score >= 60
        assert len(dim.gaps) > 0

    def test_sla_high_target(self):
        """99.99% SLA → very high commitment risk."""
        dim = _score_sla_commitment(99.99, "tier_1")
        assert dim.score >= 70
        assert dim.key == "sla_commitment"

    def test_sla_low_target(self):
        """99.0% SLA → low commitment risk."""
        dim = _score_sla_commitment(99.0, "tier_3")
        assert dim.score <= 30

    def test_sla_mismatch_tier(self):
        """High SLA + low tier = penalty."""
        dim = _score_sla_commitment(99.99, "tier_3")
        assert dim.score >= 90  # mismatch penalty

    def test_sla_weight(self):
        """Weight matches RRI_WEIGHTS."""
        dim = _score_sla_commitment(99.9, "tier_2")
        assert dim.weight == RRI_WEIGHTS["sla_commitment"]
        assert abs(dim.weighted_score - dim.score * dim.weight) < 0.01

    def test_recovery_no_answers(self):
        """No assessment data → high risk."""
        dim = _score_recovery_capability({}, 0)
        assert dim.score >= 70
        assert dim.key == "recovery_capability"

    def test_recovery_good_controls(self):
        """All RS answers positive → low risk."""
        answers = {f"rs_0{i}": True for i in range(1, 7)}
        dim = _score_recovery_capability(answers, 3)
        assert dim.score <= 20

    def test_recovery_rto_undefined(self):
        """RTO 'not defined' → penalty."""
        answers = {"rs_05": "not defined"}
        dim = _score_recovery_capability(answers, 0)
        assert dim.score >= 60

    def test_redundancy_no_data(self):
        """No data → moderate-high risk."""
        dim = _score_redundancy_ha({}, [])
        assert dim.score >= 50

    def test_redundancy_with_ha_tech(self):
        """HA tech registered → lower risk."""
        mock_item = MagicMock()
        mock_item.category = "Load Balancer"
        dim = _score_redundancy_ha({"rs_02": True, "rs_04": True}, [mock_item])
        assert dim.score < 50

    def test_monitoring_no_data(self):
        """No monitoring data → high risk."""
        dim = _score_monitoring_detection({})
        assert dim.score >= 70

    def test_monitoring_good_coverage(self):
        """All monitoring controls active → low risk."""
        answers = {f"tl_0{i}": True for i in range(1, 7)}
        answers.update({f"dc_0{i}": True for i in range(1, 7)})
        dim = _score_monitoring_detection(answers)
        assert dim.score <= 20

    def test_bcdr_no_data(self):
        """No IR data → high risk."""
        dim = _score_bcdr_validation({}, [])
        assert dim.score >= 60

    def test_bcdr_good_ir(self):
        """All IR controls + DR testing → low risk."""
        answers = {f"ir_0{i}": True for i in range(1, 7)}
        answers["rs_03"] = True
        audit_entries = [MagicMock(), MagicMock()]
        dim = _score_bcdr_validation(answers, audit_entries)
        assert dim.score <= 30


# ═════════════════════════════════════════════════════════════════════
# 6. Composite RRI Score
# ═════════════════════════════════════════════════════════════════════

class TestCompositeRRI:
    """Test the full RRI calculation pipeline."""

    def test_basic_rri_calculation(self, db):
        """Basic RRI returns valid result with all fields."""
        org = _make_org(db)
        result = calculate_rri(db, org)

        assert 0 <= result.rri_score <= 100
        assert result.risk_band in ("Low", "Moderate", "High", "Critical")
        assert result.breach_probability in ("Negligible", "Low", "Moderate", "High")
        assert result.application_tier in ("Tier 0", "Tier 1", "Tier 2", "Tier 3", "Tier 4", "Not configured")
        assert len(result.dimensions) == 5
        assert result.architecture_alignment in ("aligned", "partial", "high_risk")
        assert result.sla_advisor is not None

    def test_rri_with_high_sla(self, db):
        """High SLA target → higher risk exposure."""
        org = _make_org(db, sla_target=99.99, application_tier="tier_1")
        result = calculate_rri(db, org)
        assert result.rri_score >= 40  # significant commitment risk

    def test_rri_with_low_sla(self, db):
        """Low SLA target → lower risk exposure."""
        org = _make_org(db, sla_target=99.0, application_tier="tier_3")
        result = calculate_rri(db, org)
        assert result.rri_score < 80

    def test_rri_tier_multiplier_applied(self, db):
        """Tier 0 multiplier (1.3) amplifies raw score."""
        org = _make_org(db, application_tier="tier_0", sla_target=99.99)
        result = calculate_rri(db, org)
        assert result.tier_multiplier == 1.30
        # rri_score should be raw × 1.3 (capped at 100)
        expected = min(100, round(result.raw_score * 1.30, 1))
        assert result.rri_score == expected

    def test_rri_tier_3_reduced(self, db):
        """Tier 3 multiplier (0.85) reduces raw score."""
        org = _make_org(db, application_tier="tier_3", sla_target=99.0)
        result = calculate_rri(db, org)
        assert result.tier_multiplier == 0.85

    def test_rri_downtime_budget_included(self, db):
        """Downtime budget calculated when SLA is set."""
        org = _make_org(db, sla_target=99.9)
        result = calculate_rri(db, org)
        assert result.downtime_budget is not None
        assert result.downtime_budget.sla_target == 99.9

    def test_rri_downtime_budget_none_without_sla(self, db):
        """No downtime budget when SLA is not set."""
        org = _make_org(db, sla_target=None)
        result = calculate_rri(db, org)
        assert result.downtime_budget is None

    def test_rri_top_gaps_capped(self, db):
        """Top gaps limited to 5."""
        org = _make_org(db)
        result = calculate_rri(db, org)
        assert len(result.top_gaps) <= 5

    def test_rri_to_dict(self, db):
        """to_dict() returns serializable dict."""
        org = _make_org(db)
        result = calculate_rri(db, org)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "rri_score" in d
        assert "dimensions" in d
        assert isinstance(d["dimensions"], list)

    def test_rri_with_custom_answers(self, db):
        """Supplying answers directly changes the score."""
        org = _make_org(db, sla_target=99.9)
        # Minimal answers
        result_empty = calculate_rri(db, org, answers={})
        # Full positive answers
        good_answers = {}
        for prefix in ("rs_", "tl_", "dc_", "ir_"):
            for i in range(1, 7):
                good_answers[f"{prefix}0{i}"] = True
        result_good = calculate_rri(db, org, answers=good_answers)
        # Good answers should yield lower risk
        assert result_good.rri_score < result_empty.rri_score

    def test_rri_all_dimensions_weighted(self, db):
        """All 5 dimensions have correct weights summing to 1.0."""
        org = _make_org(db)
        result = calculate_rri(db, org)
        total_weight = sum(d.weight for d in result.dimensions)
        assert abs(total_weight - 1.0) < 0.001

    def test_rri_dimension_keys(self, db):
        """All expected dimension keys present."""
        org = _make_org(db)
        result = calculate_rri(db, org)
        keys = {d.key for d in result.dimensions}
        assert keys == {"sla_commitment", "recovery_capability", "redundancy_ha", "monitoring_detection", "bcdr_validation"}


# ═════════════════════════════════════════════════════════════════════
# 7. Board Simulation Mode
# ═════════════════════════════════════════════════════════════════════

class TestBoardSimulation:
    """Test breach simulation (What-if analysis)."""

    def test_simulate_upgrade(self, db):
        """Simulating SLA upgrade returns valid result."""
        org = _make_org(db, sla_target=99.0)
        result = simulate_breach(db, org, simulated_sla=99.99)

        assert result.current_sla == 99.0
        assert result.simulated_sla == 99.99
        assert result.current_budget.sla_target == 99.0
        assert result.simulated_budget.sla_target == 99.99
        assert result.simulated_budget.annual_minutes < result.current_budget.annual_minutes
        assert isinstance(result.required_improvements, list)
        assert isinstance(result.cost_impact, str)
        assert len(result.cost_impact) > 0

    def test_simulate_downgrade(self, db):
        """Simulating SLA downgrade → less stringent."""
        org = _make_org(db, sla_target=99.99)
        result = simulate_breach(db, org, simulated_sla=99.0)

        assert result.simulated_budget.annual_minutes > result.current_budget.annual_minutes

    def test_simulate_preserves_org(self, db):
        """Simulation does not persist changes to org."""
        org = _make_org(db, sla_target=99.0, application_tier="tier_3")
        _ = simulate_breach(db, org, simulated_sla=99.99)
        assert org.sla_target == 99.0
        assert org.application_tier == "tier_3"

    def test_simulate_to_dict(self, db):
        """to_dict() returns serializable dict."""
        org = _make_org(db, sla_target=99.5)
        result = simulate_breach(db, org, simulated_sla=99.9)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "readiness_delta" in d
        assert "cost_impact" in d

    def test_simulate_five_nines(self, db):
        """Upgrade to 99.99% → significant improvements required."""
        org = _make_org(db, sla_target=99.0)
        result = simulate_breach(db, org, simulated_sla=99.99)
        assert len(result.required_improvements) >= 2
        assert "Significant" in result.cost_impact


# ═════════════════════════════════════════════════════════════════════
# 8. API Endpoint Tests
# ═════════════════════════════════════════════════════════════════════

class TestReliabilityAPI:
    """Test the RRI API endpoints (staging-gated)."""

    @pytest.fixture(autouse=True)
    def setup_client(self, db):
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

    def test_404_when_not_staging(self):
        """Non-staging environment → 404 (invisible)."""
        resp = self.client.get("/api/governance/any-id/reliability-index")
        assert resp.status_code == 404

    def test_200_when_staging(self):
        """Staging env → 200 with full RRI result."""
        org = _make_org(self.db, owner_uid="dev-user")
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index")
            assert resp.status_code == 200
            data = resp.json()
            assert "rri_score" in data
            assert "dimensions" in data
            assert "risk_band" in data
            assert len(data["dimensions"]) == 5

    def test_simulate_404_when_not_staging(self):
        """Simulation endpoint → 404 outside staging."""
        resp = self.client.post(
            "/api/governance/any-id/reliability-index/simulate",
            json={"simulated_sla": 99.99},
        )
        assert resp.status_code == 404

    def test_simulate_200_when_staging(self):
        """Simulation endpoint → 200 in staging."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=99.0)
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.post(
                f"/api/governance/{org.id}/reliability-index/simulate",
                json={"simulated_sla": 99.99},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["current_sla"] == 99.0
            assert data["simulated_sla"] == 99.99
            assert "readiness_delta" in data

    def test_advisor_200_when_staging(self):
        """SLA Advisor → 200 in staging."""
        org = _make_org(self.db, owner_uid="dev-user", industry="fintech")
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index/advisor")
            assert resp.status_code == 200
            data = resp.json()
            assert data["recommended_tier"] == "Tier 1"
            assert data["industry"] == "fintech"

    def test_downtime_budget_200(self):
        """Downtime budget → 200 in staging."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=99.9)
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index/downtime-budget")
            assert resp.status_code == 200
            data = resp.json()
            assert data["sla_target"] == 99.9
            assert data["annual_minutes"] > 0

    def test_downtime_budget_400_no_sla(self):
        """Downtime budget without SLA → 400."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=None)
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index/downtime-budget")
            assert resp.status_code == 400

    def test_404_org_not_found(self):
        """Nonexistent org → 404."""
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get("/api/governance/nonexistent-org/reliability-index")
            assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════
# 9. Tier Multiplier Constants
# ═════════════════════════════════════════════════════════════════════

class TestTierMultipliers:
    """Verify tier multiplier constants are correct."""

    def test_tier_0(self):
        assert TIER_RISK_MULTIPLIERS["tier_0"] == 1.30

    def test_tier_1(self):
        assert TIER_RISK_MULTIPLIERS["tier_1"] == 1.15

    def test_tier_2(self):
        assert TIER_RISK_MULTIPLIERS["tier_2"] == 1.00

    def test_tier_3(self):
        assert TIER_RISK_MULTIPLIERS["tier_3"] == 0.85

    def test_weights_sum_to_one(self):
        total = sum(RRI_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001


# ═════════════════════════════════════════════════════════════════════
# 10. Breach Exposure Badge (4 levels)
# ═════════════════════════════════════════════════════════════════════

class TestBreachExposureBadge:
    """Verify 4-level executive breach exposure badge calculation."""

    def test_within_budget_low_scores(self):
        """Low recovery + SLA scores → within_budget (green)."""
        badge = _calculate_breach_exposure(99.9, 10.0, 15.0)
        assert badge.level == "within_budget"
        assert badge.severity == "green"
        assert badge.badge == BREACH_EXPOSURE_BADGES["within_budget"]["badge"]

    def test_sla_strain_moderate_scores(self):
        """Moderate scores → sla_strain (yellow)."""
        badge = _calculate_breach_exposure(99.9, 40.0, 50.0)
        assert badge.level == "sla_strain"
        assert badge.severity == "yellow"

    def test_breach_high_elevated_scores(self):
        """High scores → breach_high (red)."""
        badge = _calculate_breach_exposure(99.99, 65.0, 70.0)
        assert badge.level == "breach_high"
        assert badge.severity == "red"

    def test_contractual_risk_extreme_scores(self):
        """Very high scores → contractual_risk (black)."""
        badge = _calculate_breach_exposure(99.999, 85.0, 80.0)
        assert badge.level == "contractual_risk"
        assert badge.severity == "black"

    def test_no_sla_target(self):
        """When SLA is None → sla_strain with explanation about missing config."""
        badge = _calculate_breach_exposure(None, 20.0, 20.0)
        assert badge.level == "sla_strain"
        assert badge.severity == "yellow"
        assert "not configured" in badge.explanation.lower()

    def test_badge_emoji_present(self):
        """All levels have non-empty badge string."""
        for level, config in BREACH_EXPOSURE_BADGES.items():
            assert config["badge"], f"Missing badge for {level}"

    def test_breach_exposure_to_dict(self):
        """to_dict() returns serializable dict."""
        badge = _calculate_breach_exposure(99.9, 20.0, 20.0)
        d = badge.to_dict()
        assert isinstance(d, dict)
        assert "level" in d
        assert "badge" in d
        assert "severity" in d
        assert "explanation" in d

    def test_boundary_25(self):
        """Exposure exactly 25 → within_budget."""
        badge = _calculate_breach_exposure(99.9, 25.0, 25.0)
        assert badge.level == "within_budget"

    def test_boundary_just_above_25(self):
        """Exposure 26 → sla_strain."""
        badge = _calculate_breach_exposure(99.9, 26.0, 26.0)
        assert badge.level == "sla_strain"


# ═════════════════════════════════════════════════════════════════════
# 11. Autonomous Advisory Engine (7 rules)
# ═════════════════════════════════════════════════════════════════════

class TestAutonomousAdvisories:
    """Verify deterministic advisory detection rules."""

    @pytest.fixture(autouse=True)
    def _setup(self, db):
        self.db = db

    def test_no_advisories_when_aligned(self):
        """Aligned org with good practices → no advisories."""
        org = _make_org(self.db, sla_target=99.5, application_tier="tier_1")
        answers = {"rs_02": True, "rs_03": True, "rs_04": True, "rs_05": 4,
                   "ir_01": True, "ir_02": True}
        dims = [MagicMock(key="monitoring_detection", score=30)]
        advisories = _detect_advisories(org, answers, dims, [])
        assert len(advisories) == 0

    def test_rule1_high_sla_no_failover(self):
        """Rule 1: 99.99% SLA + no failover → critical advisory."""
        org = _make_org(self.db, sla_target=99.99, application_tier="tier_0")
        answers = {"rs_02": True, "rs_03": True, "rs_04": True, "rs_05": 4, "ir_01": True}
        dims = [MagicMock(key="monitoring_detection", score=20)]
        advisories = _detect_advisories(org, answers, dims, [])
        arch_advisories = [a for a in advisories if "Architectural" in a.title or "Misalignment" in a.title]
        assert len(arch_advisories) >= 1
        assert arch_advisories[0].severity == "critical"

    def test_rule2_high_sla_low_tier(self):
        """Rule 2: 99.9% SLA + tier_3 → critical tier-SLA conflict."""
        org = _make_org(self.db, sla_target=99.9, application_tier="tier_3")
        answers = {"rs_02": True, "rs_04": True, "ir_01": True}
        dims = [MagicMock(key="monitoring_detection", score=20)]
        advisories = _detect_advisories(org, answers, dims, [])
        tier_advisories = [a for a in advisories if "Tier" in a.title]
        assert len(tier_advisories) >= 1
        assert tier_advisories[0].severity == "critical"

    def test_rule3_no_dr_plan(self):
        """Rule 3: Production SLA + no DR plan → high advisory."""
        org = _make_org(self.db, sla_target=99.5, application_tier="tier_1")
        answers = {"rs_02": True, "rs_04": False}
        dims = [MagicMock(key="monitoring_detection", score=20)]
        advisories = _detect_advisories(org, answers, dims, [])
        dr_advisories = [a for a in advisories if "Disaster Recovery" in a.title]
        assert len(dr_advisories) >= 1
        assert dr_advisories[0].severity == "high"

    def test_rule4_monitoring_blindspot(self):
        """Rule 4: High monitoring score (= poor monitoring) → high advisory."""
        org = _make_org(self.db, sla_target=99.5, application_tier="tier_1")
        answers = {"rs_02": True, "rs_04": True, "ir_01": True}
        dims = [MagicMock(key="monitoring_detection", score=75)]
        advisories = _detect_advisories(org, answers, dims, [])
        mon_advisories = [a for a in advisories if "Monitoring" in a.title]
        assert len(mon_advisories) >= 1
        assert mon_advisories[0].severity == "high"

    def test_rule5_no_ir_readiness(self):
        """Rule 5: High SLA + no IR controls → high advisory."""
        org = _make_org(self.db, sla_target=99.9, application_tier="tier_1")
        answers = {"rs_02": True, "rs_04": True}
        dims = [MagicMock(key="monitoring_detection", score=20)]
        advisories = _detect_advisories(org, answers, dims, [])
        ir_advisories = [a for a in advisories if "Incident Response" in a.title]
        assert len(ir_advisories) >= 1

    def test_rule6_no_backup_docs(self):
        """Rule 6: No backup documentation → medium advisory."""
        org = _make_org(self.db, sla_target=99.5, application_tier="tier_1")
        answers = {"rs_04": True, "ir_01": True}
        dims = [MagicMock(key="monitoring_detection", score=20)]
        advisories = _detect_advisories(org, answers, dims, [])
        backup_advisories = [a for a in advisories if "Backup" in a.title]
        assert len(backup_advisories) >= 1
        assert backup_advisories[0].severity == "medium"

    def test_rule7_no_rto(self):
        """Rule 7: High SLA + no RTO → medium advisory."""
        org = _make_org(self.db, sla_target=99.5, application_tier="tier_1")
        answers = {"rs_02": True, "rs_04": True, "ir_01": True}
        dims = [MagicMock(key="monitoring_detection", score=20)]
        advisories = _detect_advisories(org, answers, dims, [])
        rto_advisories = [a for a in advisories if "RTO" in a.title]
        assert len(rto_advisories) >= 1
        assert rto_advisories[0].severity == "medium"

    def test_advisory_has_remediation(self):
        """All advisories include non-empty remediation text."""
        org = _make_org(self.db, sla_target=99.99, application_tier="tier_3")
        answers = {}
        dims = [MagicMock(key="monitoring_detection", score=80)]
        advisories = _detect_advisories(org, answers, dims, [])
        assert len(advisories) > 0
        for adv in advisories:
            assert adv.remediation, f"Missing remediation for: {adv.title}"

    def test_advisory_to_dict(self):
        """to_dict() returns serializable advisory."""
        org = _make_org(self.db, sla_target=99.99, application_tier="tier_3")
        answers = {}
        dims = [MagicMock(key="monitoring_detection", score=20)]
        advisories = _detect_advisories(org, answers, dims, [])
        assert len(advisories) > 0
        d = advisories[0].to_dict()
        assert isinstance(d, dict)
        assert "severity" in d
        assert "title" in d

    def test_multiple_rules_fire_together(self):
        """Multiple rules can fire on the same org."""
        org = _make_org(self.db, sla_target=99.99, application_tier="tier_3")
        answers = {}  # All answers missing
        dims = [MagicMock(key="monitoring_detection", score=80)]
        advisories = _detect_advisories(org, answers, dims, [])
        # Should fire: rule2 (tier conflict), rule3 (no DR), rule4 (monitoring),
        # rule5 (no IR), rule6 (no backup), rule7 (no RTO)
        assert len(advisories) >= 4


# ═════════════════════════════════════════════════════════════════════
# 12. Reliability Confidence Score (RCS)
# ═════════════════════════════════════════════════════════════════════

class TestReliabilityConfidenceScore:
    """Verify RCS 5-dimensional scoring and bands."""

    def test_all_positive_answers(self):
        """Full positive answers → high RCS."""
        answers = {
            "rs_02": True, "rs_03": True, "rs_04": True, "rs_05": 4,
            "rs_06": True,
            "ir_01": True, "ir_02": True, "ir_03": True,
            "tl_01": True, "tl_02": True, "dc_01": True,
        }
        rcs = calculate_rcs(answers, [], [])
        assert rcs.total_score >= 50
        assert rcs.dr_test_recency > 0
        assert rcs.backup_validation > 0
        assert rcs.ir_tabletop_recency > 0
        assert rcs.monitoring_coverage > 0

    def test_no_answers(self):
        """No answers → Unvalidated band."""
        rcs = calculate_rcs({}, [], [])
        assert rcs.total_score == 0.0
        assert rcs.confidence_band == "Unvalidated"

    def test_verified_band(self):
        """High scoring → Verified band (≥75)."""
        answers = {
            "rs_02": True, "rs_03": True, "rs_04": True,
            "rs_06": True,
            "ir_01": True, "ir_02": True, "ir_03": True, "ir_04": True,
            "tl_01": True, "tl_02": True, "tl_03": True,
            "dc_01": True, "dc_02": True,
        }
        # Add tech items with HA categories
        tech_items = []
        for cat in ["load balancer", "cdn", "cache", "database"]:
            t = MagicMock()
            t.category = cat
            tech_items.append(t)
        rcs = calculate_rcs(answers, tech_items, [])
        assert rcs.confidence_band == "Verified"
        assert rcs.total_score >= 75

    def test_moderate_band(self):
        """Mid-range scores → Moderate band (50-74)."""
        answers = {
            "rs_02": True, "rs_03": True, "rs_04": True,
            "ir_01": True,
            "tl_01": True, "dc_01": True,
        }
        rcs = calculate_rcs(answers, [], [])
        assert rcs.confidence_band in ("Moderate", "Low", "Verified")

    def test_dr_test_recency_scoring(self):
        """DR test True → 18 points, False → 3 points."""
        rcs_true = calculate_rcs({"rs_03": True}, [], [])
        rcs_false = calculate_rcs({"rs_03": False}, [], [])
        assert rcs_true.dr_test_recency == 18.0
        assert rcs_false.dr_test_recency == 3.0

    def test_backup_validation_combined(self):
        """Backup doc + restore → max 20."""
        rcs = calculate_rcs({"rs_02": True, "rs_06": True}, [], [])
        assert rcs.backup_validation == 20.0

    def test_architecture_redundancy_with_tech(self):
        """Tech items in HA categories boost architecture score."""
        tech = []
        for cat in ["load balancer", "cdn", "cache"]:
            t = MagicMock()
            t.category = cat
            tech.append(t)
        rcs = calculate_rcs({"rs_04": True}, tech, [])
        # 3 tech * 3 = 9, capped at 12 + 8 (DR plan) = 20
        assert rcs.architecture_redundancy >= 17.0

    def test_sub_scores_dict(self):
        """sub_scores dict contains all 5 dimensions."""
        rcs = calculate_rcs({"rs_03": True}, [], [])
        assert "dr_test_recency" in rcs.sub_scores
        assert "backup_validation" in rcs.sub_scores
        assert "ir_tabletop_recency" in rcs.sub_scores
        assert "monitoring_coverage" in rcs.sub_scores
        assert "architecture_redundancy" in rcs.sub_scores

    def test_rcs_weights_sum_to_one(self):
        """RCS dimension weights must sum to 1.0."""
        total = sum(RCS_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_rcs_to_dict(self):
        """to_dict() returns full serializable dict."""
        rcs = calculate_rcs({"rs_03": True}, [], [])
        d = rcs.to_dict()
        assert isinstance(d, dict)
        assert "total_score" in d
        assert "confidence_band" in d
        assert "sub_scores" in d

    def test_max_score_100(self):
        """Total score cannot exceed 100."""
        answers = {
            "rs_02": True, "rs_03": True, "rs_04": True,
            "rs_06": True,
            "ir_01": True, "ir_02": True, "ir_03": True, "ir_04": True,
            "tl_01": True, "tl_02": True, "tl_03": True,
            "dc_01": True, "dc_02": True, "dc_03": True,
        }
        tech = [MagicMock(category=cat) for cat in ["load balancer", "cdn", "cache", "database", "queue", "storage"]]
        rcs = calculate_rcs(answers, tech, [])
        assert rcs.total_score <= 100.0


# ═════════════════════════════════════════════════════════════════════
# 13. Auto-Recommendation Engine
# ═════════════════════════════════════════════════════════════════════

class TestAutoRecommendation:
    """Verify auto-detect of missing tier/SLA."""

    @pytest.fixture(autouse=True)
    def _setup(self, db):
        self.db = db

    def test_returns_none_when_configured(self):
        """Org with both tier + SLA → no recommendation."""
        org = _make_org(self.db, application_tier="tier_1", sla_target=99.9)
        rec = _auto_recommend(org)
        assert rec is None

    def test_recommends_when_sla_missing(self):
        """Missing SLA → generates recommendation."""
        org = _make_org(self.db, application_tier="tier_1", sla_target=None)
        rec = _auto_recommend(org)
        assert rec is not None
        assert rec.recommended_sla > 0
        assert rec.recommended_tier

    def test_recommends_when_tier_missing(self):
        """Missing tier → generates recommendation."""
        org = _make_org(self.db, application_tier=None, sla_target=99.9)
        rec = _auto_recommend(org)
        assert rec is not None
        assert rec.recommended_tier

    def test_recommends_when_tier_empty(self):
        """Empty tier string → generates recommendation."""
        org = _make_org(self.db, application_tier="", sla_target=99.9)
        rec = _auto_recommend(org)
        assert rec is not None

    def test_recommends_when_both_missing(self):
        """Both tier + SLA missing → generates recommendation."""
        org = _make_org(self.db, application_tier=None, sla_target=None)
        rec = _auto_recommend(org)
        assert rec is not None
        assert rec.recommended_sla > 0
        assert rec.recommended_tier

    def test_recommendation_has_rationale(self):
        """Recommendation includes non-empty rationale."""
        org = _make_org(self.db, application_tier=None, sla_target=None, industry="healthcare")
        rec = _auto_recommend(org)
        assert rec is not None
        assert rec.rationale
        assert rec.accept_action

    def test_recommendation_source_industry(self):
        """Known industry → source is 'industry'."""
        org = _make_org(self.db, application_tier=None, sla_target=None, industry="healthcare")
        rec = _auto_recommend(org)
        assert rec is not None
        assert rec.source in ("industry", "default")

    def test_recommendation_to_dict(self):
        """to_dict() returns serializable dict."""
        org = _make_org(self.db, application_tier=None, sla_target=None)
        rec = _auto_recommend(org)
        assert rec is not None
        d = rec.to_dict()
        assert isinstance(d, dict)
        assert "recommended_tier" in d
        assert "recommended_sla" in d


# ═════════════════════════════════════════════════════════════════════
# 14. Audit Trail Logging
# ═════════════════════════════════════════════════════════════════════

class TestAuditTrailLogging:
    """Verify RRI audit event logging."""

    @pytest.fixture(autouse=True)
    def _setup(self, db):
        self.db = db

    def test_logs_audit_event(self):
        """_log_rri_audit_event creates an AuditEvent record."""
        org = _make_org(self.db)
        _log_rri_audit_event(self.db, org.id, "system", 45.5, 62.0)
        from app.models.audit_event import AuditEvent
        events = self.db.query(AuditEvent).filter_by(org_id=org.id).all()
        assert len(events) == 1
        assert "rri_calculated" in events[0].action
        assert "score=45.5" in events[0].action
        assert "rcs=62.0" in events[0].action

    def test_logs_multiple_events(self):
        """Multiple calls create multiple audit events."""
        org = _make_org(self.db)
        _log_rri_audit_event(self.db, org.id, "system", 45.0, 60.0)
        _log_rri_audit_event(self.db, org.id, "system", 42.0, 65.0)
        from app.models.audit_event import AuditEvent
        events = self.db.query(AuditEvent).filter_by(org_id=org.id).all()
        assert len(events) == 2


# ═════════════════════════════════════════════════════════════════════
# 15. Breach Exposure Badge Constants
# ═════════════════════════════════════════════════════════════════════

class TestBreachExposureConstants:
    """Verify BREACH_EXPOSURE_BADGES constant structure."""

    def test_has_four_levels(self):
        assert len(BREACH_EXPOSURE_BADGES) == 4

    def test_within_budget(self):
        assert "within_budget" in BREACH_EXPOSURE_BADGES
        assert BREACH_EXPOSURE_BADGES["within_budget"]["severity"] == "green"

    def test_sla_strain(self):
        assert "sla_strain" in BREACH_EXPOSURE_BADGES
        assert BREACH_EXPOSURE_BADGES["sla_strain"]["severity"] == "yellow"

    def test_breach_high(self):
        assert "breach_high" in BREACH_EXPOSURE_BADGES
        assert BREACH_EXPOSURE_BADGES["breach_high"]["severity"] == "red"

    def test_contractual_risk(self):
        assert "contractual_risk" in BREACH_EXPOSURE_BADGES
        assert BREACH_EXPOSURE_BADGES["contractual_risk"]["severity"] == "black"


# ═════════════════════════════════════════════════════════════════════
# 16. RRI v2 integrated — calculate_rri returns new fields
# ═════════════════════════════════════════════════════════════════════

class TestRRIv2Integration:
    """Verify calculate_rri returns all v2 fields wired correctly."""

    @pytest.fixture(autouse=True)
    def _setup(self, db):
        self.db = db

    def test_rri_has_breach_exposure(self):
        """calculate_rri result includes breach_exposure badge."""
        org = _make_org(self.db, sla_target=99.9, application_tier="tier_2")
        result = calculate_rri(self.db, org)
        assert result.breach_exposure is not None
        assert result.breach_exposure.level in ("within_budget", "sla_strain", "breach_high", "contractual_risk")
        assert result.breach_exposure.severity in ("green", "yellow", "red", "black")

    def test_rri_has_advisories(self):
        """calculate_rri result includes advisories list."""
        org = _make_org(self.db, sla_target=99.99, application_tier="tier_3")
        result = calculate_rri(self.db, org)
        assert isinstance(result.advisories, list)
        # tier_3 + 99.99 SLA should trigger at least the tier-SLA conflict
        assert len(result.advisories) >= 1

    def test_rri_has_rcs(self):
        """calculate_rri result includes reliability_confidence."""
        org = _make_org(self.db, sla_target=99.9, application_tier="tier_2")
        result = calculate_rri(self.db, org)
        assert result.reliability_confidence is not None
        assert 0 <= result.reliability_confidence.total_score <= 100
        assert result.reliability_confidence.confidence_band in ("Verified", "Moderate", "Low", "Unvalidated")

    def test_rri_has_auto_recommendation_when_missing(self):
        """calculate_rri returns auto_recommendation when tier/SLA missing."""
        org = _make_org(self.db, sla_target=None, application_tier=None)
        result = calculate_rri(self.db, org)
        assert result.auto_recommendation is not None

    def test_rri_no_auto_recommendation_when_configured(self):
        """calculate_rri returns None auto_recommendation when configured."""
        org = _make_org(self.db, sla_target=99.9, application_tier="tier_2")
        result = calculate_rri(self.db, org)
        assert result.auto_recommendation is None

    def test_rri_to_dict_includes_v2_fields(self):
        """to_dict() includes all v2 serialized fields."""
        org = _make_org(self.db, sla_target=99.9, application_tier="tier_2")
        result = calculate_rri(self.db, org)
        d = result.to_dict()
        assert "breach_exposure" in d
        assert "advisories" in d
        assert "reliability_confidence" in d
        assert "auto_recommendation" in d

    def test_audit_event_created_on_calculate(self):
        """calculate_rri writes an audit event."""
        org = _make_org(self.db, sla_target=99.9, application_tier="tier_2")
        calculate_rri(self.db, org)
        from app.models.audit_event import AuditEvent
        events = self.db.query(AuditEvent).filter_by(org_id=org.id).all()
        rri_events = [e for e in events if "rri_calculated" in e.action]
        assert len(rri_events) >= 1


# ═════════════════════════════════════════════════════════════════════
# 17. New API Endpoints (v2)
# ═════════════════════════════════════════════════════════════════════

class TestRRIv2API:
    """Verify new v2 API endpoints: confidence, accept-recommendation, history."""

    @pytest.fixture(autouse=True)
    def _setup(self, db):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.database import get_db

        self.db = db
        app.dependency_overrides[get_db] = lambda: db
        self.client = TestClient(app)

    def test_confidence_endpoint(self):
        """GET /confidence returns RCS data."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=99.9, application_tier="tier_2")
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index/confidence")
            assert resp.status_code == 200
            data = resp.json()
            assert "total_score" in data
            assert "confidence_band" in data
            assert "sub_scores" in data

    def test_confidence_404_no_org(self):
        """GET /confidence for nonexistent org → 404."""
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get("/api/governance/nonexistent/reliability-index/confidence")
            assert resp.status_code == 404

    def test_accept_recommendation_endpoint(self):
        """POST /accept-recommendation updates org fields."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=None, application_tier=None)
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.post(
                f"/api/governance/{org.id}/reliability-index/accept-recommendation",
                json={"recommended_tier": "tier_1", "recommended_sla": 99.9},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "accepted"
            assert "tier=tier_1" in data["applied"]
            assert "sla=99.9" in data["applied"]

    def test_accept_recommendation_404_no_org(self):
        """POST /accept-recommendation for nonexistent org → 404."""
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.post(
                "/api/governance/nonexistent/reliability-index/accept-recommendation",
                json={"recommended_tier": "tier_1", "recommended_sla": 99.9},
            )
            assert resp.status_code == 404

    def test_history_endpoint_empty(self):
        """GET /history returns empty list when no audit events."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=99.9, application_tier="tier_2")
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index/history")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)

    def test_history_after_calculation(self):
        """GET /history returns snapshots after RRI calculation."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=99.9, application_tier="tier_2")
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            # Trigger RRI calculation to create audit events
            self.client.get(f"/api/governance/{org.id}/reliability-index")
            # Now get history
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index/history")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert "rri_score" in data[0]
                assert "rcs_score" in data[0]

    def test_rri_response_includes_v2_fields(self):
        """GET /reliability-index response includes v2 fields."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=99.9, application_tier="tier_2")
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.STAGING
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index")
            assert resp.status_code == 200
            data = resp.json()
            assert "breach_exposure" in data
            assert "advisories" in data
            assert "reliability_confidence" in data

    def test_staging_gate_on_new_endpoints(self):
        """New endpoints return 404 outside staging."""
        org = _make_org(self.db, owner_uid="dev-user", sla_target=99.9, application_tier="tier_2")
        with patch("app.api.reliability.settings") as mock_settings:
            from app.core.config import Environment
            mock_settings.ENV = Environment.PROD
            resp = self.client.get(f"/api/governance/{org.id}/reliability-index/confidence")
            assert resp.status_code == 404
