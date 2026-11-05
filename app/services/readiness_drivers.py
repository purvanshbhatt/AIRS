"""
Readiness Driver Extraction.

Consumes the ``reasons`` block produced by
``app.services.scoring.calculate_readiness_delta()`` and emits a sorted list
of drivers suitable for executive consumption.

Per ADR-007, this module NEVER reimplements scoring — it only consumes the
``calculate_readiness_delta()`` output. This module never imports
``ai_narrative``, ``llm_narrative``, or any LLM client. Anti-LLM guard is
also enforced by ``tests/test_llm_isolation.py``.
"""

from typing import Any, Dict, List, Optional

from app.services.scoring import calculate_readiness_delta


_DRIVER_CATEGORIES = {"Verification", "Coverage", "Lifecycle", "Exposure"}


def _extract_impact(reason: Dict[str, Any]) -> float:
    """Extract an impact value from a scoring reason dict.

    Scoring reasons have shape:
        {"category": ..., "control_family": ..., "item": ...,
         "impact": float, "reason": ...}

    For Verification/Coverage, impact > 0 (bonus).
    For Lifecycle/Exposure, impact < 0 (penalty) — though the scoring
    function emits negative values for those cases.
    """
    return float(reason.get("impact", 0.0) or 0.0)


def _driver_from_reason(reason: Dict[str, Any]) -> Dict[str, Any]:
    """Map a scoring ``reasons`` entry to a clean driver record."""
    return {
        "driver_type": str(reason.get("category", "")).lower(),
        "driver_item": reason.get("item"),
        "impact": _extract_impact(reason),
        "evidence_source": _derive_evidence_source(reason),
    }


def _derive_evidence_source(reason: Dict[str, Any]) -> str:
    """Best-effort mapping from controller category to evidence source.

    Categories:
      - Verification  → telemetry (live control checks)
      - Coverage      → deployment (asset inventory check)
      - Lifecycle     → vendor (catalogued lifecycle data)
      - Exposure      → telemetry (KEVs and internet exposure feed)

    The exact source is intentionally left to a downstream enrichment
    step; here we surface the structural family only.
    """
    category = str(reason.get("category", "")).lower()
    return {
        "verification": "telemetry",
        "coverage": "deployment",
        "lifecycle": "vendor",
        "exposure": "telemetry",
    }.get(category, "unknown")


def extract_drivers(
    *,
    assessment_score: float,
    verified_controls: List[Dict[str, Any]],
    verified_coverages: List[Dict[str, Any]],
    lifecycle_risks: List[Dict[str, Any]],
    exposure_risks: List[Dict[str, Any]],
    top_n: int = 5,
    previous_readiness_score: Optional[float] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Produce sorted top-N positive and top-N negative drivers.

    Args:
        assessment_score: Baseline 0-100 score as passed to scoring.
        verified_controls: Verified controls list.
        verified_coverages: Coverage data.
        lifecycle_risks: Lifecycle data.
        exposure_risks: Exposure data.
        top_n: Number of drivers on each side (default 5).
        previous_readiness_score: Optional prior readiness for delta
            computation (consumed by ``calculate_readiness_delta``).

    Returns:
        A dict:
            {
                "positive_drivers": [ {driver_type, driver_item, impact,
                                       evidence_source}, ... ],
                "negative_drivers": [ same shape sorted ascending ],
            }

    """
    if top_n < 1:
        raise ValueError(f"top_n must be >= 1; got {top_n}")

    delta_result = calculate_readiness_delta(
        assessment_score=assessment_score,
        verified_controls=verified_controls,
        verified_coverages=verified_coverages,
        lifecycle_risks=lifecycle_risks,
        exposure_risks=exposure_risks,
        previous_readiness_score=previous_readiness_score,
    )

    reasons = delta_result.get("reasons") or []
    drivers = [_driver_from_reason(r) for r in reasons]

    # Filter out zero-impact drivers (e.g., a coverage data point below
    # the 80% threshold contributes nothing — should not be elevated as
    # a top driver).
    nonzero = [d for d in drivers if d["impact"] != 0.0]

    # Sort by absolute impact descending for each sign.
    positives = sorted(
        (d for d in nonzero if d["impact"] > 0),
        key=lambda d: d["impact"],
        reverse=True,
    )
    negatives = sorted(
        (d for d in nonzero if d["impact"] < 0),
        key=lambda d: d["impact"],  # ascending: -1 before -7
    )

    return {
        "positive_drivers": positives[:top_n],
        "negative_drivers": negatives[:top_n],
    }


def extract_action_items(
    *,
    assessment_score: float,
    verified_controls: List[Dict[str, Any]],
    verified_coverages: List[Dict[str, Any]],
    lifecycle_risks: List[Dict[str, Any]],
    exposure_risks: List[Dict[str, Any]],
    top_n: int = 5,
    previous_readiness_score: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Render negative drivers as 'Executive Actions' (Mon-morning list).

    Each item is rendered as a deterministic instruction with a
    structured shape for direct API consumption. No LLM.
    """
    drivers = extract_drivers(
        assessment_score=assessment_score,
        verified_controls=verified_controls,
        verified_coverages=verified_coverages,
        lifecycle_risks=lifecycle_risks,
        exposure_risks=exposure_risks,
        top_n=top_n,
        previous_readiness_score=previous_readiness_score,
    )

    actions: List[Dict[str, Any]] = []
    for driver in drivers["negative_drivers"]:
        actions.append(
            {
                "driver_type": driver["driver_type"],
                "item": driver["driver_item"],
                "impact": driver["impact"],
                "evidence_source": driver["evidence_source"],
                "rationale": (
                    f"Address {driver['driver_item']} "
                    f"({driver['driver_type']}) to recover "
                    f"{abs(driver['impact']):.1f} readiness points."
                ),
            }
        )
    return actions
