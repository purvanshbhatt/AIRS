"""
Governance Engine Regression Tests — Module 4.

Tests the deterministic ingestion pipeline and idempotency guarantees of
the Governance-as-Code Controller.

Test Cases:
  1. test_deterministic_ingestion_state_transition
     - Valid Wazuh payload with matching finding promotes badge to SOC_VERIFIED.
     - Evidence hash is a 64-char lowercase hex SHA-256 string.
     - Hash is deterministic: same payload always produces same hash.

  2. test_ingestion_idempotency_barrier
     - Posting the same alert_id + organization_id twice does not create a
       duplicate FindingProvenance record.
     - Second call returns status='already_exists' immediately.

Run with:
  py -m pytest tests/governance/ -v
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.assessment import Assessment, AssessmentStatus
from app.models.control_rule_registry import ControlRuleRegistry
from app.models.finding import Finding, Severity, FindingStatus
from app.models.finding_provenance import FindingProvenance, ProvenanceStatus
from app.models.organization import Organization
from app.services.telemetry import TelemetryVerificationService


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    """In-memory SQLite database for each test — fully isolated."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def org(db_session) -> Organization:
    """Create a test organisation."""
    o = Organization(
        id=str(uuid.uuid4()),
        name="AcmeCorp Security",
        owner_uid="uid-acme-001",
    )
    db_session.add(o)
    db_session.commit()
    return o


@pytest.fixture
def assessment(db_session, org) -> Assessment:
    """Create a test assessment linked to the organisation."""
    a = Assessment(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        owner_uid=org.owner_uid,
        status=AssessmentStatus.COMPLETED,
        overall_score=72.0,
    )
    db_session.add(a)
    db_session.commit()
    return a


@pytest.fixture
def finding(db_session, assessment) -> Finding:
    """Create a test finding with nist_category matching our SIEM rule_id."""
    f = Finding(
        id=str(uuid.uuid4()),
        assessment_id=assessment.id,
        title="EDR Coverage Gap Detected",
        severity=Severity.HIGH,
        status=FindingStatus.OPEN,
        nist_category="DC-001",   # Must match the rule_id in the payload
        domain_id="detection",
        recommendation="Deploy EDR agents to all endpoints.",
    )
    db_session.add(f)
    db_session.commit()
    return f


@pytest.fixture
def control_rule_entry(db_session) -> ControlRuleRegistry:
    """Seed a ControlRuleRegistry entry for DC-001."""
    entry = ControlRuleRegistry(
        id=str(uuid.uuid4()),
        finding_rule_id="DC-001",
        nist_ai_rmf_control_id="GOVERN-1.1",
        mitre_atlas_tactic_id="AML.TA0001",
        mapping_version="2026.1",
        is_active=True,
    )
    db_session.add(entry)
    db_session.commit()
    return entry


# ---------------------------------------------------------------------------
# Test 1: Deterministic ingestion state transition
# ---------------------------------------------------------------------------

