"""Demo telemetry replays recorded AWS fixtures per industry when present."""
import json

from app.services.demo import aws_demo_telemetry as demo


def test_fixture_replay_per_industry(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "FIXTURE_DIR", tmp_path)
    (tmp_path / "aws_legal.json").write_text(json.dumps({
        "industry": "legal",
        "source": {"account_id": "123456789012"},
        "securityhub_findings": [
            {"event_type": "aws.securityhub.finding", "source_system": "aws_security_hub",
             "source_event_id": "arn:aws:securityhub:us-east-1:123456789012:finding/abc",
             "payload": {"title": "EC2 instances should not have a public IPv4 address", "severity": "high",
                          "resources": ["arn:aws:ec2:us-east-1:123456789012:instance/i-0legal"]}},
        ],
        "iam_users": [{"user_name": "resilai-northstar-cole-managing-partner", "mfa_active": False,
                        "access_key_1_active": True}],
        "resources": [{"kind": "ec2", "instance_id": "i-0legal", "name": "northstar-cole-dms-matter-server"}],
    }))

    legal = demo.get_aws_demo_telemetry("demo-northstar-cole")
    types = [e.event_type for e in legal]
    assert "aws.securityhub.finding" in types
    assert "aws.iam.credential_report" in types
    assert "aws.inventory.snapshot" in types
    finding = next(e for e in legal if e.event_type == "aws.securityhub.finding")
    assert finding.organization_id == "demo-northstar-cole"
    assert finding.payload["recorded_from"] == "aws:123456789012"
    iam = next(e for e in legal if e.event_type == "aws.iam.credential_report")
    assert iam.payload["iam_users"][0]["mfa_enforced"] is False

    # No healthcare fixture in tmp_path -> falls back to the built-in samples
    health = demo.get_aws_demo_telemetry("demo-health-org")
    assert health and all(e.organization_id == "demo-health-org" for e in health)
