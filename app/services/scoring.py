"""
AIRS Scoring Service

Calculates readiness scores based on assessment answers.

Includes a "visibility penalty" for critical metrics where "Unknown/Not Measured"
responses indicate a governance gap. These are penalized more heavily than
low-but-measured values to incentivize instrumentation and measurement.
"""

from typing import Dict, Any, List, Optional, Tuple
from app.core.rubric import RUBRIC, get_question


class ScoringError(Exception):
    """Raised when scoring encounters an error."""
    pass


# Questions that are critical for operational visibility. When these are
# answered with "Unknown/Not Measured/Undefined" variants, an additional
# governance penalty is applied to the overall score.
VISIBILITY_CRITICAL_QUESTIONS = {
    "dc_01",  # EDR coverage
    "rs_05",  # RTO
}
VISIBILITY_PENALTY_PER_UNKNOWN = 2.0  # Points deducted per unknown critical metric


def _is_unknown_answer(answer: Any, question: dict) -> bool:
    """Check if the answer indicates an unknown/not measured state."""
    tier_options = question.get("tier_options")
    if tier_options and isinstance(answer, str):
        canonical = answer.strip().lower()
        # Check against common unknown/unmeasured keywords
        unknown_keywords = {"not measured", "undefined", "unknown", "not applicable", "n/a", "no target"}
        return any(kw in canonical for kw in unknown_keywords)
    return False


def _calculate_threshold_score(value: float, thresholds: Dict[str, float], 
                                lower_is_better: bool = False) -> float:
    """
    Calculate score based on threshold values.
    
    Args:
        value: The numeric value to score
        thresholds: Dict mapping threshold values to scores
        lower_is_better: If True, lower values get higher scores (e.g., RTO)
    
    Returns:
        Score between 0 and 1
    """
    if value is None:
        return 0.0
    
    if lower_is_better:
        # For metrics where lower is better (e.g., RTO)
        # Sort thresholds ascending, find the first one >= value
        sorted_thresholds = sorted(
            [(float(k), v) for k, v in thresholds.items()],
            key=lambda x: x[0]
        )
        for threshold, score in sorted_thresholds:
            if value <= threshold:
                return score
        return 0.0
    else:
        # For metrics where higher is better (e.g., retention days)
        sorted_thresholds = sorted(
            [(float(k), v) for k, v in thresholds.items()],
            key=lambda x: x[0]
        )
        result_score = 0.0
        for threshold, score in sorted_thresholds:
            if value >= threshold:
                result_score = score
        return result_score


def _score_question(question: dict, answer: Any, verification_status: str = "SELF_ATTESTED", high_confidence_mode: bool = False) -> float:
    """
    Score a single question based on its type and the provided answer.
    
    Supports an optional ``tier_options`` field on a question for maturity-tier
    string answers (e.g. ">90%", "<4hrs", "Not Measured").  When a tier string
    is detected the mapped score is used directly.  Legacy numeric answers
    continue to use the threshold lookup so backwards-compatibility is preserved.
    
    Args:
        question: Question definition from rubric
        answer: The answer value
        verification_status: SOC_VERIFIED gets 1.0 multiplier, SELF_ATTESTED gets 0.6
    
    Returns:
        Points earned (0 to question's max points * reliability_factor)
    """
    q_type = question["type"]
    max_points = question["points"]
    
    if answer is None:
        return 0.0

    base_points = 0.0

    # ── Maturity-tier string handling (backward-compatible) ──
    # If the question publishes tier_options AND the answer is a recognised
    # tier value string, resolve to the mapped score without touching the
    # existing threshold logic below.
    tier_options = question.get("tier_options")
    if tier_options and isinstance(answer, str):
        canonical = answer.strip()
        for opt in tier_options:
            if opt["value"].lower() == canonical.lower():
                base_points = max_points * opt["score"]
                break

    elif q_type == "boolean":
        # Boolean: True = full points, False = 0
        if isinstance(answer, bool):
            base_points = max_points if answer else 0.0
        elif isinstance(answer, str):
            base_points = max_points if answer.lower() in ("yes", "true", "1") else 0.0
        else:
            base_points = max_points if answer else 0.0
    
    elif q_type in ("numeric", "percentage"):
        # Numeric/Percentage: Use thresholds
        try:
            value = float(answer)
            thresholds = question.get("thresholds", {})
            lower_is_better = question.get("scoring_direction") == "lower_is_better"
            
            threshold_score = _calculate_threshold_score(value, thresholds, lower_is_better)
            base_points = max_points * threshold_score
        except (ValueError, TypeError):
            base_points = 0.0

    # Apply deterministic reliability factor
    if verification_status in ("STALE_CONNECTION", "Stale Connection"):
        reliability_factor = 0.0 if high_confidence_mode else 0.6
    elif verification_status in ("SOC_VERIFIED", "SOC-Verified"):
        reliability_factor = 1.0
    else:
        reliability_factor = 0.6
        
    return base_points * reliability_factor


