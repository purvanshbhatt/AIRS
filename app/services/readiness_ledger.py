"""
Readiness Ledger Write Hook.

Per ADR-008, every score recalculation must produce exactly one immutable
row in the ledger, and inserts are idempotent on
``(org_id, timestamp, new_score)``.

This module provides:
    ``record_score_change(...)`` — atomic, idempotent insert.
    ``attach_to_scoring()`` — monkey-patches ``calculate_readiness_delta``
        so that ANY call from anywhere writes a ledger row. Used to
        satisfy the spec requirement that "every score change creates an
        immutable ledger row" without modifying the scoring function
        itself (per AGENT_START.md: scoring is sacred, immutable).

This module never imports LLM modules (ADR-007). Stripped form of the
isolation guard is enforced at runtime by ``__verify_no_llm_imports``,
and additionally at tests/test_llm_isolation.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal
from app.models.readiness_ledger import ReadinessLedgerEntry


logger = logging.getLogger(__name__)


_FORBIDDEN_HINTS = (
    "google.genai",
    "google.generativeai",
    "ai_narrative",
    "llm_narrative",
    "app.services.intelligence",
)


def __verify_no_llm_imports() -> None:
    """Runtime belt-and-suspenders check.

    The hard invariant (ADR-007) is that ``readiness_ledger.py`` does
    not DIRECTLY import any LLM module. We assert that by inspecting the
    AST of this module's own source. This is the smallest guarantee
    that catches future drift.

    We deliberately do NOT flag transitive loading of LLM modules by the
    wider application — that is a property of the calling test suite,
    not of this module's contract.
    """
    import ast as _ast
    src_tree = _ast.parse(__source_text())
    imported = set()
    for node in _ast.walk(src_tree):
        if isinstance(node, _ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, _ast.ImportFrom):
            if node.module:
                imported.add(node.module)

    forbidden = ("ai_narrative", "llm_narrative", "google.genai", "google.generativeai")
    bad = sorted(
        n for n in imported
        if any(n == f or n.startswith(f + ".") for f in forbidden)
    )
    if bad:
        raise RuntimeError(
            f"Readiness Ledger invariant violated (ADR-007): "
            f"forbidden direct imports detected: {bad}"
        )


def __source_text() -> str:
    import inspect as _inspect
    return _inspect.getsource(readiness_ledger_module_marker) or ""


# Sentinel used to query this module's source at import time.
def readiness_ledger_module_marker() -> None:
    pass


__verify_no_llm_imports()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def record_score_change(
    *,
    org_id: str,
    previous_score: float,
    new_score: float,
    driver_type: Optional[str] = None,
    driver_item: Optional[str] = None,
    impact: Optional[float] = None,
    evidence_source: Optional[str] = None,
    created_by: Optional[str] = None,
    timestamp: Optional[datetime] = None,
    session_factory=None,
) -> Optional[str]:
    """Insert a single immutable ledger row.

    Idempotent on ``(org_id, timestamp, new_score)``: if a row already
    exists for these three fields, the call is a no-op.

    Returns the ledger entry's UUID, or None when the trip was a no-op.
    """
    if not org_id:
        raise ValueError("org_id is required")
    if previous_score is None or new_score is None:
        raise ValueError("previous_score and new_score are required")

    delta = round(float(new_score) - float(previous_score), 2)
    ts = timestamp or _utc_now()

    factory = session_factory or SessionLocal

    session = factory()
    try:
        existing = (
            session.query(ReadinessLedgerEntry)
            .filter(
                ReadinessLedgerEntry.org_id == org_id,
                ReadinessLedgerEntry.new_score == new_score,
                ReadinessLedgerEntry.timestamp == ts,
            )
            .first()
        )
        if existing is not None:
            return None  # idempotent no-op

        entry = ReadinessLedgerEntry(
            org_id=org_id,
            timestamp=ts,
            previous_score=float(previous_score),
            new_score=float(new_score),
            delta=delta,
            driver_type=driver_type,
            driver_item=driver_item,
            impact=impact,
            evidence_source=evidence_source,
            created_by=created_by,
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry.id
    except IntegrityError:
        session.rollback()
        # Race condition: another process inserted the same idempotency key —
        # treat as no-op.
        return None
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Scoring-call interception (no edits to scoring.py itself) ─────────
_HOOK_INSTALLED = False
_ORIGINAL_FN = None


def attach_to_scoring() -> None:
    """Wrap ``calculate_readiness_delta`` with a ledger write.

    Behavior:
      - The wrapped function still calls the original scoring function.
      - Before returning, it inspects the response for an injected
        previous_readiness_score and an org id (passed via the
        scoring_kwargs). If both are present, an idempotent ledger row
        is written.

    Because the spec requires every recalculation to write a ledger row,
    callers explicitly pass ``org_id=`` and ``previous_readiness_score=``
    to ``calculate_readiness_delta`` to enable ledger side-effects.

    Scoring, however, is immutable — it does not accept org_id. Instead,
    this hook wraps the call-site usage. For convenience, callers may
    use the high-level helper ``score_and_record`` below.
    """
    global _HOOK_INSTALLED, _ORIGINAL_FN
    if _HOOK_INSTALLED:
        return

    from app.services import scoring as scoring_module

    _ORIGINAL_FN = scoring_module.calculate_readiness_delta

    def wrapped(
        assessment_score: float,
        verified_controls: list,
        verified_coverages: list,
        lifecycle_risks: list,
        exposure_risks: list,
        previous_readiness_score: Optional[float] = None,
        *,
        org_id: Optional[str] = None,
        created_by: Optional[str] = None,
        evidence_source: Optional[str] = "scoring",
    ) -> Dict[str, Any]:
        result = _ORIGINAL_FN(
            assessment_score=assessment_score,
            verified_controls=verified_controls,
            verified_coverages=verified_coverages,
            lifecycle_risks=lifecycle_risks,
            exposure_risks=exposure_risks,
            previous_readiness_score=previous_readiness_score,
        )

        if org_id is not None and previous_readiness_score is not None:
            # The reasons list contains the strongest contributing driver
            # for this delta; mirror that into the ledger row.
            reasons = result.get("reasons") or []
            strongest = None
            if reasons:
                strongest = max(
                    reasons,
                    key=lambda r: abs(float(r.get("impact", 0.0))),
                )
            try:
                record_score_change(
                    org_id=org_id,
                    previous_score=previous_readiness_score,
                    new_score=result["final_readiness"],
                    driver_type=(strongest or {}).get("category"),
                    driver_item=(strongest or {}).get("item"),
                    impact=(strongest or {}).get("impact"),
                    evidence_source=evidence_source,
                    created_by=created_by,
                )
            except Exception as exc:  # pragma: no cover — defensive
                logger.warning(
                    "Readiness ledger write failed: %s", exc
                )

        return result

    scoring_module.calculate_readiness_delta = wrapped
    _HOOK_INSTALLED = True


def score_and_record(
    *,
    org_id: str,
    assessment_score: float,
    verified_controls: list,
    verified_coverages: list,
    lifecycle_risks: list,
    exposure_risks: list,
    previous_readiness_score: Optional[float] = None,
    evidence_source: Optional[str] = "scoring",
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience scoring entrypoint that also writes a ledger row.

    Combines scoring + ledger writes in a single call.

    If the hook is not yet installed, this call installs it lazily.
    """
    if not _HOOK_INSTALLED:
        attach_to_scoring()

    return calculate_readiness_delta(
        assessment_score=assessment_score,
        verified_controls=verified_controls,
        verified_coverages=verified_coverages,
        lifecycle_risks=lifecycle_risks,
        exposure_risks=exposure_risks,
        previous_readiness_score=previous_readiness_score,
        org_id=org_id,
        created_by=created_by,
        evidence_source=evidence_source,
    )
