import pytest
from datetime import datetime, timezone, timedelta
from app.services.evidence_confidence import calculate_evidence_confidence
from app.services.evidence.base_adapter import AdapterHealth

def test_evidence_confidence_perfect():
    now = datetime.now(timezone.utc)
    health = AdapterHealth(
        healthy=True,
        last_success_at=now,
        success_count=10,
        failure_count=0
    )
    result = calculate_evidence_confidence(health, current_time=now)
    assert result["confidence_score"] == 100.0
    assert result["factors"]["uptime"] == 1.0
    assert result["factors"]["success_rate"] == 1.0
    assert result["factors"]["freshness"] == 1.0
    assert result["factors"]["completeness"] == 1.0

def test_evidence_confidence_unhealthy():
    now = datetime.now(timezone.utc)
    health = AdapterHealth(
        healthy=False,
        last_success_at=now,
        success_count=10,
        failure_count=5
    )
    result = calculate_evidence_confidence(health, current_time=now)
    # Uptime is 0, so total is 0
    assert result["confidence_score"] == 0.0
    assert result["factors"]["uptime"] == 0.0

def test_evidence_confidence_freshness_decay():
    now = datetime.now(timezone.utc)
    # 2 hours old -> (1 - (1/167)) = ~0.994
    last_success = now - timedelta(hours=2)
    health = AdapterHealth(
        healthy=True,
        last_success_at=last_success,
        success_count=1,
        failure_count=0
    )
    result = calculate_evidence_confidence(health, current_time=now)
    score = result["confidence_score"]
    assert 99.0 <= score <= 99.5
    
    # 7 days old -> 0.0
    last_success_7d = now - timedelta(days=7)
    health.last_success_at = last_success_7d
    result_7d = calculate_evidence_confidence(health, current_time=now)
    assert result_7d["confidence_score"] == 0.0

def test_evidence_confidence_success_rate():
    now = datetime.now(timezone.utc)
    health = AdapterHealth(
        healthy=True,
        last_success_at=now,
        success_count=8,
        failure_count=2
    )
    # Success rate 80%
    result = calculate_evidence_confidence(health, current_time=now)
    assert result["confidence_score"] == 80.0

def test_evidence_confidence_completeness():
    now = datetime.now(timezone.utc)
    health = AdapterHealth(
        healthy=True,
        last_success_at=now,
        success_count=1,
        failure_count=0
    )
    # Completeness 50%
    result = calculate_evidence_confidence(health, completeness_score=0.5, current_time=now)
    assert result["confidence_score"] == 50.0

def test_evidence_confidence_never_successful():
    now = datetime.now(timezone.utc)
    health = AdapterHealth(
        healthy=True,
        last_success_at=None,
        success_count=0,
        failure_count=0
    )
    result = calculate_evidence_confidence(health, current_time=now)
    assert result["confidence_score"] == 0.0
    assert result["factors"]["freshness"] == 0.0
