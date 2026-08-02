from typing import List, Dict, Any
from app.services.clinic_engine.v2.schema import (
    Evidence, EvidenceKind, EvaluationResult, Verdict, MomentTranslation, ActionIntent
)
from app.services.clinic_engine.v2.capability import BaseCapability, CapabilityRegistry

@CapabilityRegistry.register
class DeviceCompromiseCapability(BaseCapability):
    @classmethod
    def capability_id(cls) -> str:
        return 'device_compromise'

    @classmethod
    def question_id(cls) -> str:
        return 'Q3'

    @classmethod
    def question_text(cls) -> str:
        return "Is one of my devices likely to be compromised?"

    @classmethod
    def required_evidence(cls) -> List[EvidenceKind]:
        return [EvidenceKind.DEVICE_SECURITY_STATUS, EvidenceKind.SECURITY_ALERT, EvidenceKind.VULNERABILITY_SCAN]

    @classmethod
    def supported_connectors(cls) -> List[str]:
        return ['microsoft', 'wazuh', 'crowdstrike', 'sentinelone']

    @classmethod
    def evaluate(cls, evidence: List[Evidence]) -> List[EvaluationResult]:
        devices: Dict[str, Dict[str, Any]] = {}
        
        for e in evidence:
            payload = e.payload
            device_id = payload.get('device_id')
            if not device_id:
                continue
                
            if device_id not in devices:
                devices[device_id] = {
                    'device_name': payload.get('device_name', device_id),
                    'alert_count': 0,
                    'vulnerability_count': 0,
                    'compliance_state': 'compliant',
                    'evidence_ids': set(),
                    'issues': []
                }
            
            d = devices[device_id]
            d['evidence_ids'].add(e.source_id)
            if payload.get('device_name') and d['device_name'] == device_id:
                d['device_name'] = payload.get('device_name')
                
            if e.kind == EvidenceKind.SECURITY_ALERT:
                severity = payload.get('severity', '').lower()
                status = payload.get('status', '').lower()
                if severity in ['high', 'critical'] and status == 'active':
                    d['alert_count'] += 1
                    d['issues'].append('active_alert')
                    
            elif e.kind == EvidenceKind.VULNERABILITY_SCAN:
                severity = payload.get('severity', '').lower()
                patched = payload.get('patched', False)
                if severity in ['high', 'critical'] and not patched:
                    d['vulnerability_count'] += 1
                    d['issues'].append('unpatched_vulnerability')
                    
            elif e.kind == EvidenceKind.DEVICE_SECURITY_STATUS:
                state = payload.get('compliance_state', '').lower()
                if state != 'compliant':
                    d['compliance_state'] = state
                    d['issues'].append('non_compliant')
                    
        results = []
        for device_id, d in devices.items():
            verdict = Verdict.SAFE
            if d['alert_count'] > 0 or d['vulnerability_count'] > 0:
                verdict = Verdict.CRITICAL
            elif d['compliance_state'] != 'compliant':
                verdict = Verdict.CONCERN
                
            if verdict != Verdict.SAFE:
                results.append(EvaluationResult(
                    verdict=verdict,
                    evidence_used=list(d['evidence_ids']),
                    details={
                        'device_name': d['device_name'],
                        'device_id': device_id,
                        'alert_count': d['alert_count'],
                        'vulnerability_count': d['vulnerability_count'],
                        'compliance_state': d['compliance_state'],
                        'issues': list(set(d['issues']))
                    }
                ))
                
        return results

    @classmethod
    def translate(cls, result: EvaluationResult) -> MomentTranslation:
        details = result.details
        device_name = details.get('device_name')
        alert_count = details.get('alert_count', 0)
        vulnerability_count = details.get('vulnerability_count', 0)
        issues = details.get('issues', [])
        
        if 'active_alert' in issues:
            what = f"{device_name} has {alert_count} active security warnings that need immediate attention."
        elif 'unpatched_vulnerability' in issues:
            what = f"{device_name} has {vulnerability_count} known security holes that hackers could exploit."
        else:
            what = f"{device_name} isn't meeting your security requirements and could be at risk."
            
        return MomentTranslation(
            what_happened=what,
            why_care="If this device is compromised, attackers can access your network.",
            ignore_impact="Potential ransomware or data breach."
        )

    @classmethod
    def get_actions(cls, result: EvaluationResult) -> List[ActionIntent]:
        issues = result.details.get('issues', [])
        if 'active_alert' in issues:
            return [ActionIntent(action_id='contact_it', label='Contact IT Immediately', can_automate=False)]
        elif 'unpatched_vulnerability' in issues:
            return [ActionIntent(action_id='schedule_update', label='Schedule Update for 2 AM', can_automate=True, automation_type='schedule_device_update')]
        else:
            return [ActionIntent(action_id='schedule_update', label='Schedule Update for 2 AM', can_automate=True)]
