from typing import Any, Dict, List

from app.services.clinic_engine.v2.schema import Evidence, EvidenceKind, RawEvent
from .base import EvidenceProvider

FINDING_EVENT_TYPES = ('aws.securityhub.finding', 'aws.guardduty.finding')
IAM_EVENT_TYPES = ('aws.iam.credential_report', 'aws.iam_users')
BACKUP_EVENT_TYPES = ('aws.backup.job', 'aws.backup_recovery_point')

# ARN resource types whose last path segment is an opaque id, not the name.
_NAME_SEGMENT = {'stack': 1, 'loadbalancer': -2, 'targetgroup': 1}


def resource_label(resource_id: str) -> str:
    """Short, readable name for an AWS resource id or ARN.

    ``arn:aws:ec2:us-east-1:111122223333:subnet/subnet-0abc`` -> ``subnet-0abc``
    ``arn:aws:s3:::clinic-backups``                           -> ``clinic-backups``
    ``AWS::::Account:111122223333``                           -> ``account 111122223333``
    """
    rid = str(resource_id or '').strip()
    if not rid:
        return ''
    if rid.startswith('AWS::::Account:'):
        return f"account {rid.rsplit(':', 1)[-1]}"
    resource = rid.split(':', 5)[5] if rid.startswith('arn:') and rid.count(':') >= 5 else rid
    if '/' in resource:
        parts = [p for p in resource.split('/') if p]
        if not parts:
            return rid
        index = _NAME_SEGMENT.get(parts[0], -1)
        try:
            return parts[index]
        except IndexError:
            return parts[-1]
    if ':' in resource:
        return resource.rsplit(':', 1)[-1]
    return resource


def finding_group(payload: Dict[str, Any]) -> str:
    """Key shared by every finding raised by the same check.

    AWS raises one finding per affected resource, so a check that fails on
    seven subnets arrives as seven findings with the same title. They are one
    problem to the reader and are evaluated as one.
    """
    title = ' '.join(str(payload.get('title') or '').lower().split())
    return title or str(payload.get('generator_id') or '').lower() or 'aws-finding'


def is_sample_finding(payload: Dict[str, Any]) -> bool:
    """True for findings AWS generated as test data (GuardDuty "sample findings")."""
    if payload.get('sample') is True:
        return True
    return str(payload.get('title') or '').lstrip().upper().startswith('[SAMPLE]')


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
            EvidenceKind.BACKUP_STATUS,
        ]

    @classmethod
    def extract(cls, events: List[RawEvent]) -> List[Evidence]:
        evidences: List[Evidence] = []
        seen_findings = set()

        for event in events:
            payload = event.payload or {}
            org_id = event.organization_id

            if event.event_type in FINDING_EVENT_TYPES:
                finding_id = event.source_event_id
                # The same finding can be stored more than once (one copy per
                # sync). It is still one finding.
                if finding_id in seen_findings:
                    continue
                seen_findings.add(finding_id)

                severity = payload.get('severity_label') or payload.get('severity') or 'medium'
                resources = [str(r) for r in (payload.get('resources') or []) if r]

                # One piece of evidence per finding. It carries no device_id on
                # purpose: a finding is a statement about a cloud resource, not
                # about a workstation, and the finding title is not a device
                # name. CloudPostureCapability groups these by check.
                evidences.append(Evidence(
                    kind=EvidenceKind.SECURITY_ALERT,
                    source_connector=cls.connector_type(),
                    source_id=finding_id,
                    organization_id=org_id,
                    payload={
                        'alert_id': finding_id,
                        'title': payload.get('title') or 'AWS security finding',
                        'severity': str(severity).lower(),
                        'status': 'active' if payload.get('record_state') != 'ARCHIVED' else 'resolved',
                        'description': payload.get('description', ''),
                        'compliance_status': payload.get('compliance_status', ''),
                        'cloud_finding': True,
                        'cloud_provider': 'aws',
                        'finding_group': finding_group(payload),
                        'product_name': payload.get('product_name', ''),
                        'resources': resources,
                        'resource_labels': [resource_label(r) for r in resources],
                        'sample': is_sample_finding(payload),
                    }
                ))

            elif event.event_type in BACKUP_EVENT_TYPES:
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

        evidences.extend(cls._iam_evidence(events))
        return evidences

    @classmethod
    def _iam_evidence(cls, events: List[RawEvent]) -> List[Evidence]:
        """IAM users from the newest credential report of each AWS account.

        Every sync stores a full report, so the last 24 hours hold many copies
        of the same users. Only the newest report per account is the current
        truth: reading them all would list each user once per sync and keep
        users that have since been deleted.
        """
        latest: Dict[str, RawEvent] = {}
        for event in events:
            if event.event_type not in IAM_EVENT_TYPES:
                continue
            account = str((event.payload or {}).get('account_id') or '')
            current = latest.get(account)
            # Report ids end in YYYYMMDDHH, so the greatest id is the newest.
            if current is None or str(event.source_event_id or '') > str(current.source_event_id or ''):
                latest[account] = event

        evidences: List[Evidence] = []
        seen_users = set()
        for event in latest.values():
            for user in (event.payload or {}).get('iam_users', []):
                source_id = user.get('user_id') or user.get('user_name')
                if not source_id or source_id in seen_users:
                    continue
                seen_users.add(source_id)

                mapped_user = dict(user)
                if 'user_name' in user and 'display_name' not in user:
                    mapped_user['display_name'] = user['user_name']
                if 'account_enabled' not in user:
                    mapped_user['account_enabled'] = True
                mapped_user['identity_provider'] = 'aws'

                evidences.append(Evidence(
                    kind=EvidenceKind.USER_ACCOUNT_STATUS,
                    source_connector=cls.connector_type(),
                    source_id=source_id,
                    organization_id=event.organization_id,
                    payload=mapped_user,
                ))
        return evidences
