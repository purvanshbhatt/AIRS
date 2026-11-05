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

    is_legal = any(k in org_id.lower() for k in ["cole", "law", "legal", "lex"])

    # 1. Map recorded sample findings into AWS Security Hub RawEvents
    for idx, sample in enumerate(raw_samples[:6]):
        title = sample.get("title", f"AWS Finding {idx}")
        severity = sample.get("severity", "medium").lower()
        raw_id = sample.get("source_event_id") or f"arn:aws:securityhub:us-east-1:demo:finding/aws-demo"
        event_id = f"{raw_id}-{idx}"

        if is_legal:
            if "s3" in title.lower():
                title = "Amazon S3 Block Public Access disabled for confidential client matter repository."
                resource = "arn:aws:s3:::northstar-cole-client-matters-505467908065"
            elif "root" in title.lower():
                title = "Potential credential compromise of Legal Partner AWS audit role."
                resource = "arn:aws:iam::505467908065:role/Legal-Audit-Admin"
            elif "config" in title.lower():
                title = "AWS Config should be enabled for Litigation Hold S3 buckets"
                resource = "arn:aws:s3:::northstar-cole-litigation-hold"
            else:
                resource = f"arn:aws:ec2:us-east-1:505467908065:instance/i-legal-node-0{idx + 1}"
        else:
            resource = (
                f"arn:aws:ec2:us-east-1:505467908065:instance/i-demo-node-0{idx + 1}"
                if "api" in title.lower() or "kali" in title.lower()
                else "arn:aws:s3:::resilai-clinic-records-505467908065"
            )
        
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
                    "resources": [resource],
                    "created_at": (now - timedelta(hours=idx * 2 + 1)).isoformat(),
                    "updated_at": (now - timedelta(minutes=15 * (idx + 1))).isoformat(),
                }
            )
        )

    # 2. Add AWS IAM Credential Hygiene Event (Stale IAM User)
    iam_user_1 = "discovery-counsel-ext@northstarcole.com" if is_legal else "aws-admin-backup@clinic.com"
    iam_display_1 = "External Litigation Discovery Counsel" if is_legal else "Cloud Backup Automation Admin"
    iam_user_2 = "it-director@northstarcole.com" if is_legal else "cloud-secops@clinic.com"
    iam_display_2 = "Managing IT Director" if is_legal else "Lead Cloud SecOps Engineer"

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
                        "user_name": iam_user_1,
                        "display_name": iam_display_1,
                        "mfa_enforced": False,
                        "account_enabled": True,
                        "last_sign_in": (now - timedelta(days=58)).isoformat(),  # Stale!
                        "password_last_changed": (now - timedelta(days=120)).isoformat(),
                    },
                    {
                        "user_id": "iam-u-devops",
                        "user_name": iam_user_2,
                        "display_name": iam_display_2,
                        "mfa_enforced": True,
                        "account_enabled": True,
                        "last_sign_in": (now - timedelta(hours=3)).isoformat(),
                    }
                ]
            }
        )
    )

    # 3. Add AWS Backup Telemetry Event (Verified Production DB Snapshot)
    backup_system = "AWS Production Legal Matter Vault (RDS PostgreSQL Aurora)" if is_legal else "AWS Production Patient Database (RDS Aurora)"
    vault_name = "resilai-legal-vault" if is_legal else "resilai-immutable-vault"

    events.append(
        RawEvent(
            event_type="aws.backup.job",
            source_system="aws",
            source_event_id=f"aws-backup-snap-{(now - timedelta(hours=2)).strftime('%Y%m%d%H')}",
            organization_id=org_id,
            payload={
                "system_name": backup_system,
                "last_successful_backup": (now - timedelta(hours=2)).isoformat(),
                "backup_type": "continuous_pitr_snapshot",
                "vault_name": vault_name,
                "recovery_point_arn": "arn:aws:backup:us-east-1:505467908065:recovery-point/vault-01",
            }
        )
    )

    return events
