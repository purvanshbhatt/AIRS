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
    TIER_RISK_MULTIPLIERS,
    RRI_WEIGHTS,
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
