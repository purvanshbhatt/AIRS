from typing import List, Any, Dict
from app.services.clinic_engine.v2.schema import Evidence, EvidenceKind, RawEvent
from .base import EvidenceProvider

class AWSProvider(EvidenceProvider):
    """Evidence provider for AWS Security Hub, GuardDuty, IAM, and AWS Backup telemetry."""

    @classmethod
    def connector_type(cls) -> str:
        return 'aws_security_hub'

    @classmethod
    def provides(cls) -> List[EvidenceKind]:
        return [
            EvidenceKind.SECURITY_ALERT,
            EvidenceKind.USER_ACCOUNT_STATUS,
            EvidenceKind.DEVICE_SECURITY_STATUS,
            EvidenceKind.BACKUP_STATUS,
            EvidenceKind.VULNERABILITY_SCAN,
        ]

    @classmethod
    def extract(cls, events: List[RawEvent]) -> List[Evidence]:
        evidences: List[Evidence] = []

        for event in events:
            payload = event.payload or {}
            org_id = event.organization_id

            if event.event_type in ('aws.securityhub.finding', 'aws.guardduty.finding'):
                finding_id = event.source_event_id
                severity = payload.get('severity_label') or payload.get('severity') or 'medium'
                title = payload.get('title', 'AWS Security Finding')
                resources = payload.get('resources') or []
                res_id = resources[0] if resources else finding_id

                # 1. Security Alert evidence
                evidences.append(Evidence(
                    kind=EvidenceKind.SECURITY_ALERT,
                    source_connector=cls.connector_type(),
                    source_id=finding_id,
                    organization_id=org_id,
                    payload={
                        'alert_id': finding_id,
                        'title': title,
                        'severity': str(severity).lower(),
                        'status': 'active' if payload.get('record_state') != 'ARCHIVED' else 'resolved',
                        'device_id': res_id,
                        'description': payload.get('description', ''),
                        'compliance_status': payload.get('compliance_status', ''),
                    }
                ))

                # If resource is an EC2/infrastructure asset or S3 bucket, provide device/asset security status
                evidences.append(Evidence(
                    kind=EvidenceKind.DEVICE_SECURITY_STATUS,
                    source_connector=cls.connector_type(),
                    source_id=res_id,
                    organization_id=org_id,
                    payload={
                        'device_id': res_id,
                        'device_name': title,
                        'compliance_state': 'noncompliant' if payload.get('compliance_status') == 'FAILED' or str(severity).lower() in ('critical', 'high') else 'compliant',
                        'is_encrypted': 'unencrypted' not in title.lower() and 'encryption' not in title.lower(),
                        'cloud_provider': 'aws',
                    }
                ))

            elif event.event_type in ('aws.iam.credential_report', 'aws.iam_users'):
                # IAM accounts
                for user in payload.get('iam_users', []):
                    mapped_user = dict(user)
                    if 'user_name' in user and 'display_name' not in user:
                        mapped_user['display_name'] = user['user_name']
                    if 'account_enabled' not in user:
                        mapped_user['account_enabled'] = True

                    evidences.append(Evidence(
                        kind=EvidenceKind.USER_ACCOUNT_STATUS,
                        source_connector=cls.connector_type(),
                        source_id=user.get('user_id') or user.get('user_name'),
                        organization_id=org_id,
                        payload=mapped_user,
                    ))

            elif event.event_type in ('aws.backup.job', 'aws.backup_recovery_point'):
                evidences.append(Evidence(
                    kind=EvidenceKind.BACKUP_STATUS,
                    source_connector=cls.connector_type(),
                    source_id=event.source_event_id,
                    organization_id=org_id,
                    payload={
                        'system_name': payload.get('system_name', 'AWS Production Database Backup'),
                        'last_successful_backup': payload.get('last_successful_backup'),
                        'backup_type': payload.get('backup_type', 'snapshot'),
                    }
                ))

        return evidences
