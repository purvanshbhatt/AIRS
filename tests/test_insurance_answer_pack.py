"""
Insurance questionnaire answer pack: mapping rules, guard-rails and API.

The rules under test (``app/services/questionnaires/insurance_answers.py``):
  * fresh evidence from a healthy connector gives yes / no / partial with the
    source and the time it was observed;
  * no evidence, a connector in error / waiting for sign-in, a connector that
    has not synced recently, or evidence older than the freshness bound gives
    ``not_verified`` and never the last good value;
  * questions no telemetry can answer are ``human_only``;
  * Security Hub absence-of-failure is never read as a pass.
"""
from __future__ import annotations

import io
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest

from app.core.auth import User, get_optional_user
from app.models.organization import Organization
from app.services.clinic_engine.v2.schema import RawEvent
from app.services.questionnaires import insurance_answers as ia
from app.services.questionnaires.insurance_bank import (
    HUMAN,
    QUESTION_BANK_VERSION,
    QUESTIONS,
    TELEMETRY,
)

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
ORG = "org-ins-1"


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def ev(event_type: str, payload: Dict[str, Any], at: datetime = NOW - timedelta(hours=1),
       source_event_id: Optional[str] = None, source_system: Optional[str] = None) -> RawEvent:
    return RawEvent(
        event_type=event_type,
        source_system=source_system or event_type.split(".")[0],
        source_event_id=source_event_id or f"{event_type}-{at.isoformat()}",
        organization_id=ORG,
        payload=payload,
        timestamp=at.isoformat(),
    )


def conn(ctype: str, status: str = "active", synced: Optional[datetime] = NOW - timedelta(hours=1),
         name: Optional[str] = None, error: Optional[str] = None) -> ia.ConnectorState:
    return ia.ConnectorState(connector_type=ctype, name=name or ctype.title(), status=status,
                             last_sync_at=synced, error_message=error)


def ms_event(users: List[Dict[str, Any]], devices: Optional[List[Dict[str, Any]]] = None,
             alerts: Optional[List[Dict[str, Any]]] = None, at: datetime = NOW - timedelta(hours=1)) -> RawEvent:
    return ev("microsoft.telemetry", {"entra_users": users, "intune_devices": devices or [],
                                      "defender_alerts": alerts or []}, at=at)


def user(uid: str, mfa: bool, last_sign_in: datetime = NOW - timedelta(days=1), enabled: bool = True) -> Dict[str, Any]:
    return {"user_id": uid, "user_principal_name": f"{uid}@clinic.test", "mfa_enforced": mfa,
            "account_enabled": enabled, "last_sign_in": last_sign_in.isoformat()}


def finding(control: str, title: str, status: str = "FAILED", sample: bool = False,
            at: datetime = NOW - timedelta(hours=2), product: str = "Security Hub") -> RawEvent:
    return ev("aws.securityhub.finding", {
        "title": title, "compliance_status": status, "record_state": "ACTIVE",
        "generator_id": f"security-control/{control}", "product_name": product,
        "severity_label": "high", "sample": sample, "resources": [f"arn:aws:ec2:us-east-1:1:volume/{control}"],
    }, at=at, source_event_id=f"finding-{control}-{title}", source_system="aws_security_hub")


def pack_for(events: List[RawEvent], connectors: List[ia.ConnectorState], demo: bool = False) -> Dict[str, Any]:
    snapshot = ia.EvidenceSnapshot(org_id=ORG, events=events, connectors=connectors, demo=demo, now=NOW)
    return ia.build_pack(snapshot, {"id": ORG, "name": "Test Clinic"})


def answer(pack: Dict[str, Any], qid: str) -> Dict[str, Any]:
    return next(a for a in pack["answers"] if a["id"] == qid)


# ---------------------------------------------------------------------------
# Question bank
# ---------------------------------------------------------------------------

