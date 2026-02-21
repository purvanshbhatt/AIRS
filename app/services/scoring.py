"""
AIRS Scoring Service

Calculates readiness scores based on assessment answers.
"""

from typing import Dict, Any, List, Optional
from app.core.rubric import RUBRIC, get_question


class ScoringError(Exception):
    """Raised when scoring encounters an error."""
    pass


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


def _score_question(question: dict, answer: Any) -> float:
    """
    Score a single question based on its type and the provided answer.
    
    Supports an optional ``tier_options`` field on a question for maturity-tier
    string answers (e.g. ">90%", "<4hrs", "Not Measured").  When a tier string
    is detected the mapped score is used directly.  Legacy numeric answers
    continue to use the threshold lookup so backwards-compatibility is preserved.
    
    Args:
        question: Question definition from rubric
        answer: The answer value
    
    Returns:
        Points earned (0 to question's max points)
    """
    q_type = question["type"]
    max_points = question["points"]
    
    if answer is None:
        return 0.0

    # ── Maturity-tier string handling (backward-compatible) ──
    # If the question publishes tier_options AND the answer is a recognised
    # tier value string, resolve to the mapped score without touching the
    # existing threshold logic below.
    tier_options = question.get("tier_options")
    if tier_options and isinstance(answer, str):
        canonical = answer.strip()
        for opt in tier_options:
            if opt["value"].lower() == canonical.lower():
                return max_points * opt["score"]
        # Unknown tier string → treat as unanswered (score 0) rather than
        # accidentally falling through to boolean "truthy" logic.
        return 0.0

    if q_type == "boolean":
        # Boolean: True = full points, False = 0
        if isinstance(answer, bool):
            return max_points if answer else 0.0
        if isinstance(answer, str):
            return max_points if answer.lower() in ("yes", "true", "1") else 0.0
        return max_points if answer else 0.0
    
    elif q_type in ("numeric", "percentage"):
        # Numeric/Percentage: Use thresholds
        try:
            value = float(answer)
        except (ValueError, TypeError):
            return 0.0
        
        thresholds = question.get("thresholds", {})
        lower_is_better = question.get("scoring_direction") == "lower_is_better"
        
        threshold_score = _calculate_threshold_score(value, thresholds, lower_is_better)
        return max_points * threshold_score
    
    return 0.0


def calculate_domain_score(domain_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate score for a single domain.
    
    Args:
        domain_id: The domain identifier
        answers: Dict mapping question_id to answer value
    
    Returns:
        Dict with domain scoring details
    """
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
        points = _score_question(question, answer)
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


def calculate_scores(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate complete readiness scores from assessment answers.
    
    Args:
        answers: Dict mapping question_id to answer value
                 Example: {"tl_01": True, "tl_05": 90, "dc_01": 85, ...}
    
    Returns:
        Complete scoring result with domain scores and overall score
    """
    domain_results = []
    weighted_sum = 0.0
    total_weight = 0
    
    for domain_id in RUBRIC["domains"]:
        domain_result = calculate_domain_score(domain_id, answers)
        domain_results.append(domain_result)
        
        # Calculate weighted contribution (score is 0-5, weight is %)
        # Contribution to 100-point scale: (score/5) * weight
        weighted_contribution = (domain_result["score"] / 5) * domain_result["weight"]
        weighted_sum += weighted_contribution
        total_weight += domain_result["weight"]
    
    # Overall score on 0-100 scale
    overall_score = round(weighted_sum, 2)
    
    # Determine maturity level
    maturity = _get_maturity_level(overall_score)
    
    return {
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
                for q in d["questions"] 
                if q["answer"] is not None
            ),
            "strongest_domain": max(domain_results, key=lambda x: x["score"])["domain_name"],
            "weakest_domain": min(domain_results, key=lambda x: x["score"])["domain_name"]
        }
    }


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
                domain_recs.append({
                    "priority": priority,
                    "domain": domain["domain_name"],
                    "domain_id": domain["domain_id"],
                    "question_id": question["question_id"],
                    "finding": question["question_text"],
                    "current_answer": question["answer"],
                    "points_gap": round(gap, 2),
                    "impact": "high" if gap >= 0.75 else "medium" if gap >= 0.5 else "low"
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
