"""
Regression: the first report generated from a real AWS account repeated its
findings. One failing AWS check on seven subnets printed seven identical rows,
every IAM user appeared once per connector sync, and the timeline restated
the same findings a second time.

These tests pin the behaviour from stored telemetry through to the PDF.
"""
import io
import os

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENV", "local")

from app.reports.templates import collapse_duplicate_rows, render_pdf
from app.services.clinic_engine.v2.engine import ClinicEvaluationEngine
from app.services.clinic_engine.v2.providers.aws_provider import AWSProvider, resource_label
from app.services.clinic_engine.v2.schema import RawEvent, Verdict

ORG = "org-aws-report"
ACCOUNT = "111122223333"
SUBNET_TITLE = "EC2 subnets should not automatically assign public IP addresses"
GUARDDUTY_TITLE = "Potential credential compromise of Root/example indicated by a sequence of actions."


def _finding(finding_id, title, resource, severity="medium", compliance="FAILED", **extra):
    payload = {
        "title": title,
        "severity_label": severity,
        "compliance_status": compliance,
        "record_state": "ACTIVE",
        "resources": [resource],
        "product_name": "Security Hub",
    }
    payload.update(extra)
    return RawEvent(
        event_type="aws.securityhub.finding",
        source_system="aws_security_hub",
        source_event_id=finding_id,
        organization_id=ORG,
        payload=payload,
    )


def _iam_report(hour, users):
    return RawEvent(
        event_type="aws.iam.credential_report",
        source_system="aws",
        source_event_id=f"aws-iam-report-{ACCOUNT}-20261111{hour:02d}",
        organization_id=ORG,
        payload={"iam_users": users, "user_count": len(users), "account_id": ACCOUNT},
    )


def _iam_user(name, **extra):
    user = {
        "user_id": f"arn:aws:iam::{ACCOUNT}:user/{name}",
        "user_name": name,
        "display_name": name,
        "account_enabled": True,
        "last_sign_in": None,
    }
    user.update(extra)
    return user


def _moments(events):
    return ClinicEvaluationEngine().evaluate(AWSProvider.extract(events))


def _subnet_findings(count=7):
    return [
        _finding(
            f"arn:aws:securityhub:us-east-1:{ACCOUNT}:finding/subnet-{i}",
            SUBNET_TITLE,
            f"arn:aws:ec2:us-east-1:{ACCOUNT}:subnet/subnet-0{i}",
        )
        for i in range(count)
    ]


