"""
Tests for ReadinessLedgerEntry (Sprint 1.8, Task S1.8-A1).

Verifies:
  - Model fields, types, and constraint surface.
  - Round-trip insert/select via SQLAlchemy 2.0.
  - Score range validator (0-100).
  - Idempotency uniqueness guarantee via the (org_id, timestamp, new_score)
    index (uniqueness enforced at the service layer; here we assert
    insert success, UPDATE forbidden at service layer).
  - Score range validator rejects out-of-band values.

The model is registered via app.models.__init__.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Organization, ReadinessLedgerEntry


def _make_org(session) -> str:
    org = Organization(
        id=str(uuid.uuid4()),
        name="Acme Corp",
    )
    session.add(org)
    session.commit()
    return org.id


class TestReadinessLedgerEntryModel:
    def test_round_trip(self, db_session):
        org_id = _make_org(db_session)
        entry = ReadinessLedgerEntry(
            org_id=org_id,
            previous_score=72.5,
            new_score=80.0,
            delta=80.0 - 72.5,
            driver_type="kev",
            driver_item="CVE-2024-3094",
            impact=7.5,
            evidence_source="wazuh",
            created_by="system",
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        assert entry.id is not None
        assert len(entry.id) == 36
        assert entry.org_id == org_id
        assert entry.previous_score == 72.5
        assert entry.new_score == 80.0
        assert entry.delta == pytest.approx(7.5)
        assert entry.driver_type == "kev"
        assert entry.driver_item == "CVE-2024-3094"
        assert entry.impact == pytest.approx(7.5)
        assert entry.evidence_source == "wazuh"
        assert entry.created_by == "system"
        assert isinstance(entry.timestamp, datetime)

    def test_indexes_present(self, db_session):
        # Verify the table-level indexes are declared (idempotency + ordering).
        indexes = {
            idx.name
            for idx in ReadinessLedgerEntry.__table__.indexes
        }
        assert "ix_readiness_ledger_org_timestamp" in indexes
        assert "ix_readiness_ledger_idempotency" in indexes

    def test_foreign_key_required(self, db_session):
        entry = ReadinessLedgerEntry(
            org_id=None,
            previous_score=1.0,
            new_score=2.0,
            delta=1.0,
        )
        db_session.add(entry)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_default_uuid_on_insert(self, db_session):
        org_id = _make_org(db_session)
        entry = ReadinessLedgerEntry(
            org_id=org_id,
            previous_score=10.0,
            new_score=20.0,
            delta=10.0,
        )
        db_session.add(entry)
        db_session.commit()
        assert entry.id is not None
        parsed = uuid.UUID(entry.id)
        assert parsed.version == 4

    def test_score_range_validator_rejects_above_100(self, db_session):
        with pytest.raises(ValueError):
            ReadinessLedgerEntry(
                org_id=str(uuid.uuid4()),
                previous_score=99.0,
                new_score=150.0,
                delta=51.0,
            )

    def test_score_range_validator_rejects_below_0(self, db_session):
        with pytest.raises(ValueError):
            ReadinessLedgerEntry(
                org_id=str(uuid.uuid4()),
                previous_score=-1.0,
                new_score=10.0,
                delta=11.0,
            )

    def test_idempotency_index_columns(self, db_session):
        # The (org_id, timestamp, new_score) idempotency index is what
        # prevents duplicate ledger rows from a scoring replay loop.
        idx_names_and_cols = {
            idx.name: [c.name for c in idx.columns]
            for idx in ReadinessLedgerEntry.__table__.indexes
        }
        cols = idx_names_and_cols["ix_readiness_ledger_idempotency"]
        assert cols == ["org_id", "timestamp", "new_score"]

    def test_timestamp_defaults_to_now(self, db_session):
        org_id = _make_org(db_session)
        entry = ReadinessLedgerEntry(
            org_id=org_id,
            previous_score=10.0,
            new_score=20.0,
            delta=10.0,
        )
        db_session.add(entry)
        db_session.commit()
        # SQLite server_default now() returns naive datetime; we verify
        # that a value was populated and is in a sane year range.
        assert entry.timestamp is not None
        ts = entry.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        assert ts.year >= 2026
