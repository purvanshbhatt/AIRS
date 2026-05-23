"""
Test Suite — TelemetryVerificationService & Governance Engine.

Tests Phase 1–3 of the Deterministic Governance Engine:
  1. FindingProvenance model and FrameworkMappingRegistry model integrity
  2. TelemetryVerificationService SIEM event processing
  3. SHA-256 evidence hash correctness
  4. Idempotent duplicate handling
  5. GHI recomputation with provenance-weighted findings
  6. Structured score-change audit logging

Run with:
  py -m pytest tests/test_telemetry_verification.py -v
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.assessment import Assessment, AssessmentStatus
from app.models.finding import Finding, Severity, FindingStatus
from app.models.organization import Organization
from app.models.finding_provenance import (
    FindingProvenance,
    VerificationSource,
    ProvenanceStatus,
)
from app.models.framework_mapping import FrameworkMappingRegistry
from app.services.telemetry import (
    SIEMEventPayload,
    TelemetryVerificationService,
    VerificationResponse,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def org(db_session) -> Organization:
    """Create a test organization."""
    org = Organization(
        id=str(uuid.uuid4()),
        name="TestCorp",
        owner_uid="test-uid-001",
    )
    db_session.add(org)
    db_session.commit()
    return org


@pytest.fixture
def assessment(db_session, org) -> Assessment:
    """Create a test assessment."""
    a = Assessment(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        owner_uid=org.owner_uid,
        status=AssessmentStatus.COMPLETED,
        overall_score=65.0,
    )
    db_session.add(a)
    db_session.commit()
    return a


@pytest.fixture
def findings(db_session, assessment) -> list:
    """Create test findings with mixed severities."""
    data = [
        ("EDR Coverage Gap", Severity.CRITICAL, "DE.CM-1", "DE"),
        ("MFA Not Enforced", Severity.CRITICAL, "PR.AA-5", "PR"),
        ("Logging Health", Severity.HIGH, "DE.AE-3", "DE"),
        ("Patch Management", Severity.MEDIUM, "PR.PS-1", "PR"),
        ("Policy Documentation", Severity.LOW, "GV.PO-1", "GV"),
    ]
    findings = []
    for title, sev, nist_cat, nist_func in data:
        f = Finding(
            id=str(uuid.uuid4()),
            assessment_id=assessment.id,
            title=title,
            severity=sev,
            status=FindingStatus.OPEN,
            nist_category=nist_cat,
            nist_function=nist_func,
        )
        db_session.add(f)
        findings.append(f)
    db_session.commit()
    return findings


@pytest.fixture
def framework_mapping(db_session, findings) -> FrameworkMappingRegistry:
    """Create a framework mapping for the first finding."""
    mapping = FrameworkMappingRegistry(
        id=str(uuid.uuid4()),
        finding_id=findings[0].id,
        nist_csf_control_id="DE.CM-1",
        nist_ai_rmf_control_id="MAP 1.1",
        mitre_atlas_tactic_id="AML.T0043",
        mapping_version="1.0.0",
    )
    db_session.add(mapping)
    db_session.commit()
    return mapping


def _make_payload(
    source: str = "wazuh",
    alert_id: str | None = None,
    rule_id: str = "DE.CM-1",
    **kwargs,
) -> SIEMEventPayload:
    """Helper to create SIEM event payloads."""
    return SIEMEventPayload(
        source=source,
        alert_id=alert_id or f"alert-{uuid.uuid4().hex[:8]}",
        rule_id=rule_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        raw_data_hash=hashlib.sha256(b"test-raw-data").hexdigest(),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Test: Model Integrity
# ---------------------------------------------------------------------------

class TestModelIntegrity:
    """Tests for FindingProvenance and FrameworkMappingRegistry models."""

    def test_finding_provenance_created_with_defaults(self, db_session, findings):
        """FindingProvenance can be created with correct defaults."""
        prov = FindingProvenance(
            finding_id=findings[0].id,
            evidence_hash="a" * 64,
            verification_source=VerificationSource.SIEM_WAZUH,
            verification_status=ProvenanceStatus.SOC_VERIFIED,
        )
        db_session.add(prov)
        db_session.commit()
        db_session.refresh(prov)

        assert prov.id is not None
        assert len(prov.id) == 36  # UUID format
        assert prov.finding_id == findings[0].id
        assert prov.evidence_hash == "a" * 64
        assert prov.verification_source == VerificationSource.SIEM_WAZUH
        assert prov.verification_status == ProvenanceStatus.SOC_VERIFIED
        assert prov.verified_at is not None

    def test_finding_provenance_unique_finding_id(self, db_session, findings):
        """FindingProvenance enforces unique finding_id (1-to-1)."""
        prov1 = FindingProvenance(
            finding_id=findings[0].id,
            evidence_hash="a" * 64,
        )
        db_session.add(prov1)
        db_session.commit()

        prov2 = FindingProvenance(
            finding_id=findings[0].id,  # Duplicate
            evidence_hash="b" * 64,
        )
        db_session.add(prov2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_framework_mapping_created(self, db_session, findings):
        """FrameworkMappingRegistry can be created with all control IDs."""
        mapping = FrameworkMappingRegistry(
            finding_id=findings[0].id,
            nist_csf_control_id="DE.CM-1",
            nist_ai_rmf_control_id="MAP 1.1",
            mitre_atlas_tactic_id="AML.T0043",
            soc2_control_id="CC6.1",
            iso27001_control_id="A.8.7",
            mapping_version="1.0.0",
        )
        db_session.add(mapping)
        db_session.commit()
        db_session.refresh(mapping)

        assert mapping.finding_id == findings[0].id
        assert mapping.nist_ai_rmf_control_id == "MAP 1.1"
        assert mapping.mitre_atlas_tactic_id == "AML.T0043"
        assert mapping.mapping_version == "1.0.0"

    def test_provenance_relationship_to_finding(self, db_session, findings):
        """FindingProvenance has a backref accessible from Finding."""
        prov = FindingProvenance(
            finding_id=findings[0].id,
            evidence_hash="c" * 64,
            verification_status=ProvenanceStatus.SOC_VERIFIED,
        )
        db_session.add(prov)
        db_session.commit()
        db_session.refresh(findings[0])

        assert findings[0].provenance is not None
        assert findings[0].provenance.evidence_hash == "c" * 64


# ---------------------------------------------------------------------------
# Test: SHA-256 Evidence Hash
# ---------------------------------------------------------------------------

class TestEvidenceHash:
    """Tests for deterministic SHA-256 hash computation."""

    def test_hash_is_deterministic(self, db_session):
        """Same payload must always produce the same hash."""
        payload = SIEMEventPayload(
            source="wazuh",
            alert_id="alert-12345",
            rule_id="DE.CM-1",
            timestamp="2026-05-22T12:00:00Z",
            raw_data_hash="abc123",
        )

        hash1 = TelemetryVerificationService._compute_evidence_hash(payload)
        hash2 = TelemetryVerificationService._compute_evidence_hash(payload)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

    def test_hash_changes_with_different_input(self, db_session):
        """Different payloads must produce different hashes."""
        p1 = SIEMEventPayload(
            source="wazuh", alert_id="alert-1", rule_id="DE.CM-1",
            timestamp="2026-05-22T12:00:00Z", raw_data_hash="abc",
        )
        p2 = SIEMEventPayload(
            source="wazuh", alert_id="alert-2", rule_id="DE.CM-1",
            timestamp="2026-05-22T12:00:00Z", raw_data_hash="abc",
        )

        assert TelemetryVerificationService._compute_evidence_hash(p1) != \
               TelemetryVerificationService._compute_evidence_hash(p2)

    def test_hash_matches_manual_computation(self, db_session):
        """Hash must match independently computed SHA-256."""
        payload = SIEMEventPayload(
            source="splunk", alert_id="SPL-001", rule_id="550",
            timestamp="2026-01-01T00:00:00Z", raw_data_hash="deadbeef",
        )

        # Manually compute expected hash
        canonical = json.dumps(
            {
                "source": "splunk",
                "alert_id": "SPL-001",
                "rule_id": "550",
                "timestamp": "2026-01-01T00:00:00Z",
                "raw_data_hash": "deadbeef",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        assert TelemetryVerificationService._compute_evidence_hash(payload) == expected


# ---------------------------------------------------------------------------
# Test: SIEM Event Processing
# ---------------------------------------------------------------------------

class TestSIEMEventProcessing:
    """Tests for TelemetryVerificationService.process_siem_event()."""

    def test_valid_siem_payload_creates_soc_verified_provenance(
        self, db_session, findings, framework_mapping,
    ):
        """A valid SIEM payload matching a framework mapping creates SOC_VERIFIED provenance."""
        payload = _make_payload(source="wazuh", rule_id="DE.CM-1")

        service = TelemetryVerificationService(db_session)
        result = service.process_siem_event(payload)

        assert result.status == "verified"
        assert result.finding_id == findings[0].id
        assert result.verification_status == "SOC_VERIFIED"
        assert result.evidence_hash is not None
        assert len(result.evidence_hash) == 64

        # Verify DB record
        prov = (
            db_session.query(FindingProvenance)
            .filter(FindingProvenance.finding_id == findings[0].id)
            .first()
        )
        assert prov is not None
        assert prov.verification_status == ProvenanceStatus.SOC_VERIFIED
        assert prov.verification_source == VerificationSource.SIEM_WAZUH
        assert prov.siem_alert_id == payload.alert_id

    def test_splunk_source_sets_correct_verification_source(
        self, db_session, findings, framework_mapping,
    ):
        """Splunk events set verification_source to SIEM_SPLUNK."""
        payload = _make_payload(source="splunk", rule_id="DE.CM-1")

        service = TelemetryVerificationService(db_session)
        result = service.process_siem_event(payload)

        assert result.status == "verified"
        prov = db_session.query(FindingProvenance).filter(
            FindingProvenance.finding_id == findings[0].id
        ).first()
        assert prov.verification_source == VerificationSource.SIEM_SPLUNK

    def test_no_match_returns_no_match_status(self, db_session, findings):
        """SIEM event with no matching rule returns 'no_match'."""
        payload = _make_payload(rule_id="NONEXISTENT-RULE-999")

        service = TelemetryVerificationService(db_session)
        result = service.process_siem_event(payload)

        assert result.status == "no_match"
        assert result.finding_id is None

    def test_direct_finding_rule_id_match(self, db_session, findings):
        """Direct matching via payload.finding_rule_id bypasses framework registry."""
        payload = _make_payload(
            rule_id="irrelevant",
            finding_rule_id="PR.AA-5",  # Matches findings[1].nist_category
        )

        service = TelemetryVerificationService(db_session)
        result = service.process_siem_event(payload)

        assert result.status == "verified"
        assert result.finding_id == findings[1].id  # MFA Not Enforced

    def test_nist_category_prefix_match(self, db_session, findings):
        """NIST category prefix matching works when exact match fails."""
        payload = _make_payload(rule_id="DE.AE")

        service = TelemetryVerificationService(db_session)
        result = service.process_siem_event(payload)

        assert result.status == "verified"
        assert result.finding_id == findings[2].id  # Logging Health (DE.AE-3)


# ---------------------------------------------------------------------------
# Test: Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    """Tests for idempotent duplicate handling."""

    def test_duplicate_alert_id_returns_already_exists(
        self, db_session, findings, framework_mapping,
    ):
        """Submitting the same siem_alert_id twice returns 'already_exists'."""
        payload = _make_payload(
            source="wazuh",
            alert_id="DUPE-ALERT-001",
            rule_id="DE.CM-1",
        )

        service = TelemetryVerificationService(db_session)

        # First call → verified
        result1 = service.process_siem_event(payload)
        assert result1.status == "verified"

        # Second call → already_exists
        result2 = service.process_siem_event(payload)
        assert result2.status == "already_exists"
        assert result2.siem_alert_id == "DUPE-ALERT-001"

    def test_duplicate_does_not_create_extra_records(
        self, db_session, findings, framework_mapping,
    ):
        """Duplicate submissions must not create additional provenance records."""
        payload = _make_payload(
            alert_id="DUPE-ALERT-002",
            rule_id="DE.CM-1",
        )

        service = TelemetryVerificationService(db_session)
        service.process_siem_event(payload)
        service.process_siem_event(payload)
        service.process_siem_event(payload)  # Three submissions

        count = (
            db_session.query(FindingProvenance)
            .filter(FindingProvenance.siem_alert_id == "DUPE-ALERT-002")
            .count()
        )
        assert count == 1  # Only one record


# ---------------------------------------------------------------------------
# Test: GHI Recomputation with Provenance Weighting
# ---------------------------------------------------------------------------

class TestGHIRecomputation:
    """Tests for provenance-weighted GHI score recomputation."""

    def test_recompute_ghi_adjusts_score(
        self, db_session, findings, assessment,
    ):
        """GHI recomputation updates the assessment score."""
        service = TelemetryVerificationService(db_session)

        old_score = assessment.overall_score
        result = service.recompute_ghi_for_assessment(
            assessment_id=assessment.id,
            trigger_evidence_hash="e" * 64,
        )

        assert result is not None
        assert result["old_score"] == old_score
        assert result["new_score"] != old_score  # Score should change
        assert "delta" in result
        assert "evidence_hash" in result

    def test_soc_verified_finding_gets_full_weight(
        self, db_session, findings, assessment,
    ):
        """SOC_VERIFIED findings contribute full severity weight."""
        # Create provenance for first finding (critical) as SOC_VERIFIED
        prov = FindingProvenance(
            finding_id=findings[0].id,
            evidence_hash="f" * 64,
            verification_status=ProvenanceStatus.SOC_VERIFIED,
        )
        db_session.add(prov)
        db_session.commit()

        service = TelemetryVerificationService(db_session)
        result_verified = service.recompute_ghi_for_assessment(
            assessment_id=assessment.id,
            trigger_evidence_hash="f" * 64,
        )

        # Now make it PROVISIONAL — should result in higher score
        # (because PROVISIONAL uses 0.6x weight, meaning less deduction)
        prov.verification_status = ProvenanceStatus.PROVISIONAL
        db_session.commit()

        result_provisional = service.recompute_ghi_for_assessment(
            assessment_id=assessment.id,
            trigger_evidence_hash="g" * 64,
        )

        # PROVISIONAL should yield a higher score (less deduction)
        assert result_provisional["new_score"] > result_verified["new_score"]

    def test_contradicted_finding_has_elevated_weight(
        self, db_session, findings, assessment,
    ):
        """CONTRADICTED findings use 1.2x severity weight (elevated risk)."""
        # SOC_VERIFIED provenance
        prov = FindingProvenance(
            finding_id=findings[0].id,
            evidence_hash="h" * 64,
            verification_status=ProvenanceStatus.SOC_VERIFIED,
        )
        db_session.add(prov)
        db_session.commit()

        service = TelemetryVerificationService(db_session)
        result_verified = service.recompute_ghi_for_assessment(
            assessment_id=assessment.id,
            trigger_evidence_hash="h" * 64,
        )

        # Switch to CONTRADICTED
        prov.verification_status = ProvenanceStatus.CONTRADICTED
        db_session.commit()

        result_contradicted = service.recompute_ghi_for_assessment(
            assessment_id=assessment.id,
            trigger_evidence_hash="i" * 64,
        )

        # CONTRADICTED (1.2x) should yield a lower score than SOC_VERIFIED (1.0x)
        assert result_contradicted["new_score"] < result_verified["new_score"]

    def test_nonexistent_assessment_returns_none(self, db_session):
        """Recomputing for a nonexistent assessment returns None."""
        service = TelemetryVerificationService(db_session)
        result = service.recompute_ghi_for_assessment(
            assessment_id="nonexistent-id",
            trigger_evidence_hash="z" * 64,
        )
        assert result is None


# ---------------------------------------------------------------------------
# Test: Structured Audit Logging
# ---------------------------------------------------------------------------

class TestAuditLogging:
    """Tests for structured JSON log emissions on score changes."""

    def test_score_change_emits_structured_log(
        self, db_session, findings, assessment, caplog,
    ):
        """GHI recomputation emits a structured JSON log with required fields."""
        import logging

        with caplog.at_level(logging.INFO, logger="airs.telemetry"):
            service = TelemetryVerificationService(db_session)
            service.recompute_ghi_for_assessment(
                assessment_id=assessment.id,
                trigger_evidence_hash="j" * 64,
            )

        # Find the score change log entry
        score_logs = [
            r for r in caplog.records
            if "ghi_score_change" in r.message
        ]
        assert len(score_logs) >= 1

        log_data = json.loads(score_logs[0].message)
        assert log_data["event"] == "ghi_score_change"
        assert log_data["assessment_id"] == assessment.id
        assert "old_score" in log_data
        assert "new_score" in log_data
        assert "delta" in log_data
        assert log_data["evidence_hash"] == "j" * 64
        assert "timestamp" in log_data


# ---------------------------------------------------------------------------
# Test: Pydantic V2 Schema Validation
# ---------------------------------------------------------------------------

class TestSchemas:
    """Tests for Pydantic V2 schema validation."""

    def test_siem_event_payload_valid(self):
        """Valid SIEMEventPayload passes validation."""
        payload = SIEMEventPayload(
            source="wazuh",
            alert_id="alert-001",
            rule_id="550",
            timestamp="2026-05-22T12:00:00Z",
            raw_data_hash="a" * 64,
        )
        assert payload.source == "wazuh"
        assert payload.alert_id == "alert-001"

    def test_siem_event_payload_missing_required_field(self):
        """Missing required fields raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SIEMEventPayload(
                source="wazuh",
                # missing alert_id, rule_id, timestamp, raw_data_hash
            )

    def test_verification_response_serialization(self):
        """VerificationResponse serializes to JSON correctly."""
        resp = VerificationResponse(
            status="verified",
            finding_id="test-finding-id",
            verification_status="SOC_VERIFIED",
            evidence_hash="a" * 64,
            siem_alert_id="alert-001",
            message="Test finding verified.",
        )
        data = resp.model_dump()
        assert data["status"] == "verified"
        assert data["evidence_hash"] == "a" * 64