class TestOneRowPerCheck:
    def test_same_check_on_seven_resources_is_one_item(self):
        moments = _moments(_subnet_findings(7))

        assert len(moments) == 1
        moment = moments[0]
        assert moment.capability_id == "cloud_posture"
        assert moment.verdict == Verdict.CONCERN
        text = moment.translation.what_happened
        assert SUBNET_TITLE in text
        assert "on 7 resources" in text
        assert "subnet-00, subnet-01, subnet-02 and 4 more" in text

    def test_single_resource_is_named_without_a_plural(self):
        text = _moments(_subnet_findings(1))[0].translation.what_happened
        assert "on 1 resource (subnet-00)" in text

    def test_a_finding_stored_twice_is_counted_once(self):
        events = _subnet_findings(2)
        moments = _moments(events + events)
        assert len(moments) == 1
        assert "on 2 resources" in moments[0].translation.what_happened

    def test_different_checks_stay_separate(self):
        events = _subnet_findings(2) + [
            _finding("f-s3", "S3 general purpose buckets should require requests to use TLS",
                     "arn:aws:s3:::clinic-backups"),
        ]
        labels = [m.translation.what_happened for m in _moments(events)]
        assert len(labels) == 2
        assert len(set(labels)) == 2

    def test_threat_alerts_are_grouped_and_urgent(self):
        events = [
            _finding(f"gd-{i}", GUARDDUTY_TITLE, f"arn:aws:iam::{ACCOUNT}:root",
                     severity="high", compliance="", product_name="GuardDuty")
            for i in range(6)
        ]
        moments = _moments(events)
        assert len(moments) == 1
        assert moments[0].verdict == Verdict.CRITICAL
        text = moments[0].translation.what_happened
        assert text.startswith("AWS threat detection alert:")
        assert "6 alerts" in text

    def test_passed_and_low_severity_findings_are_not_reported(self):
        events = [
            _finding("f-pass", "A check that passes", "arn:aws:s3:::ok", compliance="PASSED"),
            _finding("f-low", "A low severity notice", "arn:aws:s3:::ok", severity="low", compliance=""),
        ]
        assert _moments(events) == []

    def test_finding_title_is_never_presented_as_a_device(self):
        """The old wording was '<check title> has 7 active security warnings'
        with the reason 'If this device is compromised...'."""
        for moment in _moments(_subnet_findings(3)):
            assert moment.capability_id != "device_compromise"
            assert "device" not in moment.translation.why_care.lower()
            assert "security warnings" not in moment.translation.what_happened

    def test_sample_findings_are_labelled_as_test_data(self):
        events = [_finding("gd-sample", GUARDDUTY_TITLE, f"arn:aws:iam::{ACCOUNT}:root",
                           severity="high", compliance="", sample=True)]
        translation = _moments(events)[0].translation
        assert translation.what_happened.startswith("Sample finding (AWS test data).")
        assert "does not describe real activity" in translation.why_care

    def test_owner_is_the_aws_administrator(self):
        from app.services.clinic_engine.v2.action_engine import ActionEngine
        from app.services.clinic_engine.v2.contracts import ClinicContext
        from app.services.clinic_engine.v2.risk_engine import BusinessRiskEngine

        moment = _moments(_subnet_findings(2))[0]
        context = ClinicContext(org_id=ORG, clinic_name="Test")
        risk = BusinessRiskEngine(None).assess_moment(moment, context)
        cards = ActionEngine().build_action_cards(moment, risk, context)
        assert cards[0].category == "cloud_security"
        assert cards[0].required_permissions == ["AWS administrator"]
        assert cards[0].fix_now_available is False


class TestIamUsersAreListedOnce:
    def test_user_in_three_hourly_reports_is_one_item(self):
        events = [_iam_report(hour, [_iam_user("Devyani")]) for hour in (15, 16, 17)]
        moments = _moments(events)
        assert len(moments) == 1
        assert "Devyani" in moments[0].translation.what_happened

    def test_no_made_up_zero_days(self):
        text = _moments([_iam_report(17, [_iam_user("Devyani")])])[0].translation.what_happened
        assert "0 days" not in text
        assert "has no sign-in on record" in text

    def test_only_the_newest_report_counts(self):
        """A user deleted since the earlier sync must not linger."""
        events = [
            _iam_report(15, [_iam_user("Devyani"), _iam_user("deleted-user")]),
            _iam_report(17, [_iam_user("Devyani")]),
        ]
        texts = [m.translation.what_happened for m in _moments(events)]
        assert len(texts) == 1
        assert "deleted-user" not in texts[0]

    def test_brand_new_unused_account_is_not_flagged(self):
        from datetime import datetime, timezone
        created = datetime.now(timezone.utc).isoformat()
        assert _moments([_iam_report(17, [_iam_user("new-key", created_at=created)])]) == []

    def test_aws_account_is_not_sent_to_the_microsoft_365_admin(self):
        moment = _moments([_iam_report(17, [_iam_user("Devyani")])])[0]
        assert moment.actions[0].action_id == "review_cloud_account"
        assert moment.actions[0].can_automate is False
        assert "AWS account" in moment.translation.why_care
        assert "patient records" not in moment.translation.why_care


class TestResourceLabel:
    def test_labels(self):
        cases = {
            f"arn:aws:ec2:us-east-1:{ACCOUNT}:subnet/subnet-0abc": "subnet-0abc",
            "arn:aws:s3:::clinic-backups": "clinic-backups",
            f"AWS::::Account:{ACCOUNT}": f"account {ACCOUNT}",
            f"arn:aws:iam::{ACCOUNT}:user/Devyani": "Devyani",
            f"arn:aws:cloudformation:us-east-1:{ACCOUNT}:stack/my-stack/0f1e2d3c": "my-stack",
            f"arn:aws:secretsmanager:us-east-1:{ACCOUNT}:secret:app/key-AbCdEf": "key-AbCdEf",
            "i-0123456789": "i-0123456789",
            "": "",
        }
        for raw, expected in cases.items():
            assert resource_label(raw) == expected, raw