class TestDeterministicIngestionStateTransition:
    """Validate that a valid Wazuh payload transitions the finding to SOC_VERIFIED."""

    def test_finding_promoted_to_soc_verified(
        self, db_session, org, assessment, finding, control_rule_entry
    ):
        """
        A valid Wazuh payload matching DC-001 must:
          1. Set FindingProvenance.verification_status = SOC_VERIFIED.
          2. Set evidence_hash to a valid 64-char lowercase hex SHA-256 string.
          3. Return status = 'verified'.
        """
        raw_telemetry = {
            "agent_id": "001",
            "agent_name": "workstation-01",
            "rule_id": "550",
            "rule_description": "EDR agent inactive",
            "timestamp": "2026-05-26T00:00:00Z",
            "data": {"edr_status": "inactive", "endpoint_count": 47},
        }

        service = TelemetryVerificationService(db_session)
        result = service.ingest_siem_telemetry(
            alert_id="wazuh-2026-test-001",
            rule_id="DC-001",
            source_integration="wazuh",
            organization_id=org.id,
            raw_telemetry_dump=raw_telemetry,
        )

        # ── Outcome assertions ──
        assert result["status"] == "verified", (
            f"Expected status='verified', got '{result['status']}'. "
            f"Message: {result.get('message')}"
        )
        assert result["finding_id"] == finding.id
        assert result["verification_status"] == ProvenanceStatus.SOC_VERIFIED.value

        # ── Hash assertions ──
        evidence_hash = result["evidence_hash"]
        assert isinstance(evidence_hash, str), "evidence_hash must be a string."
        assert len(evidence_hash) == 64, (
            f"SHA-256 hex digest must be 64 chars, got {len(evidence_hash)}."
        )
        assert evidence_hash == evidence_hash.lower(), "Hash must be lowercase hex."
        assert all(c in "0123456789abcdef" for c in evidence_hash), (
            "Hash must contain only valid hex characters."
        )

    def test_evidence_hash_is_deterministic(
        self, db_session, org, assessment, finding, control_rule_entry
    ):
        """The same raw_telemetry_dump must always produce the same SHA-256 hash."""
        raw_telemetry = {
            "agent_id": "002",
            "event_type": "edr_gap",
            "severity": "high",
        }

        # Compute expected hash independently using the same algorithm
        expected_hash = hashlib.sha256(
            json.dumps(
                dict(sorted(raw_telemetry.items())),
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()

        service = TelemetryVerificationService(db_session)
        result = service.ingest_siem_telemetry(
            alert_id="wazuh-determinism-test-001",
            rule_id="DC-001",
            source_integration="wazuh",
            organization_id=org.id,
            raw_telemetry_dump=raw_telemetry,
        )

        assert result["status"] == "verified"
        assert result["evidence_hash"] == expected_hash, (
            f"Hash mismatch!\n"
            f"  Expected : {expected_hash}\n"
            f"  Got      : {result['evidence_hash']}"
        )

    def test_provenance_record_persisted(
        self, db_session, org, assessment, finding, control_rule_entry
    ):
        """Verify the FindingProvenance record is actually written to the database."""
        service = TelemetryVerificationService(db_session)
        result = service.ingest_siem_telemetry(
            alert_id="wazuh-persistence-test-001",
            rule_id="DC-001",
            source_integration="wazuh",
            organization_id=org.id,
            raw_telemetry_dump={"sensor": "edr-agent", "status": "offline"},
        )

        assert result["status"] == "verified"

        prov = (
            db_session.query(FindingProvenance)
            .filter(FindingProvenance.finding_id == finding.id)
            .first()
        )
        assert prov is not None, "FindingProvenance record must be persisted to DB."
        assert prov.verification_status == ProvenanceStatus.SOC_VERIFIED
        assert len(prov.evidence_hash) == 64
        assert prov.siem_alert_id == "wazuh-persistence-test-001"


# ---------------------------------------------------------------------------
# Test 2: Idempotency barrier
# ---------------------------------------------------------------------------

class TestIngestionIdempotencyBarrier:
    """Enforce that duplicate (alert_id, organization_id) pairs are rejected cleanly."""

    def test_duplicate_alert_returns_already_exists(
        self, db_session, org, assessment, finding, control_rule_entry
    ):
        """
        Posting the same alert_id for the same org twice must:
          1. First call  → status='verified', new FindingProvenance created.
          2. Second call → status='already_exists', no additional DB record.
        """
        service = TelemetryVerificationService(db_session)
        payload_kwargs = dict(
            alert_id="wazuh-idempotency-test-001",
            rule_id="DC-001",
            source_integration="wazuh",
            organization_id=org.id,
            raw_telemetry_dump={"edr": "inactive", "hosts": 50},
        )

        # First ingestion — should verify
        first = service.ingest_siem_telemetry(**payload_kwargs)
        assert first["status"] == "verified"

        # Second ingestion — same alert, same org
        second = service.ingest_siem_telemetry(**payload_kwargs)
        assert second["status"] == "already_exists", (
            f"Expected 'already_exists' on duplicate, got '{second['status']}'."
        )
        assert second["evidence_hash"] == first["evidence_hash"], (
            "Idempotent response should echo the original evidence hash."
        )

    def test_no_duplicate_provenance_record_created(
        self, db_session, org, assessment, finding, control_rule_entry
    ):
        """Only one FindingProvenance row must exist after two identical submissions."""
        service = TelemetryVerificationService(db_session)
        payload_kwargs = dict(
            alert_id="wazuh-dedup-test-001",
            rule_id="DC-001",
            source_integration="wazuh",
            organization_id=org.id,
            raw_telemetry_dump={"agent": "agent-99", "status": "inactive"},
        )

        service.ingest_siem_telemetry(**payload_kwargs)
        service.ingest_siem_telemetry(**payload_kwargs)

        count = (
            db_session.query(FindingProvenance)
            .filter(FindingProvenance.finding_id == finding.id)
            .count()
        )
        assert count == 1, (
            f"Expected exactly 1 FindingProvenance row, found {count}. "
            "Duplicate ingestion must be idempotent."
        )

    def test_different_orgs_same_alert_id_are_independent(
        self, db_session, org, assessment, finding, control_rule_entry
    ):
        """
        The same alert_id from two different organizations must NOT collide.
        Each should create its own FindingProvenance record.
        """
        # Create a second org and assessment with the same rule-matching finding
        org2 = Organization(
            id=str(uuid.uuid4()),
            name="SecondCorp",
            owner_uid="uid-second-001",
        )
        db_session.add(org2)
        db_session.commit()

        assessment2 = Assessment(
            id=str(uuid.uuid4()),
            organization_id=org2.id,
            owner_uid=org2.owner_uid,
            status=AssessmentStatus.COMPLETED,
            overall_score=65.0,
        )
        db_session.add(assessment2)
        db_session.commit()

        finding2 = Finding(
            id=str(uuid.uuid4()),
            assessment_id=assessment2.id,
            title="EDR Coverage Gap (Org 2)",
            severity=Severity.HIGH,
            status=FindingStatus.OPEN,
            nist_category="DC-001",
            domain_id="detection",
            recommendation="Deploy EDR agents.",
        )
        db_session.add(finding2)
        db_session.commit()

        service = TelemetryVerificationService(db_session)
        shared_alert_id = "wazuh-cross-org-test-001"

        r1 = service.ingest_siem_telemetry(
            alert_id=shared_alert_id,
            rule_id="DC-001",
            source_integration="wazuh",
            organization_id=org.id,
            raw_telemetry_dump={"host": "org1-endpoint", "status": "inactive"},
        )
        r2 = service.ingest_siem_telemetry(
            alert_id=shared_alert_id,
            rule_id="DC-001",
            source_integration="wazuh",
            organization_id=org2.id,
            raw_telemetry_dump={"host": "org2-endpoint", "status": "inactive"},
        )

        # Both should succeed independently — different orgs
        assert r1["status"] == "verified", f"Org1 first call failed: {r1}"
        assert r2["status"] == "verified", (
            f"Org2 should have created a separate provenance record, got: {r2}"
        )
