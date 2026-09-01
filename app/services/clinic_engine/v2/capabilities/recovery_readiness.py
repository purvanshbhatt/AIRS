from typing import List
from datetime import datetime, timezone, timedelta
from app.services.clinic_engine.v2.schema import (
    Evidence, EvidenceKind, EvaluationResult, Verdict, MomentTranslation, ActionIntent
)
from app.services.clinic_engine.v2.capability import BaseCapability, CapabilityRegistry

@CapabilityRegistry.register
class RecoveryReadinessCapability(BaseCapability):
    @classmethod
    def capability_id(cls) -> str:
        return 'recovery_readiness'

    @classmethod
    def question_id(cls) -> str:
        return 'Q2'

    @classmethod
    def question_text(cls) -> str:
        return "Can I recover my clinic today if systems fail?"

    @classmethod
    def required_evidence(cls) -> List[EvidenceKind]:
        return [EvidenceKind.BACKUP_STATUS]

    @classmethod
    def supported_connectors(cls) -> List[str]:
        return ['veeam', 'datto', 'acronis', 'windows_backup', 'aws_backup', 'azure_backup', 'gcp_backup']

    @classmethod
    def evaluate(cls, evidence: List[Evidence]) -> List[EvaluationResult]:
        results = []
        now = datetime.now(timezone.utc)
        for e in evidence:
            if e.kind != EvidenceKind.BACKUP_STATUS:
                continue
            payload = e.payload
            last_backup_str = payload.get('last_successful_backup')
            backup_type = payload.get('backup_type', '').lower()
            
            last_backup = None
            if last_backup_str:
                try:
                    last_backup = datetime.fromisoformat(last_backup_str.replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            verdict = Verdict.SAFE
            hours_since_backup = 0
            
            if last_backup is None:
                verdict = Verdict.CRITICAL
            else:
                delta = now - last_backup
                hours_since_backup = int(delta.total_seconds() / 3600)
                if delta > timedelta(hours=24):
                    verdict = Verdict.CRITICAL
                elif timedelta(hours=12) < delta <= timedelta(hours=24) and backup_type == 'incremental':
                    verdict = Verdict.CONCERN
                    
            if verdict != Verdict.SAFE:
                results.append(EvaluationResult(
                    verdict=verdict,
                    evidence_used=[e.source_id],
                    details={
                        'system_name': payload.get('system_name', 'Unknown System'),
                        'last_backup_date': last_backup_str or 'Never',
                        'hours_since_backup': hours_since_backup
                    }
                ))
        return results

    @classmethod
    def translate(cls, result: EvaluationResult) -> MomentTranslation:
        details = result.details
        system_name = details.get('system_name')
        hours_since_backup = details.get('hours_since_backup')
        last_backup_date = details.get('last_backup_date')
        
        return MomentTranslation(
            what_happened=f"{system_name}'s backup hasn't completed successfully in {hours_since_backup} hours.",
            why_care="If your systems crash right now, everything since the last successful backup is gone forever.",
            ignore_impact=f"Complete loss of patient records, billing data, and appointment history since {last_backup_date}."
        )

    @classmethod
    def get_actions(cls, result: EvaluationResult) -> List[ActionIntent]:
        return [
            ActionIntent(
                action_id='notify_msp',
                label='Email Instructions to IT',
                can_automate=False,
                estimated_minutes=30
            )
        ]