class TestQuestionBank:
    def test_size_version_and_unique_ids(self):
        assert 25 <= len(QUESTIONS) <= 40
        assert len({q.id for q in QUESTIONS}) == len(QUESTIONS)
        assert QUESTION_BANK_VERSION

    def test_every_telemetry_question_has_a_rule_and_sources(self):
        for q in QUESTIONS:
            if q.mode == TELEMETRY:
                assert q.id in ia.RULES
                assert q.sources and all(s in ia.SOURCES for s in q.sources)
            else:
                assert q.mode == HUMAN and q.human_reason
                assert q.id not in ia.RULES

    def test_required_topics_are_covered(self):
        ids = {q.id for q in QUESTIONS}
        for required in ("EMAIL_MFA", "ADMIN_MFA", "REMOTE_ACCESS_MFA", "BACKUP_OFFLINE_COPY", "BACKUP_DAILY",
                         "BACKUP_LAST_RUN", "RESTORE_TESTED", "ENDPOINT_PROTECTION", "SUPPORTED_SOFTWARE",
                         "DEVICE_ENCRYPTION", "REMOTE_PORTS_CLOSED", "SECURITY_MONITORING", "IR_PLAN",
                         "SECURITY_TRAINING", "VENDOR_REVIEW"):
            assert required in ids


# ---------------------------------------------------------------------------
# Guard-rails
# ---------------------------------------------------------------------------

class TestGuardRails:
    def test_nothing_connected_gives_not_verified_and_human_only(self):
        pack = pack_for([], [])
        for a in pack["answers"]:
            q = next(q for q in QUESTIONS if q.id == a["id"])
            expected = ia.HUMAN_ONLY if q.mode == HUMAN else ia.NOT_VERIFIED
            assert a["value"] == expected, a["id"]
            assert a["evidence_source"] is None and a["evidence_time"] is None
        assert answer(pack, "EMAIL_MFA")["value_label"] == "Not verified: answer manually"
        assert "not connected" in answer(pack, "EMAIL_MFA")["basis"]

    def test_fresh_evidence_from_healthy_connector_answers_with_source_and_time(self):
        observed = NOW - timedelta(hours=3)
        pack = pack_for([ms_event([user("a", True), user("b", True)], at=observed)], [conn("microsoft")])
        a = answer(pack, "EMAIL_MFA")
        assert a["value"] == ia.YES
        assert a["evidence_source"] == "Microsoft 365"
        assert ia.parse_time(a["evidence_time"]) == observed
        assert a["coverage"]["checked"] == ["Microsoft 365: 2 switched-on user accounts"]
        assert any("not in Microsoft 365" in s for s in a["coverage"]["not_checked"])

    def test_stale_evidence_gives_not_verified_never_the_last_good_value(self):
        old = NOW - timedelta(hours=72)
        pack = pack_for([ms_event([user("a", True)], at=old)], [conn("microsoft")])
        a = answer(pack, "EMAIL_MFA")
        assert a["value"] == ia.NOT_VERIFIED
        assert "freshness limit" in a["basis"]
        assert "enforced" not in a["basis"]  # the old, good-looking value is not shown
        assert a["evidence_source"] is None and a["evidence_time"] is None

    def test_connector_that_has_not_synced_recently_gives_not_verified(self):
        pack = pack_for([ms_event([user("a", True)])], [conn("microsoft", synced=NOW - timedelta(days=5))])
        a = answer(pack, "EMAIL_MFA")
        assert a["value"] == ia.NOT_VERIFIED
        assert "last synced" in a["basis"]

    @pytest.mark.parametrize("status,phrase", [
        ("error", "is failing"),
        ("pending_auth", "waiting for sign-in"),
        ("inactive", "switched off"),
    ])
    def test_failed_connector_gives_not_verified_even_with_fresh_data(self, status, phrase):
        connectors = [conn("microsoft", status=status, name="Microsoft 365", error="401 Unauthorized")]
        pack = pack_for([ms_event([user("a", True)])], connectors)
        a = answer(pack, "EMAIL_MFA")
        assert a["value"] == ia.NOT_VERIFIED
        assert phrase in a["basis"]
        assert "Answer this question yourself" in a["basis"]
        assert a["evidence_source"] is None
        src = next(s for s in pack["sources"] if s["source"] == "microsoft")
        assert src["state"] == "failed"

    def test_one_failed_source_blocks_a_multi_source_answer(self):
        events = [ms_event([user("a", True)])]
        pack = pack_for(events, [conn("microsoft"), conn("aws", status="error", error="AccessDenied")])
        a = answer(pack, "DORMANT_ACCOUNTS")
        assert a["value"] == ia.NOT_VERIFIED
        assert "AccessDenied" in a["basis"]

    def test_telemetry_without_a_connector_is_ignored_for_real_orgs(self):
        pack = pack_for([ms_event([user("a", True)])], [])
        assert answer(pack, "EMAIL_MFA")["value"] == ia.NOT_VERIFIED

    def test_connected_but_no_data_for_the_question(self):
        pack = pack_for([], [conn("microsoft")])
        a = answer(pack, "EMAIL_MFA")
        assert a["value"] == ia.NOT_VERIFIED
        assert "sent no data" in a["basis"]

    def test_human_only_questions_never_take_evidence(self):
        events = [ms_event([user("a", True)])]
        pack = pack_for(events, [conn("microsoft")])
        for qid in ("IR_PLAN", "SECURITY_TRAINING", "VENDOR_REVIEW", "BACKUP_OFFLINE_COPY", "RESTORE_TESTED"):
            a = answer(pack, qid)
            assert a["value"] == ia.HUMAN_ONLY
            assert a["value_label"] == "You answer this"
            assert a["evidence_source"] is None

    def test_deterministic(self):
        events = [ms_event([user("a", True), user("b", False)]), finding("EC2.3", "Attached EBS volumes should be encrypted")]
        connectors = [conn("microsoft"), conn("aws")]
        assert pack_for(events, connectors) == pack_for(events, connectors)


