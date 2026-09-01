import pytest
from datetime import datetime, timezone
from app.services.clinic_engine.v2.contracts import VerificationContext, ActionCard
from app.services.clinic_engine.v2.schema import ClinicMoment, MomentTranslation, Verdict
from app.services.clinic_engine.v2.explainability_engine import ExplainabilityEngine

@pytest.fixture
def engine():
    return ExplainabilityEngine()

@pytest.fixture
def mock_moment():
    return ClinicMoment(
        id="m-123",
        org_id="org-1",
        question_id="q-123",
        capability_id="device_compromise",
        verdict=Verdict.CRITICAL,
        evidence_ids=[],
        translation=MomentTranslation(what_happened="Device is compromised", why_care="Hackers can access data", ignore_impact="Data theft risk"),
        actions=[]
    )

def test_explainability_determinism(engine, mock_moment):
    """Same input -> same explanation."""
    verification = VerificationContext(
        confidence_pct=100,
        last_verified_at=datetime.now(timezone.utc),
        verification_source="wazuh",
        connector_health="healthy",
        verification_status="verified",
        data_age_description="Checked 2 minutes ago",
        verification_method="Live API check"
    )
    
    exp1 = engine.build_explanation(mock_moment, "fail", verification, [])
    exp2 = engine.build_explanation(mock_moment, "fail", verification, [])
    
    assert exp1.business_label == exp2.business_label
    assert exp1.what_it_means == exp2.what_it_means
    assert exp1.why_it_matters == exp2.why_it_matters
    assert exp1.status == "fail"

def test_failed_finding(engine, mock_moment):
    """Failed deterministic finding produces a failed explanation."""
    verification = VerificationContext(
        confidence_pct=100,
        last_verified_at=datetime.now(timezone.utc),
        verification_source="wazuh",
        connector_health="healthy",
        verification_status="verified",
        data_age_description="Checked 2 minutes ago",
        verification_method="Live API check"
    )
    
    exp = engine.build_explanation(mock_moment, "fail", verification, [])
    assert exp.status == "fail"
    assert exp.evidence_state == "verified"
    assert exp.what_to_do_next == "Review the technical details and address the security gap."

def test_unknown_finding(engine, mock_moment):
    """Unknown evidence produces an unknown/unavailable explanation."""
    verification = VerificationContext(
        confidence_pct=0,
        last_verified_at=None,
        verification_source="wazuh",
        connector_health="unreachable",
        verification_status="unverified",
        data_age_description="Unknown",
        verification_method="Live API check"
    )
    
    exp = engine.build_explanation(mock_moment, "unknown", verification, [])
    assert exp.status == "unknown"
    assert exp.evidence_state == "unavailable"
    assert "could not find evidence" in exp.what_it_means
    assert "Check the connected security system" in exp.what_to_do_next

def test_stale_finding(engine, mock_moment):
    """Stale evidence produces a stale explanation."""
    verification = VerificationContext(
        confidence_pct=0,
        last_verified_at=None,
        verification_source="wazuh",
        connector_health="degraded",
        verification_status="stale",
        data_age_description="Stale evidence: last sync was 4 days ago",
        verification_method="Live API check"
    )
    
    exp = engine.build_explanation(mock_moment, "unknown", verification, [])
    assert exp.status == "unknown"
    assert exp.evidence_state == "stale"
    assert "out of date and can no longer be trusted" in exp.what_it_means
    assert "Check the connected security system" in exp.what_to_do_next

def test_no_evidence_never_healthy(engine, mock_moment):
    """No evidence never produces healthy/verified/100%."""
    verification = VerificationContext(
        confidence_pct=0,
        last_verified_at=None,
        verification_source="wazuh",
        connector_health="unreachable",
        verification_status="unverified",
        data_age_description="Missing data",
        verification_method="Live API check"
    )
    
    # Even if accidentally passed "pass" (which shouldn't happen with the ReadinessEngine invariant),
    # the evidence_state must accurately reflect reality.
    exp = engine.build_explanation(mock_moment, "pass", verification, [])
    
    assert exp.evidence_state == "unavailable"
    assert exp.status == "pass" # Status is passed down, but evidence state guards it
    assert "healthy" not in exp.what_it_means.lower()
    assert "verified" not in exp.what_it_means.lower()
    assert "could not find evidence" in exp.what_it_means

def test_tenant_isolation(engine, mock_moment):
    """Ensure no org specific info is leaked (explanations are static templates)."""
    verification = VerificationContext(
        confidence_pct=100,
        last_verified_at=datetime.now(timezone.utc),
        verification_source="wazuh",
        connector_health="healthy",
        verification_status="verified",
        data_age_description="Checked 2 minutes ago",
        verification_method="Live API check"
    )
    
    exp = engine.build_explanation(mock_moment, "fail", verification, [])
    assert "org-1" not in exp.what_it_means
    assert "org-1" not in exp.why_it_matters
    assert "org-1" not in exp.business_label

def test_action_mapping(engine, mock_moment):
    """If a deterministic remediation action exists, the explanation references it."""
    verification = VerificationContext(
        confidence_pct=100,
        last_verified_at=datetime.now(timezone.utc),
        verification_source="wazuh",
        connector_health="healthy",
        verification_status="verified",
        data_age_description="Checked 2 minutes ago",
        verification_method="Live API check"
    )
    
    action = ActionCard(
        action_id="a-1",
        problem="Problem",
        why_it_matters="Why",
        recommended_action="Click the fix button now.",
        can_be_undone=True,
        estimated_time_minutes=5,
        fix_now_available=True,
        category="device",
        approval_needed=False,
        required_permissions=[],
        success_message="Fixed."
    )
    
    exp = engine.build_explanation(mock_moment, "fail", verification, [action])
    assert exp.what_to_do_next == "Click the fix button now."
