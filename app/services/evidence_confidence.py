from datetime import datetime, timezone
from typing import Any, Dict

from app.services.evidence.base_adapter import AdapterHealth

def calculate_evidence_confidence(
    health: AdapterHealth,
    completeness_score: float = 1.0,
    current_time: datetime = None
) -> Dict[str, Any]:
    """
    Calculate Evidence Confidence score (0-100) based on four deterministic factors:
    1. Freshness: Time since last success. (1.0 if within 1h, linear decay to 0.0 at 7d)
    2. Uptime: Is the adapter currently healthy? (1.0 or 0.0)
    3. Success Rate: Historical success rate from the adapter (0.0 to 1.0)
    4. Completeness: External completeness factor, e.g. mapping coverage (0.0 to 1.0)
    
    Formula: Confidence = Freshness * Uptime * Success Rate * Completeness * 100
    
    Returns a dict with `confidence_score` and `factors` breakdown.
    No LLM is used in this calculation.
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
        
    # 1. Uptime
    uptime_factor = 1.0 if health.healthy else 0.0
    
    # 2. Success Rate
    success_rate_factor = health.success_rate
    
    # 3. Freshness
    freshness_factor = 0.0
    if health.last_success_at:
        delta_hours = (current_time - health.last_success_at).total_seconds() / 3600.0
        # If time is in the future due to clock skew, cap at 1.0
        if delta_hours <= 1.0:
            freshness_factor = 1.0
        elif delta_hours >= 168.0: # 7 days
            freshness_factor = 0.0
        else:
            # Linear decay from 1h to 168h
            freshness_factor = 1.0 - ((delta_hours - 1.0) / 167.0)
            
    # 4. Completeness
    completeness_factor = max(0.0, min(1.0, completeness_score))
    
    # Combined score
    score = uptime_factor * success_rate_factor * freshness_factor * completeness_factor * 100.0
    
    return {
        "confidence_score": round(score, 2),
        "factors": {
            "uptime": round(uptime_factor, 2),
            "success_rate": round(success_rate_factor, 2),
            "freshness": round(freshness_factor, 2),
            "completeness": round(completeness_factor, 2)
        }
    }