# ---------------------------------------------------------------------------
# Test: End-to-End Flow
# ---------------------------------------------------------------------------

class TestEndToEnd:
    """End-to-end integration tests for the full telemetry pipeline."""

    def test_full_pipeline_siem_to_score(
        self, db_session, findings, assessment, framework_mapping,
    ):
        """Full pipeline: SIEM event → provenance → GHI recomputation."""
        service = TelemetryVerificationService(db_session)
        old_score = assessment.overall_score

        # 1. Ingest SIEM event
        payload = _make_payload(source="wazuh", rule_id="DE.CM-1")
        result = service.process_siem_event(payload)
        assert result.status == "verified"
        assert result.finding_id == findings[0].id

        # 2. Verify provenance was created
        prov = db_session.query(FindingProvenance).filter(
            FindingProvenance.finding_id == findings[0].id
        ).first()
        assert prov is not None
        assert prov.verification_status == ProvenanceStatus.SOC_VERIFIED

        # 3. Recompute GHI
        score_result = service.recompute_ghi_for_assessment(
            assessment_id=assessment.id,
            trigger_evidence_hash=result.evidence_hash,
        )
        assert score_result is not None
        assert score_result["evidence_hash"] == result.evidence_hash

        # 4. Score should have changed
        db_session.refresh(assessment)
        assert assessment.overall_score == score_result["new_score"]

    def test_multiple_findings_verified_in_sequence(
        self, db_session, findings, assessment, framework_mapping,
    ):
        """Multiple findings verified in sequence produce correct state."""
        service = TelemetryVerificationService(db_session)

        # Verify finding[0] via framework mapping
        r1 = service.process_siem_event(
            _make_payload(rule_id="DE.CM-1")
        )
        assert r1.status == "verified"

        # Verify finding[1] via direct rule_id
        r2 = service.process_siem_event(
            _make_payload(rule_id="x", finding_rule_id="PR.AA-5")
        )
        assert r2.status == "verified"

        # Check DB state
        verified_count = (
            db_session.query(FindingProvenance)
            .filter(FindingProvenance.verification_status == ProvenanceStatus.SOC_VERIFIED)
            .count()
        )
        assert verified_count == 2
