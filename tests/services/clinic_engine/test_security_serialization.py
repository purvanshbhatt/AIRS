from datetime import datetime, timezone
import json
from app.services.clinic_engine.v2.schema import (
    ClinicMoment,
    MomentTranslation,
    Verdict,
    ActionIntent,
    EvaluationResult,
)

def test_evidence_ids_never_serialized():
    """Verify that internal evidence IDs and details are stripped from serialized output."""
    # 1. Create a moment with sensitive evidence IDs
    moment = ClinicMoment(
        id="test-moment",
        question_id="Q1",
        capability_id="test_cap",
        verdict=Verdict.CRITICAL,
        confidence=1.0,
        translation=MomentTranslation(
            what_happened="Test", why_care="Test", ignore_impact="Test"
        ),
        actions=[ActionIntent(action_id="test", label="Test")],
        evidence_ids=["sensitive-user-email@test.com", "device-guid-12345"],
        severity="high",
        generated_at=datetime.now(timezone.utc)
    )

    # 2. Serialize to dictionary
    dumped_dict = moment.model_dump()
    assert "evidence_ids" not in dumped_dict, "evidence_ids leaked in model_dump()"

    # 3. Serialize to JSON string
    dumped_json = moment.model_dump_json()
    parsed_json = json.loads(dumped_json)
    assert "evidence_ids" not in parsed_json, "evidence_ids leaked in model_dump_json()"
    
    # 4. Verify evaluation results also exclude sensitive context
    eval_result = EvaluationResult(
        verdict=Verdict.CONCERN,
        confidence=0.8,
        evidence_used=["internal-id-1"],
        details={"raw_payload": {"secret": "data"}}
    )
    
    eval_dict = eval_result.model_dump()
    assert "evidence_used" not in eval_dict, "evidence_used leaked"
    assert "details" not in eval_dict, "details leaked"
