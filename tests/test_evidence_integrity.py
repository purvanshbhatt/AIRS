"""
Tests for SHA-256 Authoritative Evidence Integrity Verification.

Validates that:
- Correct payload generates expected deterministic hash
- Modified payload produces hash mismatch and fails closed
- Reordered JSON keys preserve hash identity under canonicalization
- Changed nested values produce hash mismatch
- Tampered evidence is rejected by EvidenceOrchestrator
- Duplicate evidence is identified
- Malformed evidence is handled safely
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
import app.models  # Register all models with Base.metadata
from app.models.evidence import EvidenceLedger, NormalizedEvidenceRecord
from app.models.organization import Organization
from app.models.connector import Connector
from app.schemas.evidence import (
    NormalizedEvidence,
    EvidenceCollectionResult,
    EvidenceSeverity,
    ProviderTransport,
)
from app.services.evidence.integrity import (
    canonicalize_payload,
    compute_evidence_hash,
    verify_evidence_hash,
)
from app.services.evidence.orchestrator import EvidenceOrchestrator


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_correct_payload_valid_hash():
    """A valid payload computes a deterministic SHA-256 hash that verifies successfully."""
    source = "aws_security_hub"
    ts = "2026-09-16T12:00:00+00:00"
    payload = {
        "finding_id": "arn:aws:securityhub:us-east-1:123456789012:finding/s3-encryption",
        "severity": "HIGH",
        "resource": "arn:aws:s3:::resilai-test-bucket",
    }

    hash1 = compute_evidence_hash(source, ts, payload)
    assert len(hash1) == 64
    assert verify_evidence_hash(source, ts, payload, hash1) is True


def test_modified_payload_hash_mismatch():
    """Altering any payload field causes hash verification to fail closed."""
    source = "aws_security_hub"
    ts = "2026-09-16T12:00:00+00:00"
    original_payload = {"key": "original_value", "count": 10}
    tampered_payload = {"key": "tampered_value", "count": 10}

    claimed_hash = compute_evidence_hash(source, ts, original_payload)

    # Verifying with tampered payload must return False
    assert verify_evidence_hash(source, ts, tampered_payload, claimed_hash) is False


def test_reordered_json_keys_preserve_identity():
    """Key reordering in payload produces the exact same hash due to canonicalization."""
    source = "aws_security_hub"
    ts = "2026-09-16T12:00:00+00:00"
    payload_order_a = {"alpha": 1, "beta": 2, "gamma": {"z": 26, "a": 1}}
    payload_order_b = {"gamma": {"a": 1, "z": 26}, "beta": 2, "alpha": 1}

    hash_a = compute_evidence_hash(source, ts, payload_order_a)
    hash_b = compute_evidence_hash(source, ts, payload_order_b)

    assert hash_a == hash_b
    assert verify_evidence_hash(source, ts, payload_order_b, hash_a) is True


def test_changed_nested_value_mismatch():
    """Modifying a nested attribute produces a mismatch."""
    source = "aws_security_hub"
    ts = "2026-09-16T12:00:00+00:00"
    payload_clean = {"compliance": {"status": "PASSED"}}
    payload_tampered = {"compliance": {"status": "FAILED"}}

    hash_clean = compute_evidence_hash(source, ts, payload_clean)
    assert verify_evidence_hash(source, ts, payload_tampered, hash_clean) is False


def test_orchestrator_rejects_tampered_evidence(test_db):
    """EvidenceOrchestrator rejects evidence with invalid/tampered hashes and does not persist them."""
    org_id = "test-org-integrity"
    conn_id = "test-conn-integrity"

    org = Organization(id=org_id, name="Integrity Test Org", owner_uid="user-1")
    test_db.add(org)
    conn = Connector(
        id=conn_id,
        org_id=org_id,
        connector_type="aws_security_hub",
        display_name="AWS Test",
        auth_method="api_key",
        encrypted_credentials="{}",
    )
    test_db.add(conn)
    test_db.commit()

    now = datetime.now(timezone.utc)
    valid_evidence = NormalizedEvidence(
        source_connector="aws_security_hub",
        event_type="aws.securityhub.finding",
        timestamp=now,
        raw_payload={"title": "Unencrypted S3"},
    )
    valid_evidence.compute_hash()

    tampered_evidence = NormalizedEvidence(
        source_connector="aws_security_hub",
        event_type="aws.securityhub.finding",
        timestamp=now,
        raw_payload={"title": "Legitimate Title"},
    )
    tampered_evidence.compute_hash()
    # Maliciously mutate raw_payload without recomputing hash
    tampered_evidence.raw_payload = {"title": "Forged Finding Title"}

    batch = EvidenceCollectionResult(
        provider_name="aws_security_hub",
        transport=ProviderTransport.MCP,
        evidence_count=2,
        evidence=[valid_evidence, tampered_evidence],
    )

    orchestrator = EvidenceOrchestrator(test_db)
    summary = orchestrator.ingest_collection_result(org_id, conn_id, batch)

    # Exactly 1 new record should be ingested; the tampered record is dropped
    assert summary["new"] == 1

    records = test_db.query(EvidenceLedger).filter_by(org_id=org_id).all()
    assert len(records) == 1
    assert records[0].evidence_hash == valid_evidence.evidence_hash


def test_orchestrator_handles_duplicates(test_db):
    """Duplicate evidence with identical hash is recognized and not re-persisted."""
    org_id = "test-org-dup"
    conn_id = "test-conn-dup"

    org = Organization(id=org_id, name="Dup Test Org", owner_uid="user-1")
    test_db.add(org)
    test_db.commit()

    now = datetime.now(timezone.utc)
    evidence = NormalizedEvidence(
        source_connector="aws_security_hub",
        event_type="aws.securityhub.finding",
        timestamp=now,
        raw_payload={"item": "finding-1"},
    )
    evidence.compute_hash()

    batch = EvidenceCollectionResult(
        provider_name="aws_security_hub",
        transport=ProviderTransport.MCP,
        evidence_count=1,
        evidence=[evidence],
    )

    orchestrator = EvidenceOrchestrator(test_db)
    summary1 = orchestrator.ingest_collection_result(org_id, conn_id, batch)
    assert summary1["new"] == 1
    assert summary1["duplicates"] == 0

    summary2 = orchestrator.ingest_collection_result(org_id, conn_id, batch)
    assert summary2["new"] == 0
    assert summary2["duplicates"] == 1


def test_malformed_evidence_handling():
    """Empty or malformed hash and payload fail closed gracefully."""
    assert verify_evidence_hash("aws", "2026-09-16", {}, "") is False
    assert verify_evidence_hash("aws", "2026-09-16", {}, None) is False
    assert verify_evidence_hash("aws", "2026-09-16", {}, "short") is False
