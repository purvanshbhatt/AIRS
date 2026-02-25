"""
Governance Expansion — Unit Tests

Tests all governance modules with deterministic, LLM-free logic:
  1. Compliance Engine (9 rules, all combinations)
  2. Audit Calendar Service (CRUD + enrich + forecast)
  3. Tech Stack Service (CRUD + risk classification + summary)
  4. Uptime Tier Analysis (gap analysis logic)
  5. API Integration (governance endpoints via TestClient)

Target: ≥ 95% rule coverage across all governance engines.
"""

import json
import os
import uuid
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone

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
from app.models.finding import Finding, Severity
from app.models.audit_calendar import AuditCalendarEntry, AuditType
from app.models.tech_stack import TechStackItem, LtsStatus
from app.services.governance.compliance_engine import get_applicable_frameworks
from app.services.governance.audit_calendar import AuditCalendarService, FRAMEWORK_KEYWORDS
from app.services.governance.tech_stack import TechStackService
from app.services.governance import lifecycle_engine
from app.models.framework_registry import FrameworkRegistry, FrameworkCategory
from app.schemas.audit_calendar import AuditCalendarCreate, AuditCalendarUpdate
from app.schemas.tech_stack import TechStackItemCreate, TechStackItemUpdate

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


def _make_finding(db: Session, assessment_id: str, severity: Severity, title: str) -> Finding:
    """Create a finding attached to the given assessment."""
    f = Finding(
        id=str(uuid.uuid4()),
        assessment_id=assessment_id,
        domain_name="test",
        title=title,
        description=f"Finding: {title}",
        severity=severity,
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _make_audit_entry(db: Session, org_id: str, framework: str = "HIPAA") -> AuditCalendarEntry:
    """Create an audit calendar entry 60 days from now."""
    svc = AuditCalendarService(db, org_id)
    entry = svc.create(AuditCalendarCreate(
        framework=framework,
        audit_date=datetime.now(timezone.utc) + timedelta(days=60),
    ))
    return entry


# ═════════════════════════════════════════════════════════════════════
# 1. COMPLIANCE ENGINE — RULE-BY-RULE
# ═════════════════════════════════════════════════════════════════════

class TestComplianceEngineRules:
    """Verify each deterministic rule fires exactly when expected."""

    def test_baseline_no_flags_tech_gives_soc2(self, db):
        """Industry=technology → SOC 2 recommended only."""
        org = _make_org(db, industry="technology")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert names == ["SOC 2 Type II"]
        assert fws[0].mandatory is False

    def test_baseline_no_flags_non_tech(self, db):
        """No flags + non-tech industry → zero frameworks."""
        org = _make_org(db, industry="retail")
        fws = get_applicable_frameworks(org)
        assert fws == []

    # ── HIPAA ────────────────────────────────────────────────────────
    def test_phi_triggers_hipaa(self, db):
        org = _make_org(db, processes_phi=True, industry="healthcare")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "HIPAA" in names
        hipaa = next(f for f in fws if f.framework == "HIPAA")
        assert hipaa.mandatory is True

    def test_no_phi_no_hipaa(self, db):
        org = _make_org(db, processes_phi=False, industry="healthcare")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "HIPAA" not in names

    # ── CMMC + NIST 800-171 ──────────────────────────────────────────
    def test_dod_triggers_cmmc_and_800_171(self, db):
        org = _make_org(db, handles_dod_data=True, industry="defense")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "CMMC Level 2" in names
        assert "NIST SP 800-171" in names
        cmmc = next(f for f in fws if f.framework == "CMMC Level 2")
        nist = next(f for f in fws if f.framework == "NIST SP 800-171")
        assert cmmc.mandatory is True
        assert nist.mandatory is True

    def test_no_dod_no_cmmc(self, db):
        org = _make_org(db, handles_dod_data=False, industry="defense")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "CMMC Level 2" not in names
        assert "NIST SP 800-171" not in names

    # ── PCI-DSS ──────────────────────────────────────────────────────
    def test_cardholder_triggers_pci(self, db):
        org = _make_org(db, processes_cardholder_data=True, industry="retail")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "PCI-DSS v4.0" in names
        pci = next(f for f in fws if f.framework == "PCI-DSS v4.0")
        assert pci.mandatory is True

    def test_no_cardholder_no_pci(self, db):
        org = _make_org(db, processes_cardholder_data=False, industry="retail")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "PCI-DSS v4.0" not in names

    # ── GDPR ─────────────────────────────────────────────────────────
    def test_pii_eu_triggers_gdpr(self, db):
        org = _make_org(
            db,
            processes_pii=True,
            geo_regions=json.dumps(["US", "EU"]),
            industry="saas",
        )
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "GDPR" in names
        gdpr = next(f for f in fws if f.framework == "GDPR")
        assert gdpr.mandatory is True

    def test_pii_no_eu_gives_privacy_framework(self, db):
        """PII without EU → NIST Privacy Framework (recommended)."""
        org = _make_org(
            db,
            processes_pii=True,
            geo_regions=json.dumps(["US"]),
            industry="retail",
        )
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "NIST Privacy Framework" in names
        assert "GDPR" not in names
        nist_priv = next(f for f in fws if f.framework == "NIST Privacy Framework")
        assert nist_priv.mandatory is False

    def test_pii_eu_no_privacy_framework(self, db):
        """PII + EU → GDPR fires, NIST Privacy does NOT double-fire."""
        org = _make_org(
            db,
            processes_pii=True,
            geo_regions=json.dumps(["EU"]),
            industry="retail",
        )
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "GDPR" in names
        assert "NIST Privacy Framework" not in names

    # ── SOC 2 ────────────────────────────────────────────────────────
    def test_tech_industry_triggers_soc2(self, db):
        org = _make_org(db, industry="technology")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "SOC 2 Type II" in names
        soc2 = next(f for f in fws if f.framework == "SOC 2 Type II")
        assert soc2.mandatory is False

    def test_saas_industry_triggers_soc2(self, db):
        org = _make_org(db, industry="saas")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "SOC 2 Type II" in names

    def test_software_industry_triggers_soc2(self, db):
        org = _make_org(db, industry="software")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "SOC 2 Type II" in names

    def test_non_tech_no_soc2(self, db):
        org = _make_org(db, industry="retail")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "SOC 2 Type II" not in names

    # ── NIST AI RMF ──────────────────────────────────────────────────
    def test_ai_production_triggers_ai_rmf(self, db):
        org = _make_org(db, uses_ai_in_production=True, industry="retail")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "NIST AI RMF" in names
        ai = next(f for f in fws if f.framework == "NIST AI RMF")
        assert ai.mandatory is False

    def test_no_ai_no_rmf(self, db):
        org = _make_org(db, uses_ai_in_production=False, industry="retail")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "NIST AI RMF" not in names

    # ── NIST CSF + FFIEC ─────────────────────────────────────────────
    def test_financial_triggers_csf_and_ffiec(self, db):
        org = _make_org(db, financial_services=True, industry="finance")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "NIST CSF 2.0" in names
        assert "FFIEC IT Handbook" in names
        csf = next(f for f in fws if f.framework == "NIST CSF 2.0")
        ffiec = next(f for f in fws if f.framework == "FFIEC IT Handbook")
        assert csf.mandatory is True
        assert ffiec.mandatory is True

    def test_no_financial_no_csf(self, db):
        org = _make_org(db, financial_services=False, industry="retail")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "NIST CSF 2.0" not in names
        assert "FFIEC IT Handbook" not in names

    # ── FedRAMP ──────────────────────────────────────────────────────
    def test_gov_contractor_triggers_fedramp(self, db):
        org = _make_org(db, government_contractor=True, industry="consulting")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "FedRAMP" in names
        fedramp = next(f for f in fws if f.framework == "FedRAMP")
        assert fedramp.mandatory is False

    def test_no_gov_contractor_no_fedramp(self, db):
        org = _make_org(db, government_contractor=False, industry="consulting")
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "FedRAMP" not in names


class TestComplianceEngineCombinations:
    """Test multi-flag scenarios and edge cases."""

    def test_full_profile_all_flags(self, db):
        """Org with every flag set → maximum framework output."""
        org = _make_org(
            db,
            industry="technology",
            processes_pii=True,
            processes_phi=True,
            processes_cardholder_data=True,
            handles_dod_data=True,
            uses_ai_in_production=True,
            government_contractor=True,
            financial_services=True,
            geo_regions=json.dumps(["US", "EU"]),
        )
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "HIPAA" in names
        assert "CMMC Level 2" in names
        assert "NIST SP 800-171" in names
        assert "PCI-DSS v4.0" in names
        assert "GDPR" in names
        assert "SOC 2 Type II" in names
        assert "NIST AI RMF" in names
        assert "NIST CSF 2.0" in names
        assert "FFIEC IT Handbook" in names
        assert "FedRAMP" in names
        # PII+EU → GDPR, NOT Privacy Framework
        assert "NIST Privacy Framework" not in names
        assert len(fws) == 10

    def test_empty_profile(self, db):
        """Entirely empty profile, non-tech industry → zero frameworks."""
        org = _make_org(db, industry="other", geo_regions=None)
        fws = get_applicable_frameworks(org)
        assert fws == []

    def test_healthcare_fintech(self, db):
        """PHI + financial → HIPAA + NIST CSF + FFIEC."""
        org = _make_org(
            db,
            processes_phi=True,
            financial_services=True,
            industry="fintech",
        )
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "HIPAA" in names
        assert "NIST CSF 2.0" in names
        assert "FFIEC IT Handbook" in names
        assert len(fws) == 3

    def test_dod_with_ai_gov_contractor(self, db):
        """DoD + AI + GovCon → CMMC + 800-171 + AI RMF + FedRAMP."""
        org = _make_org(
            db,
            handles_dod_data=True,
            uses_ai_in_production=True,
            government_contractor=True,
            industry="defense",
        )
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "CMMC Level 2" in names
        assert "NIST SP 800-171" in names
        assert "NIST AI RMF" in names
        assert "FedRAMP" in names
        assert len(fws) == 4

    def test_geo_regions_invalid_json(self, db):
        """Invalid geo_regions JSON → treated as empty, no GDPR."""
        org = _make_org(
            db,
            processes_pii=True,
            geo_regions="not-valid-json",
            industry="retail",
        )
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        # Invalid JSON → empty list → no EU → Privacy Framework only
        assert "NIST Privacy Framework" in names
        assert "GDPR" not in names

    def test_geo_regions_none(self, db):
        """geo_regions=None → no GDPR."""
        org = _make_org(
            db,
            processes_pii=True,
            geo_regions=None,
            industry="retail",
        )
        fws = get_applicable_frameworks(org)
        names = [f.framework for f in fws]
        assert "NIST Privacy Framework" in names
        assert "GDPR" not in names

    def test_reference_urls_populated(self, db):
        """All frameworks have reference_url set."""
        org = _make_org(
            db,
            industry="technology",
            processes_pii=True,
            processes_phi=True,
            processes_cardholder_data=True,
            handles_dod_data=True,
            uses_ai_in_production=True,
            government_contractor=True,
            financial_services=True,
            geo_regions=json.dumps(["EU"]),
        )
        fws = get_applicable_frameworks(org)
        for f in fws:
            assert f.reference_url is not None
            assert f.reference_url.startswith("https://")


# ═════════════════════════════════════════════════════════════════════
# 2. AUDIT CALENDAR SERVICE
# ═════════════════════════════════════════════════════════════════════

class TestAuditCalendarCRUD:
    """Test CRUD operations on AuditCalendarService."""

    def _setup(self, db):
        org = _make_org(db)
        svc = AuditCalendarService(db, org.id)
        return org, svc

    def test_create_entry(self, db):
        org, svc = self._setup(db)
        data = AuditCalendarCreate(
            framework="SOC 2 Type II",
            audit_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            audit_type="external",
            reminder_days_before=90,
        )
        entry = svc.create(data)
        assert entry.id is not None
        assert entry.framework == "SOC 2 Type II"
        assert entry.org_id == org.id

    def test_get_entry(self, db):
        org, svc = self._setup(db)
        data = AuditCalendarCreate(
            framework="HIPAA",
            audit_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
            audit_type="internal",
        )
        created = svc.create(data)
        fetched = svc.get(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.framework == "HIPAA"

    def test_get_nonexistent_returns_none(self, db):
        _, svc = self._setup(db)
        assert svc.get("nonexistent-id") is None

    def test_list_all(self, db):
        org, svc = self._setup(db)
        for fw in ["SOC 2", "HIPAA", "PCI-DSS"]:
            svc.create(AuditCalendarCreate(
                framework=fw,
                audit_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            ))
        entries = svc.list_all()
        assert len(entries) == 3

    def test_list_empty(self, db):
        _, svc = self._setup(db)
        assert svc.list_all() == []

    def test_update_entry(self, db):
        _, svc = self._setup(db)
        entry = svc.create(AuditCalendarCreate(
            framework="SOC 2",
            audit_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        ))
        updated = svc.update(entry.id, AuditCalendarUpdate(notes="Updated note"))
        assert updated is not None
        assert updated.notes == "Updated note"

    def test_update_nonexistent_returns_none(self, db):
        _, svc = self._setup(db)
        result = svc.update("nope", AuditCalendarUpdate(notes="x"))
        assert result is None

    def test_delete_entry(self, db):
        _, svc = self._setup(db)
        entry = svc.create(AuditCalendarCreate(
            framework="SOC 2",
            audit_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        ))
        assert svc.delete(entry.id) is True
        assert svc.get(entry.id) is None

    def test_delete_nonexistent_returns_false(self, db):
        _, svc = self._setup(db)
        assert svc.delete("nope") is False

    def test_tenant_isolation(self, db):
        """Entries from org A are not visible to org B's service."""
        org_a = _make_org(db, name="Org A")
        org_b = _make_org(db, name="Org B")
        svc_a = AuditCalendarService(db, org_a.id)
        svc_b = AuditCalendarService(db, org_b.id)

        entry = svc_a.create(AuditCalendarCreate(
            framework="SOC 2",
            audit_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        ))
        assert svc_a.get(entry.id) is not None
        assert svc_b.get(entry.id) is None
        assert len(svc_b.list_all()) == 0


class TestAuditCalendarEnrich:
    """Test enrich_response computed fields."""

    def test_future_audit_is_upcoming_within_reminder(self, db):
        org = _make_org(db)
        svc = AuditCalendarService(db, org.id)
        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        entry = svc.create(AuditCalendarCreate(
            framework="SOC 2",
            audit_date=future_date,
            reminder_days_before=90,
        ))
        enriched = svc.enrich_response(entry)
        assert enriched.is_upcoming is True
        assert enriched.days_until_audit > 0

    def test_future_audit_not_upcoming_outside_reminder(self, db):
        org = _make_org(db)
        svc = AuditCalendarService(db, org.id)
        far_future = datetime.now(timezone.utc) + timedelta(days=365)
        entry = svc.create(AuditCalendarCreate(
            framework="SOC 2",
            audit_date=far_future,
            reminder_days_before=90,
        ))
        enriched = svc.enrich_response(entry)
        assert enriched.is_upcoming is False

    def test_past_audit_days_until_is_zero(self, db):
        org = _make_org(db)
        svc = AuditCalendarService(db, org.id)
        past_date = datetime.now(timezone.utc) - timedelta(days=30)
        entry = svc.create(AuditCalendarCreate(
            framework="HIPAA",
            audit_date=past_date,
        ))
        enriched = svc.enrich_response(entry)
        assert enriched.days_until_audit == 0


class TestAuditForecast:
    """Test forecast engine logic."""

    def _setup_with_findings(self, db, framework, findings_spec):
        """
        findings_spec: list of (title, severity) tuples.
        Returns (entry, svc).
        """
        org = _make_org(db)
        svc = AuditCalendarService(db, org.id)

        # Create assessment for findings
        assessment = Assessment(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            status=AssessmentStatus.COMPLETED,
        )
        db.add(assessment)
        db.commit()

        for title, severity in findings_spec:
            finding = Finding(
                id=str(uuid.uuid4()),
                assessment_id=assessment.id,
                domain_name="test",
                title=title,
                description=f"Finding about {title}",
                severity=severity,
            )
            db.add(finding)
        db.commit()

        entry = svc.create(AuditCalendarCreate(
            framework=framework,
            audit_date=datetime.now(timezone.utc) + timedelta(days=60),
        ))
        return entry, svc

    def test_forecast_critical_risk(self, db):
        """3+ critical/high related findings → critical risk."""
        entry, svc = self._setup_with_findings(db, "SOC 2 Type II", [
            ("SOC trust principle violation", Severity.CRITICAL),
            ("SOC2 availability gap", Severity.HIGH),
            ("SOC confidentiality control failure", Severity.HIGH),
        ])
        forecast = svc.get_forecast(entry)
        assert forecast.risk_level == "critical"
        assert forecast.critical_high_count == 3

    def test_forecast_high_risk(self, db):
        """1-2 critical/high related findings → high risk."""
        entry, svc = self._setup_with_findings(db, "SOC 2", [
            ("SOC availability deficiency", Severity.HIGH),
            ("SOC trust anomaly", Severity.MEDIUM),
        ])
        forecast = svc.get_forecast(entry)
        assert forecast.risk_level == "high"
        assert forecast.critical_high_count == 1

    def test_forecast_medium_risk(self, db):
        """2+ related findings but no critical/high → medium."""
        entry, svc = self._setup_with_findings(db, "SOC 2", [
            ("SOC test finding low", Severity.LOW),
            ("SOC another test finding low", Severity.LOW),
            ("SOC third test finding", Severity.MEDIUM),
        ])
        forecast = svc.get_forecast(entry)
        assert forecast.risk_level == "medium"
        assert forecast.critical_high_count == 0
        assert forecast.related_findings_count >= 2

    def test_forecast_low_risk(self, db):
        """No related findings → low risk."""
        entry, svc = self._setup_with_findings(db, "HIPAA", [
            ("Unrelated networking issue", Severity.LOW),
        ])
        forecast = svc.get_forecast(entry)
        assert forecast.risk_level == "low"
        assert forecast.related_findings_count == 0

    def test_forecast_critical_when_imminent(self, db):
        """Any critical/high + audit < 30 days → critical."""
        org = _make_org(db)
        svc = AuditCalendarService(db, org.id)
        assessment = Assessment(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            status=AssessmentStatus.COMPLETED,
        )
        db.add(assessment)
        db.commit()
        finding = Finding(
            id=str(uuid.uuid4()),
            assessment_id=assessment.id,
            domain_name="test",
            title="SOC availability gap",
            severity=Severity.HIGH,
        )
        db.add(finding)
        db.commit()

        entry = svc.create(AuditCalendarCreate(
            framework="SOC 2",
            audit_date=datetime.now(timezone.utc) + timedelta(days=15),
        ))
        forecast = svc.get_forecast(entry)
        assert forecast.risk_level == "critical"

    def test_forecast_recommendation_text(self, db):
        """Verify recommendation strings are set per risk level."""
        entry, svc = self._setup_with_findings(db, "HIPAA", [
            ("HIPAA phi breach risk", Severity.CRITICAL),
            ("HIPAA health record exposure", Severity.HIGH),
            ("HIPAA medical data handling", Severity.HIGH),
        ])
        forecast = svc.get_forecast(entry)
        assert "⚠️" in forecast.recommendation
        assert "HIPAA" in forecast.recommendation

    def test_framework_keywords_complete(self):
        """Verify all mapped frameworks have keywords."""
        for fw, kws in FRAMEWORK_KEYWORDS.items():
            assert isinstance(kws, list)
            assert len(kws) > 0, f"Framework {fw} has no keywords"


# ═════════════════════════════════════════════════════════════════════
# 3. TECH STACK SERVICE
# ═════════════════════════════════════════════════════════════════════

class TestTechStackCRUD:
    """Test CRUD operations on TechStackService."""

    def _setup(self, db):
        org = _make_org(db)
        svc = TechStackService(db, org.id)
        return org, svc

    def test_create_item(self, db):
        org, svc = self._setup(db)
        data = TechStackItemCreate(
            component_name="Python",
            version="3.13",
            lts_status="active",
            major_versions_behind=0,
            category="Language",
        )
        item = svc.create(data)
        assert item.id is not None
        assert item.component_name == "Python"
        assert item.org_id == org.id

    def test_get_item(self, db):
        _, svc = self._setup(db)
        item = svc.create(TechStackItemCreate(
            component_name="Node.js", version="20", lts_status="lts",
        ))
        fetched = svc.get(item.id)
        assert fetched is not None
        assert fetched.component_name == "Node.js"

    def test_get_nonexistent_returns_none(self, db):
        _, svc = self._setup(db)
        assert svc.get("nope") is None

    def test_list_all(self, db):
        _, svc = self._setup(db)
        for name in ["Python", "Node.js", "PostgreSQL"]:
            svc.create(TechStackItemCreate(
                component_name=name, version="1.0", lts_status="active",
            ))
        items = svc.list_all()
        assert len(items) == 3

    def test_update_item(self, db):
        _, svc = self._setup(db)
        item = svc.create(TechStackItemCreate(
            component_name="React", version="17", lts_status="active",
        ))
        updated = svc.update(item.id, TechStackItemUpdate(version="18"))
        assert updated.version == "18"

    def test_update_nonexistent_returns_none(self, db):
        _, svc = self._setup(db)
        assert svc.update("nope", TechStackItemUpdate(version="x")) is None

    def test_delete_item(self, db):
        _, svc = self._setup(db)
        item = svc.create(TechStackItemCreate(
            component_name="jQuery", version="1.6", lts_status="eol",
        ))
        assert svc.delete(item.id) is True
        assert svc.get(item.id) is None

    def test_delete_nonexistent_returns_false(self, db):
        _, svc = self._setup(db)
        assert svc.delete("nope") is False


class TestTechStackRiskClassification:
    """Verify classify_risk deterministic rules."""

    def _make_item(self, lts_status="active", major_versions_behind=0):
        """Create a mock-like TechStackItem for risk testing."""
        item = MagicMock(spec=TechStackItem)
        item.lts_status = LtsStatus(lts_status)
        item.major_versions_behind = major_versions_behind
        return item

    def test_eol_is_critical(self):
        item = self._make_item(lts_status="eol")
        assert TechStackService.classify_risk(item) == "critical"

    def test_deprecated_is_high(self):
        item = self._make_item(lts_status="deprecated")
        assert TechStackService.classify_risk(item) == "high"

    def test_3_versions_behind_is_high(self):
        item = self._make_item(major_versions_behind=3)
        assert TechStackService.classify_risk(item) == "high"

    def test_5_versions_behind_is_high(self):
        item = self._make_item(major_versions_behind=5)
        assert TechStackService.classify_risk(item) == "high"

    def test_1_version_behind_is_medium(self):
        item = self._make_item(major_versions_behind=1)
        assert TechStackService.classify_risk(item) == "medium"

    def test_2_versions_behind_is_medium(self):
        item = self._make_item(major_versions_behind=2)
        assert TechStackService.classify_risk(item) == "medium"

    def test_current_is_low(self):
        item = self._make_item(lts_status="active", major_versions_behind=0)
        assert TechStackService.classify_risk(item) == "low"

    def test_lts_current_is_low(self):
        item = self._make_item(lts_status="lts", major_versions_behind=0)
        assert TechStackService.classify_risk(item) == "low"

    def test_eol_overrides_version_gap(self):
        """EOL takes precedence even if major_versions_behind=0."""
        item = self._make_item(lts_status="eol", major_versions_behind=0)
        assert TechStackService.classify_risk(item) == "critical"

    def test_deprecated_overrides_version_gap(self):
        """Deprecated takes precedence over version gap of 1."""
        item = self._make_item(lts_status="deprecated", major_versions_behind=1)
        assert TechStackService.classify_risk(item) == "high"


class TestTechStackSummary:
    """Test get_summary aggregation logic."""

    def test_summary_all_current(self, db):
        org = _make_org(db)
        svc = TechStackService(db, org.id)
        svc.create(TechStackItemCreate(
            component_name="Python", version="3.13", lts_status="active",
            major_versions_behind=0,
        ))
        svc.create(TechStackItemCreate(
            component_name="Node.js", version="20", lts_status="lts",
            major_versions_behind=0,
        ))
        summary = svc.get_summary()
        assert summary.eol_count == 0
        assert summary.deprecated_count == 0
        assert summary.outdated_count == 0
        assert "No lifecycle risks" in summary.upgrade_governance_summary

    def test_summary_with_eol(self, db):
        org = _make_org(db)
        svc = TechStackService(db, org.id)
        svc.create(TechStackItemCreate(
            component_name="Python 2.7", version="2.7", lts_status="eol",
            major_versions_behind=5,
        ))
        summary = svc.get_summary()
        assert summary.eol_count == 1
        assert summary.risk_breakdown["critical"] == 1
        assert "EOL" in summary.upgrade_governance_summary

    def test_summary_mixed(self, db):
        org = _make_org(db)
        svc = TechStackService(db, org.id)
        svc.create(TechStackItemCreate(
            component_name="Rails", version="5.2", lts_status="eol",
            major_versions_behind=2,
        ))
        svc.create(TechStackItemCreate(
            component_name="Angular", version="12", lts_status="deprecated",
            major_versions_behind=4,
        ))
        svc.create(TechStackItemCreate(
            component_name="React", version="18", lts_status="active",
            major_versions_behind=0,
        ))
        summary = svc.get_summary()
        assert summary.eol_count == 1
        assert summary.deprecated_count == 1
        assert summary.risk_breakdown["critical"] == 1
        assert summary.risk_breakdown["high"] == 1
        assert summary.risk_breakdown["low"] == 1

    def test_summary_empty_stack(self, db):
        org = _make_org(db)
        svc = TechStackService(db, org.id)
        summary = svc.get_summary()
        assert summary.eol_count == 0
        assert summary.deprecated_count == 0
        assert "No lifecycle risks" in summary.upgrade_governance_summary


# ═════════════════════════════════════════════════════════════════════
# 4. UPTIME TIER ANALYSIS (logic extracted from governance.py)
# ═════════════════════════════════════════════════════════════════════

class TestUptimeTierLogic:
    """Test uptime gap analysis logic."""

    TIER_SLAS = {
        "Tier 1": 99.99,
        "Tier 2": 99.9,
        "Tier 3": 99.5,
        "Tier 4": 99.0,
    }

    def _gap_analysis(self, tier, sla_target):
        tier_sla = self.TIER_SLAS.get(tier)
        if not tier_sla or sla_target is None:
            return ("not_configured", None)
        gap = tier_sla - sla_target
        if gap <= 0:
            return ("on_track", round(gap, 4))
        elif gap <= 0.5:
            return ("at_risk", round(gap, 4))
        else:
            return ("unrealistic", round(gap, 4))

    def test_on_track_meets_sla(self):
        status, gap = self._gap_analysis("Tier 2", 99.95)
        assert status == "on_track"
        assert gap <= 0

    def test_on_track_exact_match(self):
        status, gap = self._gap_analysis("Tier 2", 99.9)
        assert status == "on_track"
        assert gap == 0.0

    def test_at_risk_small_gap(self):
        status, gap = self._gap_analysis("Tier 1", 99.6)
        assert status == "at_risk"
        assert 0 < gap <= 0.5

    def test_unrealistic_large_gap(self):
        status, gap = self._gap_analysis("Tier 1", 98.0)
        assert status == "unrealistic"
        assert gap > 0.5

    def test_not_configured_no_tier(self):
        status, gap = self._gap_analysis("Unknown", 99.9)
        assert status == "not_configured"
        assert gap is None

    def test_not_configured_no_sla(self):
        status, gap = self._gap_analysis("Tier 1", None)
        assert status == "not_configured"
        assert gap is None

    def test_tier_3_on_track(self):
        status, gap = self._gap_analysis("Tier 3", 99.5)
        assert status == "on_track"

    def test_tier_4_at_risk(self):
        status, gap = self._gap_analysis("Tier 4", 98.6)
        assert status == "at_risk"

    def test_over_provision_tier_3_targeting_9999(self):
        """Tier 3 org targeting 99.99% is on_track (tier SLA 99.5%)."""
        status, gap = self._gap_analysis("Tier 3", 99.99)
        assert status == "on_track"
        assert gap < 0  # surplus


# ═════════════════════════════════════════════════════════════════════
# 5. API INTEGRATION TESTS (via TestClient)
# ═════════════════════════════════════════════════════════════════════

class TestGovernanceAPI:
    """Integration tests for governance API endpoints."""

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

    def _create_org(self):
        org = _make_org(self.db, industry="technology", owner_uid="dev-user")
        return org

    def test_get_profile_empty(self):
        org = self._create_org()
        resp = self.client.get(f"/api/governance/{org.id}/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["org_id"] == org.id
        assert data["processes_pii"] is False

    def test_update_profile(self):
        org = self._create_org()
        resp = self.client.put(
            f"/api/governance/{org.id}/profile",
            json={
                "revenue_band": "$10M-$50M",
                "processes_pii": True,
                "geo_regions": ["US", "EU"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["revenue_band"] == "$10M-$50M"
        assert data["processes_pii"] is True
        assert data["geo_regions"] == ["US", "EU"]

    def test_applicable_frameworks_endpoint(self):
        org = _make_org(self.db, industry="technology", processes_phi=True, owner_uid="dev-user")
        resp = self.client.get(f"/api/governance/{org.id}/applicable-frameworks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        names = [f["framework"] for f in data["frameworks"]]
        assert "HIPAA" in names

    def test_uptime_analysis_not_configured(self):
        org = self._create_org()
        resp = self.client.get(f"/api/governance/{org.id}/uptime-analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_configured"

    def test_uptime_analysis_on_track(self):
        org = _make_org(
            self.db,
            application_tier="Tier 2",
            sla_target=99.95,
            owner_uid="dev-user",
        )
        resp = self.client.get(f"/api/governance/{org.id}/uptime-analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "on_track"

    def test_profile_404_unknown_org(self):
        resp = self.client.get("/api/governance/nonexistent/profile")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# 10. AUDIT READINESS SCORE (Item 4)
# ═══════════════════════════════════════════════════════════════════════

class TestAuditReadinessScore:
    """Test the audit_readiness_score computation in forecast."""

    def test_score_perfect_no_findings(self, db):
        """No related findings → score = 100."""
        org = _make_org(db)
        entry = _make_audit_entry(db, org.id, framework="HIPAA")
        svc = AuditCalendarService(db, org.id)
        forecast = svc.get_forecast(entry)
        assert forecast.audit_readiness_score == 100
        assert forecast.risk_level == "low"

    def test_score_with_critical(self, db):
        """Critical findings reduce score by 15 each."""
        org = _make_org(db)
        assessment = _make_assessment(db, org.id)
        _make_finding(db, assessment.id, severity=Severity.CRITICAL, title="HIPAA breach risk")
        entry = _make_audit_entry(db, org.id, framework="HIPAA")
        svc = AuditCalendarService(db, org.id)
        forecast = svc.get_forecast(entry)
        assert forecast.audit_readiness_score == 85  # 100 - 15

    def test_score_with_high(self, db):
        """High findings reduce score by 8 each."""
        org = _make_org(db)
        assessment = _make_assessment(db, org.id)
        _make_finding(db, assessment.id, severity=Severity.HIGH, title="HIPAA access control gap")
        entry = _make_audit_entry(db, org.id, framework="HIPAA")
        svc = AuditCalendarService(db, org.id)
        forecast = svc.get_forecast(entry)
        assert forecast.audit_readiness_score == 92  # 100 - 8

    def test_score_with_medium(self, db):
        """Medium findings reduce score by 3 each."""
        org = _make_org(db)
        assessment = _make_assessment(db, org.id)
        _make_finding(db, assessment.id, severity=Severity.MEDIUM, title="HIPAA training gap")
        entry = _make_audit_entry(db, org.id, framework="HIPAA")
        svc = AuditCalendarService(db, org.id)
        forecast = svc.get_forecast(entry)
        assert forecast.audit_readiness_score == 97  # 100 - 3

    def test_score_mixed_severities(self, db):
        """Mixed severities: 100 - 15 - 8 - 3 = 74."""
        org = _make_org(db)
        assessment = _make_assessment(db, org.id)
        _make_finding(db, assessment.id, severity=Severity.CRITICAL, title="HIPAA critical issue")
        _make_finding(db, assessment.id, severity=Severity.HIGH, title="HIPAA high issue")
        _make_finding(db, assessment.id, severity=Severity.MEDIUM, title="HIPAA medium issue")
        entry = _make_audit_entry(db, org.id, framework="HIPAA")
        svc = AuditCalendarService(db, org.id)
        forecast = svc.get_forecast(entry)
        assert forecast.audit_readiness_score == 74

    def test_score_floor_at_zero(self, db):
        """Score should never go below 0."""
        org = _make_org(db)
        assessment = _make_assessment(db, org.id)
        for i in range(8):
            _make_finding(db, assessment.id, severity=Severity.CRITICAL, title=f"HIPAA critical {i}")
        entry = _make_audit_entry(db, org.id, framework="HIPAA")
        svc = AuditCalendarService(db, org.id)
        forecast = svc.get_forecast(entry)
        # 100 - 8*15 = -20, clamped to 0
        assert forecast.audit_readiness_score == 0

    def test_score_in_forecast_response_schema(self, db):
        """Verify audit_readiness_score is returned in the forecast schema."""
        org = _make_org(db)
        entry = _make_audit_entry(db, org.id, framework="SOC 2")
        svc = AuditCalendarService(db, org.id)
        forecast = svc.get_forecast(entry)
        assert hasattr(forecast, "audit_readiness_score")
        assert isinstance(forecast.audit_readiness_score, int)
        assert 0 <= forecast.audit_readiness_score <= 100


# ═══════════════════════════════════════════════════════════════════════
# 11. LIFECYCLE ENGINE (Item 5)
# ═══════════════════════════════════════════════════════════════════════

class TestLifecycleEngine:
    """Test the static lifecycle intelligence engine."""

    def test_python_eol(self):
        """Python 3.8 is EOL."""
        info = lifecycle_engine.get_version_status("python", "3.8")
        assert info is not None
        assert info["status"] == "eol"

    def test_python_active(self):
        """Python 3.12 is active."""
        info = lifecycle_engine.get_version_status("python", "3.12")
        assert info is not None
        assert info["status"] == "active"

    def test_node_lts(self):
        """Node 20 is LTS."""
        info = lifecycle_engine.get_version_status("node", "20")
        assert info is not None
        assert info["status"] == "lts"

    def test_node_alias(self):
        """nodejs alias resolves to node."""
        info = lifecycle_engine.get_version_status("nodejs", "20")
        assert info is not None
        assert info["status"] == "lts"

    def test_postgres_alias(self):
        """postgres alias resolves to postgresql."""
        info = lifecycle_engine.get_version_status("postgres", "16")
        assert info is not None
        assert info["status"] == "active"

    def test_unknown_tech(self):
        """Unknown technology returns None."""
        assert lifecycle_engine.get_version_status("cobol", "85") is None

    def test_unknown_version(self):
        """Unknown version returns None."""
        assert lifecycle_engine.get_version_status("python", "2.7") is None

    def test_is_eol_true(self):
        """Python 3.8 is EOL."""
        assert lifecycle_engine.is_eol("python", "3.8") is True

    def test_is_eol_false(self):
        """Python 3.12 is not EOL."""
        assert lifecycle_engine.is_eol("python", "3.12") is False

    def test_eol_date(self):
        """Get EOL date for a version."""
        d = lifecycle_engine.get_eol_date("python", "3.8")
        assert d == "2024-10-01"

    def test_eol_date_unknown(self):
        """Unknown version has no EOL date."""
        assert lifecycle_engine.get_eol_date("python", "2.7") is None

    def test_version_major_minor_match(self):
        """Version 3.11.5 should resolve to 3.11 config entry."""
        info = lifecycle_engine.get_version_status("python", "3.11.5")
        assert info is not None
        assert info["status"] == "active"

    def test_version_major_only_match(self):
        """Version 18.17.0 for Node matches major 18."""
        info = lifecycle_engine.get_version_status("node", "18.17.0")
        assert info is not None
        assert info["status"] == "lts"

    def test_supported_technologies(self):
        """Should list at least 8 technologies."""
        techs = lifecycle_engine.get_supported_technologies()
        assert len(techs) >= 8
        assert "python" in techs
        assert "node" in techs

    def test_get_technology_versions(self):
        """Get all version data for python."""
        versions = lifecycle_engine.get_technology_versions("python")
        assert versions is not None
        assert "3.8" in versions
        assert "3.12" in versions

    def test_days_until_eol(self):
        """days_until_eol returns int for known versions."""
        days = lifecycle_engine.days_until_eol("python", "3.8")
        assert isinstance(days, int)
        # Already past EOL, should be negative
        assert days < 0

    def test_dotnet_alias(self):
        """.net alias resolves to dotnet."""
        info = lifecycle_engine.get_version_status(".net", "8.0")
        assert info is not None
        assert info["status"] == "lts"

    def test_k8s_alias(self):
        """k8s alias resolves to kubernetes."""
        info = lifecycle_engine.get_version_status("k8s", "1.30")
        assert info is not None
        assert info["status"] == "active"


# ═══════════════════════════════════════════════════════════════════════
# 12. UPTIME TIER ENHANCEMENTS (Item 6)
# ═══════════════════════════════════════════════════════════════════════

class TestUptimeTierEnhancements:
    """Test over-provision, SOC 2 CC7 tagging, and tier normalization."""

    def test_tier_normalization(self):
        """tier_1 → Tier 1 normalization via TIER_NORMALIZE."""
        from app.api.governance import TIER_NORMALIZE
        assert TIER_NORMALIZE["tier_1"] == "Tier 1"
        assert TIER_NORMALIZE["tier_2"] == "Tier 2"
        assert TIER_NORMALIZE["tier_3"] == "Tier 3"
        assert TIER_NORMALIZE["tier_4"] == "Tier 4"

    def test_over_provision_detection(self, db):
        """SLA target well above tier requirement triggers over-provision."""
        # Tier 4 SLA = 99.0, target = 99.99 → gap = 99.0 - 99.99 = -0.99 < -0.5
        org = _make_org(db, application_tier="tier_4", sla_target=99.99, owner_uid="dev-user")
        from app.api.governance import TIER_SLAS, TIER_NORMALIZE
        tier = TIER_NORMALIZE.get(org.application_tier, org.application_tier)
        tier_sla = TIER_SLAS.get(tier)
        gap = tier_sla - org.sla_target
        assert gap < -0.5  # Over-provisioned

    def test_soc2_cc7_tier1(self):
        """Tier 1 triggers SOC 2 CC7 applicability."""
        from app.api.governance import SOC2_CC7_TIERS
        assert "Tier 1" in SOC2_CC7_TIERS
        assert "Tier 2" in SOC2_CC7_TIERS
        assert "Tier 3" not in SOC2_CC7_TIERS

    def test_uptime_schema_new_fields(self):
        """UptimeTierAnalysis schema has new fields."""
        from app.schemas.organization import UptimeTierAnalysis
        fields = UptimeTierAnalysis.model_fields
        assert "over_provisioned" in fields
        assert "cost_warning" in fields
        assert "soc2_cc7_applicable" in fields
        assert "soc2_cc7_note" in fields

    def test_tier4_support(self):
        """Schema now supports tier_4."""
        from app.schemas.organization import OrganizationProfileUpdate
        # Should not raise validation error
        update = OrganizationProfileUpdate(application_tier="tier_4")
        assert update.application_tier == "tier_4"

    def test_over_provision_api(self, db):
        """API returns over_provisioned flag when target exceeds tier."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.database import get_db

        def override():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override
        try:
            client = TestClient(app)
            # Tier 4 SLA = 99.0, target 99.99 → gap = -0.99 → over-provisioned
            org = _make_org(db, application_tier="Tier 4", sla_target=99.99, owner_uid="dev-user")
            resp = client.get(f"/api/governance/{org.id}/uptime-analysis")
            assert resp.status_code == 200
            data = resp.json()
            assert data["over_provisioned"] is True
            assert data["cost_warning"] is not None
            assert data["status"] == "over_provisioned"
        finally:
            app.dependency_overrides.clear()

    def test_soc2_cc7_in_api_tier1(self, db):
        """API returns SOC 2 CC7 note for Tier 1."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.database import get_db

        def override():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override
        try:
            client = TestClient(app)
            org = _make_org(db, application_tier="Tier 1", sla_target=99.99, owner_uid="dev-user")
            resp = client.get(f"/api/governance/{org.id}/uptime-analysis")
            assert resp.status_code == 200
            data = resp.json()
            assert data["soc2_cc7_applicable"] is True
            assert "CC7" in data["soc2_cc7_note"]
        finally:
            app.dependency_overrides.clear()

    def test_soc2_cc7_not_applicable_tier3(self, db):
        """Tier 3 does NOT trigger SOC 2 CC7."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.database import get_db

        def override():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override
        try:
            client = TestClient(app)
            org = _make_org(db, application_tier="Tier 3", sla_target=99.5, owner_uid="dev-user")
            resp = client.get(f"/api/governance/{org.id}/uptime-analysis")
            assert resp.status_code == 200
            data = resp.json()
            assert data["soc2_cc7_applicable"] is False
            assert data["soc2_cc7_note"] is None
        finally:
            app.dependency_overrides.clear()

    def test_normalized_tier_api(self, db):
        """tier_2 stored in DB is normalized to Tier 2 in response."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.database import get_db

        def override():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override
        try:
            client = TestClient(app)
            org = _make_org(db, application_tier="tier_2", sla_target=99.9, owner_uid="dev-user")
            resp = client.get(f"/api/governance/{org.id}/uptime-analysis")
            assert resp.status_code == 200
            data = resp.json()
            assert data["application_tier"] == "Tier 2"
            assert data["status"] == "on_track"
        finally:
            app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════
# 13. FRAMEWORK REGISTRY (Item 3)
# ═══════════════════════════════════════════════════════════════════════

class TestFrameworkRegistry:
    """Test framework registry model and seed data."""

    def test_model_creation(self, db):
        """Can create a FrameworkRegistry entry."""
        fw = FrameworkRegistry(
            name="Test Framework",
            full_name="Test Compliance Framework",
            category=FrameworkCategory.VOLUNTARY,
            version="1.0",
            description="A test framework.",
            reference_url="https://example.com",
        )
        db.add(fw)
        db.commit()
        db.refresh(fw)
        assert fw.id is not None
        assert fw.name == "Test Framework"
        assert fw.category == FrameworkCategory.VOLUNTARY

    def test_category_enum(self):
        """FrameworkCategory enum has all expected values."""
        assert FrameworkCategory.REGULATORY.value == "regulatory"
        assert FrameworkCategory.CONTRACTUAL.value == "contractual"
        assert FrameworkCategory.VOLUNTARY.value == "voluntary"

    def test_unique_name_constraint(self, db):
        """Framework names must be unique."""
        fw1 = FrameworkRegistry(
            name="Unique FW",
            full_name="Unique Framework",
            category=FrameworkCategory.REGULATORY,
        )
        db.add(fw1)
        db.commit()

        fw2 = FrameworkRegistry(
            name="Unique FW",
            full_name="Duplicate Framework",
            category=FrameworkCategory.REGULATORY,
        )
        db.add(fw2)
        with pytest.raises(Exception):  # IntegrityError
            db.commit()
        db.rollback()

    def test_query_by_category(self, db):
        """Can query frameworks by category."""
        for name, cat in [("FW-A", "regulatory"), ("FW-B", "contractual"), ("FW-C", "voluntary")]:
            fw = FrameworkRegistry(
                name=name,
                full_name=f"Full {name}",
                category=FrameworkCategory(cat),
            )
            db.add(fw)
        db.commit()
        regs = db.query(FrameworkRegistry).filter(
            FrameworkRegistry.category == FrameworkCategory.REGULATORY
        ).all()
        assert len(regs) == 1
        assert regs[0].name == "FW-A"

    def test_schema_response(self, db):
        """FrameworkRegistryResponse schema works with model."""
        from app.schemas.framework_registry import FrameworkRegistryResponse
        fw = FrameworkRegistry(
            name="Schema Test",
            full_name="Schema Test Framework",
            category=FrameworkCategory.CONTRACTUAL,
            version="2.0",
            reference_url="https://example.com",
        )
        db.add(fw)
        db.commit()
        db.refresh(fw)
        resp = FrameworkRegistryResponse.model_validate(fw)
        assert resp.name == "Schema Test"
        assert resp.category == "contractual"

    def test_seed_count(self):
        """Migration seeds 12 canonical frameworks."""
        import importlib.util
        import os
        spec = importlib.util.spec_from_file_location(
            "migration_0013",
            os.path.join(os.path.dirname(__file__), "..", "alembic", "versions", "0013_framework_registry.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert len(mod.SEED_FRAMEWORKS) == 12

    def test_seed_data_completeness(self):
        """All compliance engine frameworks are in the seed data."""
        import importlib.util
        import os
        spec = importlib.util.spec_from_file_location(
            "migration_0013",
            os.path.join(os.path.dirname(__file__), "..", "alembic", "versions", "0013_framework_registry.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        seed_names = {fw["name"] for fw in mod.SEED_FRAMEWORKS}
        expected = {
            "HIPAA", "CMMC Level 2", "NIST SP 800-171", "PCI-DSS v4.0",
            "GDPR", "NIST Privacy Framework", "SOC 2 Type II", "NIST AI RMF",
            "NIST CSF 2.0", "FFIEC IT Handbook", "FedRAMP",
        }
        assert expected.issubset(seed_names)


# ═══════════════════════════════════════════════════════════════════════
# 14. ARCHITECTURE REFACTOR VALIDATION (Item 7)
# ═══════════════════════════════════════════════════════════════════════

class TestArchitectureRefactor:
    """Validate the governance package structure after refactoring."""

    def test_package_imports(self):
        """Can import from app.services.governance package."""
        from app.services.governance import (
            get_applicable_frameworks,
            AuditCalendarService,
            TechStackService,
            get_version_status,
            is_eol,
        )
        assert callable(get_applicable_frameworks)
        assert callable(get_version_status)
        assert callable(is_eol)

    def test_compliance_engine_import(self):
        """Direct import from compliance_engine submodule."""
        from app.services.governance.compliance_engine import get_applicable_frameworks
        assert callable(get_applicable_frameworks)

    def test_audit_calendar_import(self):
        """Direct import from audit_calendar submodule."""
        from app.services.governance.audit_calendar import AuditCalendarService
        assert AuditCalendarService is not None

    def test_tech_stack_import(self):
        """Direct import from tech_stack submodule."""
        from app.services.governance.tech_stack import TechStackService
        assert TechStackService is not None

    def test_lifecycle_engine_import(self):
        """Direct import from lifecycle_engine submodule."""
        from app.services.governance.lifecycle_engine import get_version_status, is_eol
        assert callable(get_version_status)
        assert callable(is_eol)

    def test_framework_registry_model(self):
        """FrameworkRegistry model imported via models package."""
        from app.models import FrameworkRegistry, FrameworkCategory
        assert FrameworkRegistry is not None
        assert FrameworkCategory is not None