class TestReportDoesNotRepeatItself:
    def _row(self, label, severity="warning"):
        return {"severity": severity, "label": label, "detail": "why", "owner": "AWS administrator"}

    def test_identical_rows_merge_with_a_count(self):
        rows = collapse_duplicate_rows([self._row("A"), self._row("B"), self._row("A"), self._row("A")])
        assert [r["label"] for r in rows] == ["A (reported 3 times)", "B"]

    def test_rows_that_differ_are_kept(self):
        rows = collapse_duplicate_rows([self._row("A"), self._row("A", severity="fail")])
        assert len(rows) == 2

    def test_monthly_report_lists_each_finding_once(self):
        from pypdf import PdfReader

        check = {
            "label": 'AWS security check failing: "Uniquecheckname" on 7 resources (a, b, c and 4 more).',
            "detail": "A setting in your AWS account does not meet the AWS security baseline.",
            "action": {"category": "cloud_security", "required_permissions": ["AWS administrator"]},
            "verification": {},
        }
        snapshot = {
            "organization": {"name": "Test"},
            "generated_at": "2026-11-11T17:59:00+00:00",
            "overall_score": 40,
            "findings_count": 1,
            "evidence_hash": "0" * 64,
            "connectors": [],
            "readiness": {
                "status": "action_needed",
                "warnings": [check],
                "failed_checks": [],
                "passed_checks": [],
                "unknowns": [],
                "checks_performed": 1,
                "timeline": [
                    # restates the finding above: must not print a second time
                    {"timestamp": "2026-11-11T17:59:00+00:00", "label": check["label"], "source": "ResilAI checks"},
                    {"timestamp": "2026-11-11T16:28:00+00:00", "label": "Amazon Web Services sent fresh data",
                     "source": "Amazon Web Services"},
                ],
            },
        }
        pdf = render_pdf("monthly_ops", snapshot)
        text = " ".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
        text = " ".join(text.split())

        assert text.count("Uniquecheckname") == 1
        assert "Amazon Web Services sent fresh data" in text
        assert "AWS administrator" in text


class TestEndToEndFromStoredTelemetry:
    """Stored telemetry -> readiness pipeline -> generated report, as the
    Reports page runs it."""

    def test_generated_report_has_one_item_per_check(self, db_session, client_with_org):
        import hashlib
        import json
        from unittest.mock import patch

        from app.models.telemetry_event import TelemetryEvent

        org_id = "test-org-123"  # provisioned by the client_with_org fixture
        events = _subnet_findings(7) + [_iam_report(h, [_iam_user("Devyani")]) for h in (15, 16, 17)]
        for event in events:
            db_session.add(TelemetryEvent(
                org_id=org_id,
                event_type=event.event_type,
                source_system=event.source_system,
                source_event_id=event.source_event_id,
                payload_hash=hashlib.sha256(json.dumps(event.payload, sort_keys=True).encode()).hexdigest(),
                payload=json.dumps(event.payload),
            ))
        db_session.commit()

        with patch("app.core.entitlements.EntitlementService.has", return_value=True):
            created = client_with_org.post("/api/v1/reports/generate", json={
                "organization_id": org_id, "org_id": org_id,
                "report_type": "monthly_ops", "format": "json",
            })
            assert created.status_code == 201, created.text
            data = client_with_org.get(f"/api/reports/{created.json()['id']}/download").json()

        readiness = data["readiness"]
        labels = [c["label"] for c in readiness["failed_checks"] + readiness["warnings"]]

        # 7 findings + 3 copies of one IAM user used to print 10 rows.
        assert len(labels) == 2, labels
        assert len(set(labels)) == 2
        assert any("on 7 resources" in label for label in labels)
        assert sum("Devyani" in label for label in labels) == 1
