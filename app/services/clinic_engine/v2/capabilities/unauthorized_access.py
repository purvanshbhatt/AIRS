from typing import List
from datetime import datetime, timezone, timedelta
from app.services.clinic_engine.v2.schema import (
    Evidence, EvidenceKind, EvaluationResult, Verdict, MomentTranslation, ActionIntent
)
from app.services.clinic_engine.v2.capability import BaseCapability, CapabilityRegistry

@CapabilityRegistry.register
class UnauthorizedAccessCapability(BaseCapability):
    @classmethod
    def capability_id(cls) -> str:
        return 'unauthorized_access'

    @classmethod
    def question_id(cls) -> str:
        return 'Q1'

    @classmethod
    def question_text(cls) -> str:
        return "Does someone who shouldn't have access still have access?"

    @classmethod
    def required_evidence(cls) -> List[EvidenceKind]:
        return [EvidenceKind.USER_ACCOUNT_STATUS]

    @classmethod
    def supported_connectors(cls) -> List[str]:
        return ['microsoft', 'google_workspace', 'okta', 'jumpcloud']

    @classmethod
    def evaluate(cls, evidence: List[Evidence]) -> List[EvaluationResult]:
        results = []
        now = datetime.now(timezone.utc)
        for e in evidence:
            if e.kind != EvidenceKind.USER_ACCOUNT_STATUS:
                continue
            payload = e.payload
            account_enabled = payload.get('account_enabled')
            if not account_enabled:
                continue
                
            last_sign_in_str = payload.get('last_sign_in')
            created_at_str = payload.get('created_at')
            
            last_sign_in = None
            if last_sign_in_str:
                try:
                    last_sign_in = datetime.fromisoformat(last_sign_in_str.replace('Z', '+00:00'))
                except ValueError:
                    pass
                    
            created_at = None
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            verdict = Verdict.SAFE
            days_inactive = 0
            
            if last_sign_in is not None:
                delta = now - last_sign_in
                if delta > timedelta(days=30):
                    verdict = Verdict.CRITICAL
                    days_inactive = delta.days
            else:
                if created_at is not None:
                    delta = now - created_at
                    if delta > timedelta(days=90):
                        verdict = Verdict.CRITICAL
                        days_inactive = delta.days
                else:
                    verdict = Verdict.CONCERN
                    
            if verdict != Verdict.SAFE:
                results.append(EvaluationResult(
                    verdict=verdict,
                    evidence_used=[e.source_id],
                    details={
                        'display_name': payload.get('display_name', 'Unknown User'),
                        'user_id': payload.get('user_id', e.source_id),
                        'last_sign_in': last_sign_in_str,
                        'days_inactive': days_inactive
                    }
                ))
        return results

    @classmethod
    def translate(cls, result: EvaluationResult) -> MomentTranslation:
        details = result.details
        display_name = details.get('display_name')
        days_inactive = details.get('days_inactive')
        return MomentTranslation(
            what_happened=f"{display_name}'s account is still active but they haven't signed in for {days_inactive} days.",
            why_care="Anyone with their password could access patient records, billing data, and email right now.",
            ignore_impact="If this account is compromised, your clinic faces a HIPAA violation and potential data breach."
        )

    @classmethod
    def get_actions(cls, result: EvaluationResult) -> List[ActionIntent]:
        return [
            ActionIntent(
                action_id='disable_account',
                label='Suspend Account',
                can_automate=True,
                automation_type='m365_disable_user',
                automation_params={'user_id': result.details.get('user_id')}
            )
        ]
