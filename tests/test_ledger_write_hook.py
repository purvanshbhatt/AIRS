"""
Tests for the Readiness Ledger write hook (Sprint 1.8, Task S1.8-A4).

Covers:
  - Single-write idempotency on the same (org_id, timestamp, new_score).
  - Multiple writes with different new_score or timestamp not no-op.
  - The wrapped calculate_readiness_delta preserves the original return
    value while writing to the ledger whenever org_id is provided.
  - Score out-of-bounds values are rejected by the model validator.
  - No forbidden LLM imports by AST scan.
"""

import uuid
import inspect
import ast
from datetime import datetime, timedelta, timezone

import pytest

from app.models import Organization
from app.models.readiness_ledger import ReadinessLedgerEntry
from app.services import readiness_ledger as ledger_module
from app.services.readiness_ledger import record_score_change


def _make_org(session) -> str:
    org = Organization(
        id=str(uuid.uuid4()),
        name="sandbox - Ledger Test",
    )
    session.add(org)
    session.commit()
    return org.id


class TestRecordScoreChange:
    def test_basic_insert_and_idempotency(self, db_session):
        org_id = _make_org(db_session)
        ts = datetime(2026, 7, 12, 12, 0, 0, tzinfo=timezone.utc)
        # First write
        first = record_score_change(
            session_factory=lambda: db_session,
            org_id=org_id,
            previous_score=70.0,
            new_score=75.0,
            driver_type="verification",
            driver_item="ctrl-1",
            impact=3.0,
            evidence_source="telemetry",
            created_by="system",
            timestamp=ts,
        )
        assert first is not None
        # Idempotent replay: same (org, timestamp, new_score) → no-op
        replay = record_score_change(
            session_factory=lambda: db_session,
            org_id=org_id,
            previous_score=70.0,
            new_score=75.0,
            timestamp=ts,
        )
        assert replay is None

        # Verify exactly one row exists
        rows = db_session.query(ReadinessLedgerEntry).all()
        assert len(rows) == 1

    def test_distinct_write_creates_second_row(self, db_session):
        org_id = _make_org(db_session)
        t0 = datetime(2026, 7, 12, 9, 0, 0, tzinfo=timezone.utc)
        record_score_change(
            session_factory=lambda: db_session,
            org_id=org_id,
            previous_score=70.0,
            new_score=75.0,
            timestamp=t0,
        )
        # Later timestamp → distinct row.
        second = record_score_change(
            session_factory=lambda: db_session,
            org_id=org_id,
            previous_score=75.0,
            new_score=80.0,
            timestamp=t0 + timedelta(hours=1),
        )
        assert second is not None
        rows = db_session.query(ReadinessLedgerEntry).all()
        assert len(rows) == 2

    def test_invalid_org_id_raises(self, db_session):
        with pytest.raises(ValueError):
            record_score_change(
                session_factory=lambda: db_session,
                org_id="",
                previous_score=1.0,
                new_score=2.0,
            )

    def test_score_range_rejection_through_validator(self, db_session):
        # Out-of-range previous_score is rejected by the model validator.
        with pytest.raises(ValueError):
            record_score_change(
                session_factory=lambda: db_session,
                org_id=str(uuid.uuid4()),
                previous_score=-1.0,
                new_score=10.0,
            )


class TestScoreAndRecordHook:
    def test_score_and_record_writes_ledger_row(self, db_session):
        from app.models import Organization

        org = Organization(id=str(uuid.uuid4()), name="Hook Test")
        db_session.add(org)
        db_session.commit()
        org_id = org.id

        # The hook may already be installed by other tests in the file.
        # attach_to_scoring is idempotent.
        from app.services import readiness_ledger as rl
        rl.attach_to_scoring()

        from app.services.scoring import calculate_readiness_delta
        result = calculate_readiness_delta(
            assessment_score=60.0,
            verified_controls=[
                {"name": "EDR", "family": "Endpoint", "severity": "critical"},
            ],
            verified_coverages=[],
            lifecycle_risks=[],
            exposure_risks=[],
            previous_readiness_score=55.0,
            org_id=org_id,
            evidence_source="telemetry",
            created_by="test",
        )

        assert "final_readiness" in result
        baseline_final = result["final_readiness"]

        rows = db_session.query(ReadinessLedgerEntry).filter(
            ReadinessLedgerEntry.org_id == org_id
        ).all()
        assert len(rows) == 1
        assert rows[0].delta == pytest.approx(round(baseline_final - 55.0, 2))

    def test_invariance_under_replay(self, db_session):
        from app.models import Organization

        org = Organization(id=str(uuid.uuid4()), name="Replay Test")
        db_session.add(org)
        db_session.commit()
        org_id = org.id

        from app.services import readiness_ledger as rl
        rl.attach_to_scoring()

        from app.services.scoring import calculate_readiness_delta
        call_kwargs = dict(
            assessment_score=70.0,
            verified_controls=[],
            verified_coverages=[],
            lifecycle_risks=[],
            exposure_risks=[],
            previous_readiness_score=60.0,
            org_id=org_id,
            evidence_source="telemetry",
            created_by="test",
        )
        r1 = calculate_readiness_delta(**call_kwargs)
        r2 = calculate_readiness_delta(**call_kwargs)
        assert r1["final_readiness"] == r2["final_readiness"]


class TestModuleInvariants:
    def test_no_forbidden_llm_imports_in_source(self):
        src = inspect.getsource(ledger_module)
        tree = ast.parse(src)

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module)

        forbidden = ("ai_narrative", "llm_narrative", "google.genai",
                     "google.generativeai")
        bad = sorted(
            n for n in imported
            if any(n == f or n.startswith(f + ".") for f in forbidden)
        )
        assert not bad, f"readiness_ledger.py has forbidden imports: {bad}"
