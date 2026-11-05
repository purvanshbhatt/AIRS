import pytest
from app.services.ai_narrative import _validate_numeric_trace, _extract_numerics

def test_extract_numerics():
    text = "Score is 85.5 and 10 vulnerabilities out of 100."
    nums = _extract_numerics(text)
    assert 85.5 in nums
    assert 10.0 in nums
    assert 100.0 in nums

def test_validate_numeric_trace_success():
    payload = {
        "overall_score": 85.5,
        "findings": [{"severity": "critical"}]
    }
    narrative = {
        "sections": [
            {"content": "Your score is 85.5 and you have 1 critical finding. 30 days."}
        ]
    }
    assert _validate_numeric_trace(narrative, payload) is True

def test_validate_numeric_trace_hallucination():
    payload = {
        "overall_score": 85.5,
        "findings": []
    }
    narrative = {
        "sections": [
            {"content": "I invented a score of 42.0 which is not allowed."}
        ]
    }
    assert _validate_numeric_trace(narrative, payload) is False