def calculate_domain_score(domain_id: str, answers: Dict[str, Any], verification_statuses: Dict[str, str] = None, high_confidence_mode: bool = False) -> Dict[str, Any]:
    """
    Calculate score for a single domain.
    
    Args:
        domain_id: The domain identifier
        answers: Dict mapping question_id to answer value
        verification_statuses: Dict mapping question_id to status string
    
    Returns:
        Dict with domain scoring details
    """
    verification_statuses = verification_statuses or {}
    domain = RUBRIC["domains"].get(domain_id)
    if not domain:
        raise ScoringError(f"Unknown domain: {domain_id}")
    
    questions = domain["questions"]
    max_raw_points = sum(q["points"] for q in questions)
    
    question_scores = []
    total_points = 0.0
    
    for question in questions:
        q_id = question["id"]
        answer = answers.get(q_id)
        status = verification_statuses.get(q_id, "SELF_ATTESTED")
        points = _score_question(question, answer, status, high_confidence_mode)
        total_points += points
        
        question_scores.append({
            "question_id": q_id,
            "question_text": question["text"],
            "answer": answer,
            "points_earned": round(points, 2),
            "points_possible": question["points"]
        })
    
    # Scale to 0-5
    domain_score = (total_points / max_raw_points) * 5 if max_raw_points > 0 else 0
    
    return {
        "domain_id": domain_id,
        "domain_name": domain["name"],
        "weight": domain["weight"],
        "raw_points": round(total_points, 2),
        "max_raw_points": max_raw_points,
        "score": round(domain_score, 2),  # 0-5 scale
        "max_score": 5,
        "questions": question_scores
    }


def _calc_scores_internal(answers: Dict[str, Any], verification_statuses: Dict[str, str] = None, high_confidence_mode: bool = False) -> Dict[str, Any]:
    domain_results = []
    weighted_sum = 0.0
    total_weight = 0
    unknown_critical_metrics: List[str] = []
    
    for domain_id in RUBRIC["domains"]:
        domain_result = calculate_domain_score(domain_id, answers, verification_statuses, high_confidence_mode)
        domain_results.append(domain_result)
        
        # Calculate weighted contribution (score is 0-5, weight is %)
        # Contribution to 100-point scale: (score/5) * weight
        weighted_contribution = (domain_result["score"] / 5) * domain_result["weight"]
        weighted_sum += weighted_contribution
        total_weight += domain_result["weight"]
        
        # Track unknown answers to visibility-critical questions
        for q in domain_result["questions"]:
            if q["question_id"] in VISIBILITY_CRITICAL_QUESTIONS:
                question_data, _domain_id = get_question(q["question_id"])
                if question_data and _is_unknown_answer(q["answer"], question_data):
                    unknown_critical_metrics.append(q["question_id"])
    
    # Apply visibility penalty for unknown critical metrics
    visibility_penalty = len(unknown_critical_metrics) * VISIBILITY_PENALTY_PER_UNKNOWN
    
    # Overall score on 0-100 scale (with visibility penalty)
    overall_score = max(0.0, round(weighted_sum - visibility_penalty, 2))
    
    # Determine maturity level
    maturity = _get_maturity_level(overall_score)
    
    result = {
        "overall_score": overall_score,
        "max_score": 100,
        "maturity_level": maturity["level"],
        "maturity_name": maturity["name"],
        "maturity_description": maturity["description"],
        "domains": domain_results,
        "summary": {
            "total_questions": sum(len(d["questions"]) for d in domain_results),
            "questions_answered": sum(
                1 for d in domain_results 
                for q in d["questions"] if q["answer"] is not None
            ),
            "unknown_critical_metrics": unknown_critical_metrics,
            "strongest_domain": max(domain_results, key=lambda x: x["score"])["domain_name"],
            "weakest_domain": min(domain_results, key=lambda x: x["score"])["domain_name"]
        }
    }
    
    # Add visibility penalty info if any
    if unknown_critical_metrics:
        result["visibility_penalty"] = {
            "penalty_applied": visibility_penalty,
            "unknown_critical_metrics": unknown_critical_metrics,
            "message": f"Score reduced by {visibility_penalty} points due to {len(unknown_critical_metrics)} unmeasured critical metric(s)"
        }
    
    return result