# ---------------------------------------------------------------------------
# Mapping rules
# ---------------------------------------------------------------------------

class TestMappingRules:
    def test_email_mfa_three_levels(self):
        def value(users):
            return answer(pack_for([ms_event(users)], [conn("microsoft")]), "EMAIL_MFA")["value"]
        assert value([user("a", True), user("b", True)]) == ia.YES
        assert value([user("a", True), user("b", False)]) == ia.PARTIAL
        assert value([user("a", False)]) == ia.NO
        # Switched-off accounts are not counted.
        assert value([user("a", True), user("b", False, enabled=False)]) == ia.YES

    def test_dormant_accounts_reuse_the_unused_account_rule(self):
        users = [user("a", True), user("gone", True, last_sign_in=NOW - timedelta(days=45))]
        a = answer(pack_for([ms_event(users)], [conn("microsoft")]), "DORMANT_ACCOUNTS")
        assert a["value"] == ia.NO
        assert "gone@clinic.test" in a["basis"]

    def test_admin_mfa_from_aws_credential_report(self):
        report = ev("aws.iam.credential_report", {"account_id": "1", "iam_users": [
            {"user_id": "root", "user_name": "<root_account>", "mfa_enforced": True, "account_enabled": True},
            {"user_id": "u1", "user_name": "alice", "mfa_enforced": False, "password_enabled": True},
            {"user_id": "u2", "user_name": "ci-bot", "mfa_enforced": False, "password_enabled": False},
        ]}, source_event_id="aws-iam-report-1-2026111111", source_system="aws")
        a = answer(pack_for([report], [conn("aws")]), "ADMIN_MFA")
        assert a["value"] == ia.PARTIAL
        assert "alice" in a["basis"] and "ci-bot" not in a["basis"]

    def test_access_keys_rotation(self):
        def report(rotated):
            return ev("aws.iam.credential_report", {"account_id": "1", "iam_users": [
                {"user_id": "u1", "user_name": "alice", "access_key_active": True,
                 "access_key_last_rotated": rotated.isoformat()}]}, source_system="aws")
        assert answer(pack_for([report(NOW - timedelta(days=10))], [conn("aws")]), "ACCESS_KEYS_ROTATED")["value"] == ia.YES
        assert answer(pack_for([report(NOW - timedelta(days=200))], [conn("aws")]), "ACCESS_KEYS_ROTATED")["value"] == ia.NO

    def test_backup_daily_and_last_run(self):
        def job(name, last_ok, status):
            return ev("veeam.backup_job", {"system_name": name, "job_id": name,
                                           "last_successful_backup": last_ok.isoformat() if last_ok else None,
                                           "status": status}, source_event_id=f"veeam-{name}")
        fresh = pack_for([job("EHR", NOW - timedelta(hours=3), "Success")], [conn("veeam")])
        assert answer(fresh, "BACKUP_DAILY")["value"] == ia.YES
        assert "most recent successful backup" in answer(fresh, "BACKUP_DAILY")["basis"]
        assert answer(fresh, "BACKUP_LAST_RUN")["value"] == ia.YES

        mixed = pack_for([job("EHR", NOW - timedelta(hours=3), "Success"), job("Files", NOW - timedelta(hours=30), "Failed")],
                         [conn("veeam")])
        assert answer(mixed, "BACKUP_DAILY")["value"] == ia.PARTIAL
        assert answer(mixed, "BACKUP_LAST_RUN")["value"] == ia.PARTIAL
        assert "Files" in answer(mixed, "BACKUP_LAST_RUN")["basis"]

    def test_device_encryption_and_compliance_from_intune(self):
        devices = [{"device_id": "d1", "device_name": "FRONT-DESK", "bitlocker_status": "not_encrypted",
                    "compliance_state": "noncompliant"},
                   {"device_id": "d2", "device_name": "OFFICE-2", "bitlocker_status": "encrypted",
                    "compliance_state": "compliant"}]
        pack = pack_for([ms_event([user("a", True)], devices=devices)], [conn("microsoft")])
        assert answer(pack, "DEVICE_ENCRYPTION")["value"] == ia.PARTIAL
        assert "FRONT-DESK" in answer(pack, "DEVICE_ENCRYPTION")["basis"]
        assert answer(pack, "DEVICES_MANAGED")["value"] == ia.PARTIAL

    def test_security_hub_failures_only_never_read_as_a_pass(self):
        unrelated = finding("IAM.14", "Ensure IAM password policy requires at least one number")
        pack = pack_for([unrelated], [conn("aws")])
        a = answer(pack, "CLOUD_ENCRYPTION")
        assert a["value"] == ia.NOT_VERIFIED
        assert "only receives failed checks" in a["basis"]

        pack = pack_for([finding("EC2.3", "Attached EBS volumes should be encrypted at-rest")], [conn("aws")])
        a = answer(pack, "CLOUD_ENCRYPTION")
        assert a["value"] == ia.NO and "EC2.3" in a["basis"]

    def test_remote_ports_from_network_snapshot(self):
        def snapshot(ports):
            return ev("aws.network.snapshot", {"security_groups": [
                {"id": "sg-1", "name": "web", "open_ports": ["tcp/443"]},
                {"id": "sg-2", "name": "admin", "open_ports": ports}]}, source_system="aws")
        closed = pack_for([snapshot(["tcp/80"])], [conn("aws")])
        assert answer(closed, "REMOTE_PORTS_CLOSED")["value"] == ia.YES
        open_rdp = pack_for([snapshot(["tcp/3380-3390"])], [conn("aws")])
        a = answer(open_rdp, "REMOTE_PORTS_CLOSED")
        assert a["value"] == ia.NO and "admin" in a["basis"] and "RDP" in a["basis"]

    @pytest.mark.parametrize("entry,port,expected", [
        ("tcp/22", 22, True), ("tcp/0-1024", 22, True), ("tcp/all", 3389, True), ("all", 22, True),
        ("tcp/443", 22, False), ("udp/3389", 3389, False), ("icmp", 22, False), ("tcp/3390-4000", 3389, False),
    ])
    def test_port_open(self, entry, port, expected):
        assert ia.port_open(entry, port) is expected

    def test_sample_findings_are_not_evidence(self):
        gd = finding("x", "EC2 instance queried a known C2 domain", status="", sample=True, product="GuardDuty")
        assert answer(pack_for([gd], [conn("aws")]), "CLOUD_THREAT_DETECTION")["value"] == ia.NOT_VERIFIED
        real = finding("y", "EC2 instance queried a known C2 domain", status="", product="GuardDuty")
        assert answer(pack_for([real], [conn("aws")]), "CLOUD_THREAT_DETECTION")["value"] == ia.YES

    def test_monitoring_any_source_is_enough(self):
        agents = [ev("wazuh.agent_status", {"agent_id": "001", "name": "pc-1", "status": "active"},
                     source_event_id="agent-status-001")]
        pack = pack_for(agents, [conn("wazuh")])
        assert answer(pack, "SECURITY_MONITORING")["value"] == ia.YES
        assert answer(pack, "ENDPOINT_PROTECTION")["value"] == ia.YES

    def test_critical_vulns_need_scan_results(self):
        agents = ev("wazuh.agent_status", {"agent_id": "001", "status": "active"}, source_event_id="agent-status-001")
        pack = pack_for([agents], [conn("wazuh")])
        assert answer(pack, "CRITICAL_VULNS_PATCHED")["value"] == ia.NOT_VERIFIED
        vuln = ev("wazuh.vulnerability", {"agent_id": "001", "cve": "CVE-2026-0001", "severity": "Critical",
                                          "status": "Active"}, source_event_id="vuln-001-CVE-2026-0001")
        pack = pack_for([agents, vuln], [conn("wazuh")])
        a = answer(pack, "CRITICAL_VULNS_PATCHED")
        assert a["value"] == ia.NO and "CVE-2026-0001" in a["basis"]


