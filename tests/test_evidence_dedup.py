"""
Regression: a generated report repeated the same finding again and again.

Two causes are pinned here, both independent of the connector vendor:

1. A connector that reports its full state on every sync (a Microsoft 365
   snapshot, an AWS credential report) stores a new telemetry event each
   time. The readiness pipeline read every stored copy from the last 24
   hours as new evidence, so each user, device and alert was evaluated once
   per sync and printed once per sync.

2. Findings that carry no timestamp of their own were written to the
   evidence ledger with "now" as their timestamp. The ledger hash includes
   the timestamp, so every sync stored the same unchanged finding again.

De-duplication is by stable identity (evidence kind + connector + the
source system's own id), keeping the newest observation.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENV", "local")

from app.connectors.base import NormalizedEvent
from app.models.evidence import EvidenceLedger, NormalizedEvidenceRecord
from app.models.organization import Organization
from app.models.telemetry_event import TelemetryEvent
from app.reports.readiness_source import build_readiness_report, build_template_snapshot
from app.reports.templates import flatten_findings
from app.services.clinic_engine.v2.evidence_collection import (
    collect_evidence,
    dedupe_moments,
    evaluate_events,
)
from app.services.clinic_engine.v2.schema import EvidenceKind, RawEvent, Verdict
from app.services.connector_manager import ConnectorManager

ORG = "org-evidence-dedup"
NOW = datetime.now(timezone.utc)
STALE = (NOW - timedelta(days=200)).isoformat()


def _org(db):
    db.add(Organization(id=ORG, name="Dedup Clinic", owner_uid="owner-1"))
    db.commit()


def _ms_payload(users=None, alerts=None, devices=None):
    return {
        "entra_users": users if users is not None else [_ms_user("u-1", "Dana Former")],
        "intune_devices": devices if devices is not None else [
            {"device_id": "dev-1", "device_name": "FRONT-DESK-01", "compliance_state": "compliant"},
        ],
        "defender_alerts": alerts if alerts is not None else [
            {"alert_id": "al-1", "device_id": "dev-1", "severity": "high", "status": "active",
             "title": "Suspicious PowerShell"},
        ],
    }


def _ms_user(user_id, name, enabled=True, last_sign_in=STALE):
    return {"user_id": user_id, "display_name": name, "account_enabled": enabled, "last_sign_in": last_sign_in}


def _ms_event(minutes_ago, payload=None):
    """A Microsoft 365 sync: the connector stores one full snapshot per sync,
    each under a new id (``sync-<connector>-<unix time>``)."""
    when = NOW - timedelta(minutes=minutes_ago)
    return RawEvent(
        event_type="microsoft.telemetry",
        source_system="microsoft",
        source_event_id=f"sync-conn-1-{int(when.timestamp())}",
        organization_id=ORG,
        payload=payload if payload is not None else _ms_payload(),
        timestamp=when.isoformat(),
    )


def _store(db, event, minutes_ago=0, source_event_id=None):
    db.add(TelemetryEvent(
        org_id=ORG,
        event_type=event.event_type,
        source_system=event.source_system,
        source_event_id=source_event_id or event.source_event_id,
        payload_hash="0" * 64,
        payload=json.dumps(event.payload),
        created_at=NOW - timedelta(minutes=minutes_ago),
    ))


def _labels(readiness):
    return [c.label for c in readiness.failed_checks + readiness.warnings]


# ---------------------------------------------------------------------------
# Evidence: one item per entity, newest observation wins
# ---------------------------------------------------------------------------

class TestCollectEvidence:
    def test_entity_seen_in_three_syncs_is_one_piece_of_evidence(self):
        events = [_ms_event(0), _ms_event(60), _ms_event(120)]  # newest first
        stats = {}
        evidence = collect_evidence(events, stats)

        users = [e for e in evidence if e.kind == EvidenceKind.USER_ACCOUNT_STATUS]
        alerts = [e for e in evidence if e.kind == EvidenceKind.SECURITY_ALERT]
        devices = [e for e in evidence if e.kind == EvidenceKind.DEVICE_SECURITY_STATUS]
        assert [e.source_id for e in users] == ["u-1"]
        assert [e.source_id for e in alerts] == ["al-1"]
        assert [e.source_id for e in devices] == ["dev-1"]
        # Occurrences are counted, not thrown away silently.
        assert stats["events"] == 3
        assert stats["evidence_items"] == 3
        assert stats["repeat_observations_collapsed"] == 6

    def test_newest_observation_wins(self):
        """Suspended an hour ago: the older snapshot must not keep them listed."""
        newer = _ms_event(0, _ms_payload(users=[_ms_user("u-1", "Dana Former", enabled=False)]))
        older = _ms_event(60)
        evidence = collect_evidence([newer, older])
        users = [e for e in evidence if e.kind == EvidenceKind.USER_ACCOUNT_STATUS]
        assert len(users) == 1
        assert users[0].payload["account_enabled"] is False

    def test_order_of_events_does_not_matter_when_they_are_timestamped(self):
        newer = _ms_event(0, _ms_payload(users=[_ms_user("u-1", "Dana Former", enabled=False)]))
        older = _ms_event(60)
        evidence = collect_evidence([older, newer])  # oldest first
        users = [e for e in evidence if e.kind == EvidenceKind.USER_ACCOUNT_STATUS]
        assert [u.payload["account_enabled"] for u in users] == [False]

    def test_same_event_stored_twice_is_read_once(self):
        event = _ms_event(0)
        stats = {}
        evidence = collect_evidence([event, event], stats)
        assert len(evidence) == 3
        assert stats["duplicate_events_skipped"] == 1

    def test_different_entities_are_all_kept(self):
        payload = _ms_payload(users=[_ms_user("u-1", "Dana Former"), _ms_user("u-2", "Lee Former")])
        evidence = collect_evidence([_ms_event(0, payload), _ms_event(60, payload)])
        users = sorted(e.source_id for e in evidence if e.kind == EvidenceKind.USER_ACCOUNT_STATUS)
        assert users == ["u-1", "u-2"]

    def test_evidence_without_an_id_is_never_merged_with_different_evidence(self):
        payload = _ms_payload(users=[_ms_user("", "No Id One"), _ms_user("", "No Id Two")], alerts=[], devices=[])
        evidence = collect_evidence([_ms_event(0, payload), _ms_event(60, payload)])
        # Two different users stay two; the older copy of each is still collapsed.
        assert sorted(e.payload["display_name"] for e in evidence) == ["No Id One", "No Id Two"]


class TestMoments:
    def test_three_syncs_give_one_moment_per_finding(self):
        moments, stats = evaluate_events([_ms_event(0), _ms_event(60), _ms_event(120)])
        texts = [m.translation.what_happened for m in moments]
        assert len(texts) == len(set(texts)) == 2, texts
        assert sum("Dana Former" in t for t in texts) == 1
        # The alert count is a number the reader acts on: one alert, not three.
        device = next(t for t in texts if "FRONT-DESK-01" in t)
        assert "has 1 active security warning" in device

    def test_identical_moments_collapse_and_are_counted(self):
        moments, _ = evaluate_events([_ms_event(0)])
        stats = {}
        merged = dedupe_moments(moments + moments, stats)
        assert [m.id for m in merged] == [m.id for m in moments]
        assert stats["duplicate_checks_collapsed"] == len(moments)

    def test_resolved_user_drops_out(self):
        newer = _ms_event(0, _ms_payload(users=[_ms_user("u-1", "Dana Former", enabled=False)], alerts=[]))
        older = _ms_event(60, _ms_payload(alerts=[]))
        moments, _ = evaluate_events([newer, older])
        assert moments == []


# ---------------------------------------------------------------------------
# Report built from stored telemetry
# ---------------------------------------------------------------------------

class TestReportFromStoredTelemetry:
    def _three_syncs(self, db):
        _org(db)
        for minutes_ago in (5, 65, 125):
            _store(db, _ms_event(minutes_ago), minutes_ago=minutes_ago)
        db.commit()

    def test_report_lists_each_finding_once(self, db_session):
        self._three_syncs(db_session)

        snapshot = build_template_snapshot(db_session, ORG, "technical_telemetry", demo=False)
        rows = flatten_findings(snapshot)
        labels = [r["label"] for r in rows]

        assert len(labels) == len(set(labels)) == 2, labels
        assert sum("Dana Former" in label for label in labels) == 1
        assert snapshot["findings_count"] == 2
        assert snapshot["readiness"]["checks_performed"] == 2
        assert snapshot["telemetry_event_count"] == 3
        assert snapshot["evidence_dedup"]["repeat_observations_collapsed"] == 6

    def test_generating_twice_gives_the_same_findings(self, db_session):
        self._three_syncs(db_session)
        first = flatten_findings(build_template_snapshot(db_session, ORG, "monthly_ops", demo=False))
        second = flatten_findings(build_template_snapshot(db_session, ORG, "monthly_ops", demo=False))
        assert [r["label"] for r in first] == [r["label"] for r in second]
        assert len(first) == 2

    def test_score_is_not_charged_once_per_copy(self, db_session):
        """Each failed check costs 15 points. Three copies of two findings used
        to cost 90; the two findings cost 30."""
        from app.models.connector import Connector

        self._three_syncs(db_session)
        db_session.add(Connector(
            org_id=ORG, connector_type="microsoft", display_name="Microsoft 365",
            status="active", health_status="healthy", last_sync_at=NOW,
            auth_method="oauth", created_by="test",
        ))
        db_session.commit()

        readiness, _source, _count, _stats = build_readiness_report(db_session, ORG, demo=False)
        assert len(readiness.failed_checks) == 2
        assert readiness.clinic_health_pct == 70

    def test_readiness_endpoint_and_report_agree(self, db_session, client):
        self._three_syncs(db_session)
        report, _source, _count, _stats = build_readiness_report(db_session, ORG, demo=False)
        resp = client.get(f"/api/clinic/readiness/{ORG}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        endpoint_labels = sorted(c["label"] for c in body["failed_checks"] + body["warnings"])
        assert endpoint_labels == sorted(_labels(report))
        assert len(endpoint_labels) == 2


# ---------------------------------------------------------------------------
# Ingestion: the same finding synced again is not stored again
# ---------------------------------------------------------------------------

FINDING_PAYLOAD = {
    "title": "S3 general purpose buckets should block public access",
    "severity_label": "high",
    "compliance_status": "FAILED",
    "record_state": "ACTIVE",
    "resources": ["arn:aws:s3:::clinic-backups"],
    "created_at": "2026-11-01T10:00:00.000Z",
    "updated_at": "2026-11-09T08:30:00.000Z",
}


def _finding_event(payload=None, timestamp=None):
    return NormalizedEvent(
        event_type="aws.securityhub.finding",
        source_system="aws_security_hub",
        source_event_id="arn:aws:securityhub:us-east-1:111122223333:finding/s3-1",
        severity="high",
        payload=dict(payload or FINDING_PAYLOAD),
        timestamp=timestamp,
    )


class TestIngestionIsIdempotent:
    def _sync(self, db, events):
        return asyncio.run(ConnectorManager(db, ORG)._ingest_events(None, events))

    def test_resyncing_an_unchanged_finding_stores_nothing_new(self, db_session):
        _org(db_session)
        for _ in range(3):  # on Save, by hand, hourly
            self._sync(db_session, [_finding_event()])

        assert db_session.query(TelemetryEvent).filter(TelemetryEvent.org_id == ORG).count() == 1
        assert db_session.query(EvidenceLedger).filter(EvidenceLedger.org_id == ORG).count() == 1
        assert db_session.query(NormalizedEvidenceRecord).filter(NormalizedEvidenceRecord.org_id == ORG).count() == 1

    def test_ledger_timestamp_is_the_findings_own_time_not_the_sync_time(self, db_session):
        _org(db_session)
        self._sync(db_session, [_finding_event()])
        entry = db_session.query(EvidenceLedger).filter(EvidenceLedger.org_id == ORG).one()
        assert entry.timestamp.replace(tzinfo=None) == datetime(2026, 11, 9, 8, 30)

    def test_a_finding_aws_updated_is_a_new_ledger_entry(self, db_session):
        _org(db_session)
        self._sync(db_session, [_finding_event()])
        changed = dict(FINDING_PAYLOAD, updated_at="2026-11-10T08:30:00.000Z", severity_label="critical")
        self._sync(db_session, [_finding_event(changed)])
        assert db_session.query(EvidenceLedger).filter(EvidenceLedger.org_id == ORG).count() == 2

    def test_finding_without_any_timestamp_is_still_stored_once(self, db_session):
        _org(db_session)
        bare = {k: v for k, v in FINDING_PAYLOAD.items() if k not in ("created_at", "updated_at")}
        for _ in range(3):
            self._sync(db_session, [_finding_event(bare)])
        assert db_session.query(EvidenceLedger).filter(EvidenceLedger.org_id == ORG).count() == 1

    def test_an_event_with_its_own_timestamp_keeps_it(self, db_session):
        _org(db_session)
        stamp = "2026-11-11T12:00:00+00:00"
        self._sync(db_session, [_finding_event(timestamp=stamp)])
        entry = db_session.query(EvidenceLedger).filter(EvidenceLedger.org_id == ORG).one()
        assert entry.timestamp.replace(tzinfo=None) == datetime(2026, 11, 11, 12, 0)


# ---------------------------------------------------------------------------
# An item the source keeps reporting stays visible, with its current result
# ---------------------------------------------------------------------------

def _backup_event(result="Success"):
    return NormalizedEvent(
        event_type="veeam.backup_job",
        source_system="veeam",
        source_event_id="veeam-job-1",
        severity="info",
        payload={"system_name": "Patient Database Server", "last_result": result},
    )


def _age_rows(db, hours):
    """Pretend every stored row was first stored `hours` ago."""
    from datetime import timedelta, timezone
    old = datetime.now(timezone.utc) - timedelta(hours=hours)
    db.query(TelemetryEvent).filter(TelemetryEvent.org_id == ORG).update({"created_at": old})
    db.commit()


class TestReportedItemsStayCurrent:
    """Connectors give a finding, a backup job or an agent the same id on every
    sync. The stored copy used to be written once and never touched again, so
    it kept its first result and left every 24-hour view a day later."""

    def _sync(self, db, events):
        return asyncio.run(ConnectorManager(db, ORG)._ingest_events(None, events))

    def _feed(self, db):
        from app.api.clinic.router import _fetch_persisted_telemetry
        return _fetch_persisted_telemetry(db, ORG)

    def test_item_still_reported_after_a_day_stays_in_the_readiness_feed(self, db_session):
        _org(db_session)
        self._sync(db_session, [_finding_event()])
        _age_rows(db_session, 30)
        assert self._feed(db_session) == []  # nothing has reported it since

        self._sync(db_session, [_finding_event()])  # the source still reports it

        feed = self._feed(db_session)
        assert len(feed) == 1
        assert db_session.query(TelemetryEvent).filter(TelemetryEvent.org_id == ORG).count() == 1
        seen = datetime.fromisoformat(feed[0].timestamp)
        assert (datetime.now(seen.tzinfo) - seen).total_seconds() < 120

    def test_item_the_source_stopped_reporting_drops_out_after_a_day(self, db_session):
        _org(db_session)
        self._sync(db_session, [_finding_event()])
        self._sync(db_session, [_finding_event()])
        from datetime import timedelta, timezone
        old = datetime.now(timezone.utc) - timedelta(hours=30)
        db_session.query(TelemetryEvent).filter(TelemetryEvent.org_id == ORG).update(
            {"created_at": old, "last_seen_at": old})
        db_session.commit()
        assert self._feed(db_session) == []

    def test_a_changed_result_replaces_the_stored_one(self, db_session):
        _org(db_session)
        self._sync(db_session, [_backup_event("Success")])
        self._sync(db_session, [_backup_event("Failed")])

        rows = db_session.query(TelemetryEvent).filter(TelemetryEvent.org_id == ORG).all()
        assert len(rows) == 1
        feed = self._feed(db_session)
        assert feed[0].payload["last_result"] == "Failed"

    def test_insurance_answers_read_the_time_the_item_was_last_reported(self, db_session):
        from datetime import timezone
        from app.services.questionnaires.insurance_answers import load_persisted_events
        _org(db_session)
        self._sync(db_session, [_backup_event("Success")])
        _age_rows(db_session, 30)
        self._sync(db_session, [_backup_event("Success")])

        now = datetime.now(timezone.utc)
        events = load_persisted_events(db_session, ORG, now)
        assert len(events) == 1
        stamp = datetime.fromisoformat(events[0].timestamp)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        assert (now - stamp).total_seconds() < 120