def _get_maturity_level(score: float) -> Dict[str, Any]:
    """Determine maturity level based on overall score."""
    for range_key, level_info in RUBRIC["maturity_levels"].items():
        low, high = map(int, range_key.split("-"))
        if low <= score <= high:
            return level_info
    
    # Default fallback
    return {"level": 1, "name": "Initial", "description": "Unable to determine maturity level"}


def get_recommendations(scores: Dict[str, Any], max_per_domain: int = 3) -> List[Dict[str, Any]]:
    """
    Generate recommendations based on scoring results.
    
    Args:
        scores: Result from calculate_scores()
        max_per_domain: Maximum recommendations per domain
    
    Returns:
        List of prioritized recommendations
    """
    recommendations = []
    
    # Sort domains by score (lowest first = highest priority)
    sorted_domains = sorted(scores["domains"], key=lambda x: x["score"])
    
    priority = 1
    for domain in sorted_domains:
        domain_recs = []
        
        # Find questions with low scores
        for question in domain["questions"]:
            if question["points_earned"] < question["points_possible"]:
                gap = question["points_possible"] - question["points_earned"]
                possible = max(float(question["points_possible"]), 1.0)
                gap_ratio = gap / possible
                if gap_ratio >= 0.8:
                    impact = "high"
                elif gap_ratio >= 0.4:
                    impact = "medium"
                else:
                    impact = "low"
                domain_recs.append({
                    "priority": priority,
                    "domain": domain["domain_name"],
                    "domain_id": domain["domain_id"],
                    "question_id": question["question_id"],
                    "finding": question["question_text"],
                    "current_answer": question["answer"],
                    "points_gap": round(gap, 2),
                    "impact": impact,
                })
        
        # Sort by gap size and take top N
        domain_recs.sort(key=lambda x: x["points_gap"], reverse=True)
        for rec in domain_recs[:max_per_domain]:
            rec["priority"] = priority
            recommendations.append(rec)
            priority += 1
    
    return recommendations


def validate_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate answers against the rubric.
    
    Args:
        answers: Dict mapping question_id to answer value
    
    Returns:
        Validation result with any errors
    """
    errors = []
    warnings = []
    valid_ids = set()
    
    for domain in RUBRIC["domains"].values():
        for question in domain["questions"]:
            valid_ids.add(question["id"])
    
    # Check for unknown question IDs
    for q_id in answers:
        if q_id not in valid_ids:
            errors.append(f"Unknown question ID: {q_id}")
    
    # Check for missing answers
    for q_id in valid_ids:
        if q_id not in answers or answers[q_id] is None:
            warnings.append(f"Missing answer for: {q_id}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "questions_expected": len(valid_ids),
        "questions_provided": len([a for a in answers.values() if a is not None])
    }


def calculate_scores(answers: Dict[str, Any], verification_statuses: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Calculate complete readiness scores from assessment answers.
    Includes base_ghi and high_confidence_ghi tracking.
    """
    # 1. Base calculation (STALE counts as 0.6)
    base_result = _calc_scores_internal(answers, verification_statuses, high_confidence_mode=False)
    
    # 2. High confidence calculation (STALE counts as 0.0)
    high_conf_result = _calc_scores_internal(answers, verification_statuses, high_confidence_mode=True)
    
    # 3. Enrichment
    base_result["base_ghi"] = base_result["overall_score"]
    base_result["high_confidence_ghi"] = high_conf_result["overall_score"]
    
    stale_findings = [q for q, s in (verification_statuses or {}).items() if s in ("STALE_CONNECTION", "Stale Connection")]
    base_result["has_stale_connections"] = len(stale_findings) > 0
    base_result["stale_finding_count"] = len(stale_findings)
    
    return base_result
