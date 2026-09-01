"""
Tests for the Readiness API surface (Sprint 1.8, Task S1.8-A5).

Covers:
  - GET /api/v1/readiness/drivers  happy path + missing org_id + unknown org
  - GET /api/v1/readiness/actions  ?
  - GET /api/v1/readiness/ledger   returns inserted rows
  - GET /api/v1/readiness/timeline returns time-series
  - 422 on missing org_id
  - 404 on unknown org
"""

import uuid

import pytest

from app.models import Organization


def _make_org(db_session) -> str:
    org = Organization(id=str(uuid.uuid4()), name="API Test Org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org.id


class TestReadinessDrivers:
    def test_returns_empty_drivers_for_known_org(self, client, db_session):
        org_id = _make_org(db_session)
        r = client.get(f"/api/v1/readiness/drivers?org_id={org_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["org_id"] == org_id
        assert body["positive_drivers"] == []
        assert body["negative_drivers"] == []

    def test_unknown_org_returns_404(self, client, db_session):
        r = client.get("/api/v1/readiness/drivers?org_id=does-not-exist")
        assert r.status_code == 404

    def test_missing_org_id_returns_422(self, client, db_session):
        r = client.get("/api/v1/readiness/drivers")
        # 422 from FastAPI's validation error
        assert r.status_code == 422


class TestReadinessActions:
    def test_returns_empty_actions(self, client, db_session):
        org_id = _make_org(db_session)
        r = client.get(f"/api/v1/readiness/actions?org_id={org_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["org_id"] == org_id
        assert body["actions"] == []

    def test_unknown_org_returns_404(self, client):
        r = client.get("/api/v1/readiness/actions?org_id=nope")
        assert r.status_code == 404

    def test_top_n_validation(self, client, db_session):
        org_id = _make_org(db_session)
        r = client.get(
            f"/api/v1/readiness/actions?org_id={org_id}&top_n=0"
        )
        assert r.status_code == 422


class TestReadinessLedger:
    def test_returns_inserted_rows(self, client, db_session):
        from datetime import datetime, timezone
        from app.models.readiness_ledger import ReadinessLedgerEntry

        org_id = _make_org(db_session)
        # Insert a few ledger rows directly via the session
        ts = datetime(2026, 7, 12, 10, 0, 0, tzinfo=timezone.utc)
        for prev, new in [(50.0, 55.0), (55.0, 60.0)]:
            db_session.add(ReadinessLedgerEntry(
                org_id=org_id,
                timestamp=ts,
                previous_score=prev,
                new_score=new,
                delta=new - prev,
            ))
            ts = datetime.fromtimestamp(ts.timestamp() + 60, tz=timezone.utc)
        db_session.commit()

        r = client.get(f"/api/v1/readiness/ledger?org_id={org_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["org_id"] == org_id
        assert body["count"] == 2
        assert len(body["entries"]) == 2
        # Most-recent-first ordering
        assert body["entries"][0]["new_score"] == 60.0

    def test_unknown_org_returns_404(self, client):
        r = client.get("/api/v1/readiness/ledger?org_id=nope")
        assert r.status_code == 404


class TestReadinessTimeline:
    def test_returns_time_series(self, client, db_session):
        from datetime import datetime, timezone
        from app.models.readiness_ledger import ReadinessLedgerEntry

        org_id = _make_org(db_session)
        ts = datetime(2026, 7, 12, 9, 0, 0, tzinfo=timezone.utc)
        for prev, new in [(40.0, 45.0), (45.0, 50.0)]:
            db_session.add(ReadinessLedgerEntry(
                org_id=org_id,
                timestamp=ts,
                previous_score=prev,
                new_score=new,
                delta=new - prev,
            ))
            ts = datetime.fromtimestamp(ts.timestamp() + 60, tz=timezone.utc)
        db_session.commit()

        r = client.get(f"/api/v1/readiness/timeline?org_id={org_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 2
        # Ascending order: first point is earlier
        assert body["points"][0]["new_score"] == 45.0
        assert body["points"][1]["new_score"] == 50.0

    def test_unknown_org_returns_404(self, client):
        r = client.get("/api/v1/readiness/timeline?org_id=nope")
        assert r.status_code == 404


class TestRouteRegistration:
    def test_routes_are_mounted(self, client):
        # Sanity: the readiness paths exist and respond.
        # Some auth paths return 422 (validation) without org_id.
        r = client.get("/api/v1/readiness/drivers")
        assert r.status_code == 422
        r = client.get("/api/v1/readiness/actions")
        assert r.status_code == 422
        r = client.get("/api/v1/readiness/ledger")
        assert r.status_code == 422
        r = client.get("/api/v1/readiness/timeline")
        assert r.status_code == 422