# ---------------------------------------------------------------------------
# Pack shape and demo
# ---------------------------------------------------------------------------

class TestPack:
    def test_summary_counts_and_notice(self):
        pack = pack_for([ms_event([user("a", True)])], [conn("microsoft")])
        summary = pack["summary"]
        assert set(summary["counts"]) == set(ia.ANSWER_VALUES)
        assert sum(summary["counts"].values()) == summary["total"] == len(QUESTIONS)
        assert summary["question_bank_version"] == QUESTION_BANK_VERSION
        assert summary["generated_at"] == NOW.isoformat()
        assert pack["notice"] == "You attest. ResilAI shows the evidence it has, as of 11 Nov 2026, 12:00 UTC."
        assert pack["attestation"]["submitted_by_resilai"] is False
        assert pack["is_demo"] is False and pack["data_label"] == "Live data"

    def test_demo_pack_is_labelled_sample_data(self):
        events = ia.load_demo_events("demo-health-org", NOW)
        snapshot = ia.EvidenceSnapshot(org_id="demo-health-org", events=events, connectors=[], demo=True, now=NOW)
        pack = ia.build_pack(snapshot)
        assert pack["is_demo"] is True
        assert pack["data_label"] == "Sample data"
        assert pack["organization"]["is_demo"] is True
        assert pack["summary"]["from_evidence"] > 0
        assert answer(pack, "IR_PLAN")["value"] == ia.HUMAN_ONLY


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

