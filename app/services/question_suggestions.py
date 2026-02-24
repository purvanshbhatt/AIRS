"""
Question Suggestion Service

Deterministic, rule-based engine that recommends assessment questions an
organization should focus on.  Zero LLM involvement.

Algorithm overview:
  1. Gather org's completed assessments and compute per-control-function
     average scores.
  2. Identify the weakest control function(s).
  3. Return questions aligned to those functions, prioritized by
     impact (high first), then maturity level (next tier up from org avg).

All metadata comes from ``app.core.question_catalog`` (static config).
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.rubric import RUBRIC, get_question
from app.core.question_catalog import QUESTION_CATALOG, CONTROL_FUNCTIONS
from app.models.assessment import Assessment, AssessmentStatus
from app.models.answer import Answer
from app.models.score import Score
from app.services.scoring import calculate_scores

logger = logging.getLogger("airs.suggestions")

# Map NIST CSF 2.0 short codes to control function names
_NIST_TO_FUNCTION = {
    "GV": "govern",
    "ID": "identify",
    "PR": "protect",
    "DE": "detect",
    "RS": "respond",
    "RC": "recover",
}

# Impact sort weight (higher is better priority)
_IMPACT_WEIGHT = {"high": 3, "medium": 2, "low": 1}
_MATURITY_RANK = {"basic": 1, "managed": 2, "advanced": 3}


def _org_maturity_label(avg_score: float) -> str:
    """Convert a 0-100 average score into a maturity label."""
    if avg_score < 40:
        return "basic"
    elif avg_score < 70:
        return "managed"
    return "advanced"


def _domain_to_function(domain_id: str) -> str:
    """Map a rubric domain_id to its NIST control function name."""
    domain = RUBRIC["domains"].get(domain_id, {})
    nist_code = domain.get("nist_function", "")
    return _NIST_TO_FUNCTION.get(nist_code, "detect")


def _compute_function_scores_from_db(
    db: Session, org_id: str
) -> Dict[str, float]:
    """
    Compute average scores per control function from persisted assessments.

    Returns dict like {"detect": 55.0, "protect": 72.0, ...}.
    Functions with no data default to 0.0.
    """
    # Get all completed assessments for this org
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.organization_id == org_id,
            Assessment.status == AssessmentStatus.COMPLETED,
        )
        .order_by(Assessment.completed_at.desc())
        .limit(10)  # Only consider latest 10
        .all()
    )

    if not assessments:
        return {fn: 0.0 for fn in CONTROL_FUNCTIONS}

    # Aggregate scores by control function across assessments
    function_totals: Dict[str, List[float]] = {fn: [] for fn in CONTROL_FUNCTIONS}

    for assessment in assessments:
        scores = (
            db.query(Score)
            .filter(Score.assessment_id == assessment.id)
            .all()
        )
        for score_row in scores:
            fn = _domain_to_function(score_row.domain_id)
            # Convert 0-5 score to percentage
            pct = (score_row.score / score_row.max_score) * 100 if score_row.max_score else 0
            function_totals[fn].append(pct)

    return {
        fn: round(sum(vals) / len(vals), 2) if vals else 0.0
        for fn, vals in function_totals.items()
    }


def _compute_function_scores_from_answers(
    answers: Dict[str, Any]
) -> Dict[str, float]:
    """
    Compute per-function scores from raw answers dict (no DB needed).
    Useful for in-memory / test scenarios.
    """
    result = calculate_scores(answers)
    function_totals: Dict[str, List[float]] = {fn: [] for fn in CONTROL_FUNCTIONS}

    for domain in result["domains"]:
        fn = _domain_to_function(domain["domain_id"])
        pct = (domain["score"] / domain["max_score"]) * 100 if domain["max_score"] else 0
        function_totals[fn].append(pct)

    return {
        fn: round(sum(vals) / len(vals), 2) if vals else 0.0
        for fn, vals in function_totals.items()
    }


def get_suggestions(
    db: Session,
    org_id: str,
    *,
    max_results: int = 10,
    industry: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return deterministic question suggestions for an organization.

    Algorithm:
      1. Compute per-control-function average scores.
      2. Rank functions by score ascending (weakest first).
      3. For the weakest function(s), select questions where:
         a. maturity_level >= org's next-tier maturity
         b. impact_level is high (preferred)
      4. Sort by impact desc, then effort asc.
      5. Cap at max_results.

    Args:
        db:          SQLAlchemy session
        org_id:      Organization UUID
        max_results: Maximum suggestions to return (default 10)
        industry:    Optional industry tag (reserved for future use)

    Returns:
        List of suggestion dicts with question text + metadata.
    """
    function_scores = _compute_function_scores_from_db(db, org_id)
    return _build_suggestions(function_scores, max_results=max_results, industry=industry)


def get_suggestions_from_answers(
    answers: Dict[str, Any],
    *,
    max_results: int = 10,
    industry: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Stateless variant: compute suggestions from raw answers without DB.
    """
    function_scores = _compute_function_scores_from_answers(answers)
    return _build_suggestions(function_scores, max_results=max_results, industry=industry)


def _build_suggestions(
    function_scores: Dict[str, float],
    *,
    max_results: int = 10,
    industry: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Core suggestion builder (pure function, no I/O).
    """
    # Overall average to determine org maturity
    all_scores = [v for v in function_scores.values() if v > 0]
    org_avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
    org_maturity = _org_maturity_label(org_avg)
    org_maturity_rank = _MATURITY_RANK[org_maturity]

    # Sort functions by score ascending — weakest first
    ranked_functions = sorted(function_scores.items(), key=lambda x: x[1])

    # Determine which functions to target (lowest + any within 10pts of lowest)
    threshold = ranked_functions[0][1] + 10.0 if ranked_functions else 100.0
    target_functions = {fn for fn, score in ranked_functions if score <= threshold}

    # If org is perfect on everything, still return advanced questions
    if not target_functions or all(v >= 90 for v in function_scores.values()):
        target_functions = set(CONTROL_FUNCTIONS)

    # Collect candidate questions
    candidates: List[Dict[str, Any]] = []
    for qid, meta in QUESTION_CATALOG.items():
        if meta["control_function"] not in target_functions:
            continue

        # Prefer questions at or above org's next maturity tier
        q_maturity_rank = _MATURITY_RANK[meta["maturity_level"]]
        # Include questions at current or next tier
        if q_maturity_rank < org_maturity_rank:
            continue

        # Resolve question text from rubric
        question_def, domain_id = get_question(qid)
        if not question_def:
            continue

        candidates.append({
            "id": qid,
            "question_text": question_def["text"],
            "framework_tags": meta["framework_tags"],
            "maturity_level": meta["maturity_level"],
            "effort_level": meta["effort_level"],
            "impact_level": meta["impact_level"],
            "control_function": meta["control_function"],
            "domain_id": domain_id,
        })

    # Sort: impact desc, effort asc, maturity asc
    candidates.sort(
        key=lambda c: (
            -_IMPACT_WEIGHT.get(c["impact_level"], 0),
            _IMPACT_WEIGHT.get(c["effort_level"], 2),
            _MATURITY_RANK.get(c["maturity_level"], 1),
        )
    )

    suggestions = candidates[:max_results]

    logger.info(
        "Generated %d suggestions for org (avg=%.1f, maturity=%s, targets=%s)",
        len(suggestions),
        org_avg,
        org_maturity,
        target_functions,
    )

    return suggestions
