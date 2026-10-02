from datetime import datetime, timezone, timedelta
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.services.clinic_engine.v2.schema import RawEvent

logger = logging.getLogger("airs.services.demo.aws_demo_telemetry")

E2E_RESULTS_PATH = Path(__file__).resolve().parents[3] / "tests" / "aws_integration" / "e2e_results.json"


def get_aws_demo_telemetry(org_id: str) -> List[RawEvent]:
    """
    Generate realistic, high-fidelity AWS telemetry events derived from real AWS test machines
    and the recorded AWS integration runs in tests/aws_integration/e2e_results.json.

    Returns RawEvents for:
    - AWS Security Hub findings (Root credential compromise, AWS Config rules, S3 public access)
    - AWS GuardDuty alerts (Kali Linux remote host actions)
    - AWS IAM credential hygiene (stale keys)
    - AWS Backup recovery points
    """
    now = datetime.now(timezone.utc)
    events: List[RawEvent] = []

    # Attempt to load recorded findings from the test run
    raw_samples: List[Dict[str, Any]] = []
    if E2E_RESULTS_PATH.exists():
        try:
            content = json.loads(E2E_RESULTS_PATH.read_text(encoding="utf-8"))
            raw_samples = content.get("tests", {}).get("sample_findings", {}).get("samples", [])
        except Exception as exc:
            logger.warning("Could not read e2e_results.json for demo telemetry: %s", exc)

    if not raw_samples:
        # Fallback to canonical AWS test machine findings if file not loaded
        raw_samples = [
            {
                "title": "Potential credential compromise of Root/Root indicated by a sequence of actions.",
                "severity": "critical",
                "source_event_id": "arn:aws:guardduty:us-east-1:505467908065:detector/resilai-demo/root-compromise",
                "compliance_status": "FAILED",
            },
            {
                "title": "The API UploadPart was invoked from a remote host potentially running Kali Linux.",
                "severity": "medium",
                "source_event_id": "arn:aws:guardduty:us-east-1:505467908065:detector/resilai-demo/kali-upload",
                "compliance_status": "",
            },
            {
                "title": "Amazon S3 Block Public Access was disabled for the S3 bucket resilai-clinic-website.",
                "severity": "low",
                "source_event_id": "arn:aws:guardduty:us-east-1:505467908065:detector/resilai-demo/s3-public",
                "compliance_status": "",
            },
            {
                "title": "AWS Config should be enabled and use the service-linked role for resource recording",
                "severity": "critical",
                "source_event_id": "arn:aws:securityhub:us-east-1:505467908065:security-control/config-recording",
                "compliance_status": "FAILED",
            }
        ]

    # 1. Map recorded sample findings into AWS Security Hub RawEvents
    for idx, sample in enumerate(raw_samples[:6]):
        title = sample.get("title", f"AWS Finding {idx}")
        severity = sample.get("severity", "medium").lower()
        event_id = sample.get("source_event_id") or f"arn:aws:securityhub:us-east-1:demo:finding/aws-demo-{idx}"
        
        events.append(
            RawEvent(
                event_type="aws.securityhub.finding",
                source_system="aws_security_hub",
                source_event_id=event_id,
                organization_id=org_id,
                payload={
                    "title": title,
                    "description": f"Live telemetry finding detected from AWS test infrastructure: {title}",
                    "severity_label": severity.upper(),
                    "severity": severity,
                    "compliance_status": sample.get("compliance_status") or ("FAILED" if severity in ("critical", "high") else "PASSED"),
                    "record_state": "ACTIVE",
                    "product_name": "GuardDuty" if "guardduty" in event_id.lower() or "kali" in title.lower() else "Security Hub",
                    "resources": [
                        f"arn:aws:ec2:us-east-1:505467908065:instance/i-demo-node-0{idx + 1}"
                        if "api" in title.lower() or "kali" in title.lower()
                        else f"arn:aws:s3:::resilai-clinic-records-505467908065"
                    ],
                    "created_at": (now - timedelta(hours=idx * 2 + 1)).isoformat(),
                    "updated_at": (now - timedelta(minutes=15 * (idx + 1))).isoformat(),
                }
            )
        )

    # 2. Add AWS IAM Credential Hygiene Event (Stale IAM User)
    events.append(
        RawEvent(
            event_type="aws.iam.credential_report",
            source_system="aws",
            source_event_id=f"aws-iam-report-{(now - timedelta(hours=1)).strftime('%Y%m%d%H')}",
            organization_id=org_id,
            payload={
                "iam_users": [
                    {
                        "user_id": "iam-u-root",
                        "user_name": "aws-admin-backup@clinic.com",
                        "display_name": "Cloud Backup Automation Admin",
                        "mfa_enforced": False,
                        "account_enabled": True,
                        "last_sign_in": (now - timedelta(days=58)).isoformat(),  # Stale!
                        "password_last_changed": (now - timedelta(days=120)).isoformat(),
                    },
                    {
                        "user_id": "iam-u-devops",
                        "user_name": "cloud-secops@clinic.com",
                        "display_name": "Lead Cloud SecOps Engineer",
                        "mfa_enforced": True,
                        "account_enabled": True,
                        "last_sign_in": (now - timedelta(hours=3)).isoformat(),
                    }
                ]
            }
        )
    )

    # 3. Add AWS Backup Telemetry Event (Verified Production DB Snapshot)
    events.append(
        RawEvent(
            event_type="aws.backup.job",
            source_system="aws",
            source_event_id=f"aws-backup-snap-{(now - timedelta(hours=2)).strftime('%Y%m%d%H')}",
            organization_id=org_id,
            payload={
                "system_name": "AWS Production Patient Database (RDS Aurora)",
                "last_successful_backup": (now - timedelta(hours=2)).isoformat(),
                "backup_type": "continuous_pitr_snapshot",
                "vault_name": "resilai-immutable-vault",
                "recovery_point_arn": "arn:aws:backup:us-east-1:505467908065:recovery-point/vault-01",
            }
        )
    )

    return events