OWNER = User(uid="ins-owner", email="owner@example.com", name="Owner")
STRANGER = User(uid="ins-stranger", email="stranger@example.com", name="Stranger")


def _as(client, user_):
    async def override():
        return user_
    client.app.dependency_overrides[get_optional_user] = override


@pytest.fixture
def owned_org(db_session):
    org = Organization(id="ins-org-1", name="Insured Clinic", owner_uid=OWNER.uid)
    db_session.add(org)
    db_session.commit()
    return org


def _add_connector(db_session, org_id, status="active", error=None):
    from app.models.connector import Connector, ConnectorAuthMethod, ConnectorStatus, ConnectorType
    c = Connector(org_id=org_id, connector_type=ConnectorType.microsoft, display_name="Microsoft 365",
                  auth_method=ConnectorAuthMethod.oauth, status=ConnectorStatus(status),
                  health_status="healthy", last_sync_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                  error_message=error)
    db_session.add(c)
    db_session.commit()
    return c


def _add_ms_telemetry(db_session, org_id, users):
    from app.models.telemetry_event import TelemetryEvent
    db_session.add(TelemetryEvent(
        org_id=org_id, event_type="microsoft.telemetry", source_system="microsoft",
        source_event_id="sync-ms-1", payload_hash="a" * 64, severity="info",
        payload=json.dumps({"entra_users": users, "intune_devices": [], "defender_alerts": []}),
        created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
    ))
    db_session.commit()


