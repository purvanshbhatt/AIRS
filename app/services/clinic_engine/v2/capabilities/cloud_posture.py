from typing import Any, Dict, List

from app.services.clinic_engine.v2.schema import (
    Evidence, EvidenceKind, EvaluationResult, Verdict, MomentTranslation, ActionIntent
)
from app.services.clinic_engine.v2.capability import BaseCapability, CapabilityRegistry

SEVERITY_RANK = {'informational': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
# How many affected resources are named before the rest become "and N more".
MAX_NAMED_RESOURCES = 3


def _plural(count: int, singular: str, plural: str = '') -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


@CapabilityRegistry.register
class CloudPostureCapability(BaseCapability):
    """Findings reported by a cloud provider's own security service.

    A cloud provider raises one finding per affected resource. Reported one by
    one, a single failing check on seven subnets reads as the same sentence
    seven times. This capability reports each check once, with the number of
    resources it fails on and their names.
    """

    @classmethod
    def capability_id(cls) -> str:
        return 'cloud_posture'

    @classmethod
    def question_id(cls) -> str:
        return 'Q3'

    @classmethod
    def question_text(cls) -> str:
        return "Is something in my cloud account exposed or under attack?"

    @classmethod
    def required_evidence(cls) -> List[EvidenceKind]:
        return [EvidenceKind.SECURITY_ALERT]

    @classmethod
    def supported_connectors(cls) -> List[str]:
        return ['aws', 'aws_security_hub']

    @classmethod
    def evaluate(cls, evidence: List[Evidence]) -> List[EvaluationResult]:
        groups: Dict[str, Dict[str, Any]] = {}

        for e in evidence:
            payload = e.payload
            if e.kind != EvidenceKind.SECURITY_ALERT or not payload.get('cloud_finding'):
                continue
            if str(payload.get('status', '')).lower() != 'active':
                continue

            severity = str(payload.get('severity', '')).lower()
            failed_check = str(payload.get('compliance_status', '')).upper() == 'FAILED'
            urgent = severity in ('high', 'critical')
            # Same thresholds as before grouping: high or critical is urgent,
            # a failed check of lower severity is a concern, anything else
            # (passed checks, low-severity notices) is not reported.
            if not urgent and not failed_check:
                continue

            key = str(payload.get('finding_group') or payload.get('title') or e.source_id)
            group = groups.setdefault(key, {
                'title': str(payload.get('title') or 'AWS security finding').strip(),
                'provider': str(payload.get('cloud_provider') or 'aws'),
                'severity': severity,
                'urgent': False,
                'is_check': False,
                'sample': True,
                'finding_ids': [],
                'resources': [],
            })
            group['finding_ids'].append(e.source_id)
            group['urgent'] = group['urgent'] or urgent
            group['is_check'] = group['is_check'] or bool(payload.get('compliance_status'))
            group['sample'] = group['sample'] and bool(payload.get('sample'))
            if SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK.get(group['severity'], 0):
                group['severity'] = severity
            for label in payload.get('resource_labels') or []:
                if label and label not in group['resources']:
                    group['resources'].append(label)

        results = []
        for key in sorted(groups):
            g = groups[key]
            results.append(EvaluationResult(
                verdict=Verdict.CRITICAL if g['urgent'] else Verdict.CONCERN,
                evidence_used=sorted(set(g['finding_ids'])),
                details={
                    'title': g['title'],
                    'provider': g['provider'],
                    'severity': g['severity'],
                    'is_check': g['is_check'],
                    'sample': g['sample'],
                    'finding_count': len(set(g['finding_ids'])),
                    'resource_count': len(g['resources']),
                    'resources': sorted(g['resources']),
                }
            ))
        return results

    @classmethod
    def translate(cls, result: EvaluationResult) -> MomentTranslation:
        d = result.details
        title = str(d.get('title') or 'AWS security finding').rstrip('.')
        resources = d.get('resources') or []
        resource_count = d.get('resource_count') or len(resources)
        finding_count = d.get('finding_count') or 1

        named = ', '.join(resources[:MAX_NAMED_RESOURCES])
        if resource_count > MAX_NAMED_RESOURCES:
            named += f" and {resource_count - MAX_NAMED_RESOURCES} more"

        if d.get('is_check'):
            what = f'AWS security check failing: "{title}"'
            if resource_count:
                what += f" on {_plural(resource_count, 'resource')} ({named})"
            what += '.'
            why = "A setting in your AWS account does not meet the AWS security baseline."
            if d.get('severity') in ('high', 'critical'):
                why += f" AWS rates this {d.get('severity')} severity."
            ignore = "A misconfigured cloud resource can expose data or let an attacker in."
        else:
            what = f'AWS threat detection alert: "{title}"'
            extras = []
            if finding_count > 1:
                extras.append(_plural(finding_count, 'alert'))
            if resource_count:
                extras.append(f"affects {named}")
            if extras:
                what += f" ({', '.join(extras)})"
            what += '.'
            why = "AWS saw activity in your account that looks like an attack or a stolen credential."
            ignore = "If the activity is real, an attacker may already have access to your cloud account."

        if d.get('sample'):
            what = f"Sample finding (AWS test data). {what}"
            why = "AWS generated this finding as test data. It does not describe real activity in your account."

        return MomentTranslation(what_happened=what, why_care=why, ignore_impact=ignore)

    @classmethod
    def get_actions(cls, result: EvaluationResult) -> List[ActionIntent]:
        return [ActionIntent(
            action_id='review_cloud_finding',
            label='Review in AWS Security Hub',
            can_automate=False,
            automation_params={
                'title': result.details.get('title'),
                'resource_count': result.details.get('resource_count', 0),
                'is_check': bool(result.details.get('is_check')),
            },
            estimated_minutes=15,
        )]