class TestInsuranceEndpoint:
    def test_demo_org_readable_without_token(self, client):
        resp = client.get("/api/v1/questionnaires/insurance", params={"org_id": "demo-health-org"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_demo"] is True and body["data_label"] == "Sample data"
        assert body["summary"]["question_bank_version"] == QUESTION_BANK_VERSION
        assert body["summary"]["total"] == len(body["answers"]) == len(QUESTIONS)
        assert body["notice"].startswith("You attest. ResilAI shows the evidence it has, as of ")
        for a in body["answers"]:
            assert a["value"] in ia.ANSWER_VALUES
            assert {"basis", "evidence_source", "evidence_time", "coverage"} <= set(a)

    def test_real_org_answers_from_persisted_telemetry(self, client, db_session, owned_org):
        _add_connector(db_session, owned_org.id)
        _add_ms_telemetry(db_session, owned_org.id, [
            {"user_id": "u1", "user_principal_name": "a@clinic.test", "mfa_enforced": True, "account_enabled": True,
             "last_sign_in": datetime.now(timezone.utc).isoformat()},
        ])
        _as(client, OWNER)
        body = client.get("/api/v1/questionnaires/insurance", params={"org_id": owned_org.id}).json()
        a = answer(body, "EMAIL_MFA")
        assert a["value"] == "yes"
        assert a["evidence_source"] == "Microsoft 365" and a["evidence_time"]
        assert body["is_demo"] is False and body["organization"]["name"] == "Insured Clinic"

    def test_failed_connector_gives_not_verified_through_the_api(self, client, db_session, owned_org):
        _add_connector(db_session, owned_org.id, status="error", error="Token expired")
        _add_ms_telemetry(db_session, owned_org.id, [
            {"user_id": "u1", "user_principal_name": "a@clinic.test", "mfa_enforced": True, "account_enabled": True},
        ])
        _as(client, OWNER)
        body = client.get("/api/v1/questionnaires/insurance", params={"org_id": owned_org.id}).json()
        a = answer(body, "EMAIL_MFA")
        assert a["value"] == "not_verified"
        assert "Token expired" in a["basis"]

    def test_foreign_org_is_not_found(self, client, owned_org):
        _as(client, STRANGER)
        resp = client.get("/api/v1/questionnaires/insurance", params={"org_id": owned_org.id})
        assert resp.status_code == 404

    def test_missing_org_id_is_rejected(self, client):
        assert client.get("/api/v1/questionnaires/insurance").status_code == 422

    def test_pdf_has_notice_on_first_page_and_blank_signature_block(self, client):
        from pypdf import PdfReader

        resp = client.get("/api/v1/questionnaires/insurance/pdf", params={"org_id": "demo-health-org"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert "attachment" in resp.headers["content-disposition"]
        pages = PdfReader(io.BytesIO(resp.content)).pages
        first = " ".join(pages[0].extract_text().split())
        assert "You attest. ResilAI shows the evidence it has, as of" in first
        assert "SAMPLE DATA" in first
        last = " ".join(pages[-1].extract_text().split())
        assert "Attestation and signature" in last
        assert "Signature" in last and "Date" in last
