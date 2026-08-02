# ADR-007: Deterministic Scoring Invariant

**Date:** 2026-07-12
**Status:** Permanent
**Supersedes:** None
**Extends:** ADR-001

## Context

Sprint 1.8 introduces `readiness_drivers.py` and `readiness_ledger.py`, which intercept the output of `app/services/scoring.py`. Sprint 2 introduces `decision_engine.py`, which performs "what-if" projections of scoring outcomes. Both changes create a risk of scoring logic being duplicated or sideloaded by another module.

## Decision

`app/services/scoring.py::calculate_readiness_delta()` is the **single** function permitted to produce readiness scores, deltas, or impact breakdowns. Any other module (`readiness_drivers.py`, `readiness_ledger.py`, `decision_engine.py`, `evidence_confidence.py`, `ai_frameworks.py`, frontend code) must consume its output and MUST NOT reimplement or approximate the calculation.

A bytecode-level import guard (`tests/test_llm_isolation.py`) further forbids any of those modules from importing `ai_narrative.py`, `intelligence.py`, `narrative/*`, `llm_narrative.py`, or `google.genai`.

## Consequences

- Any future scoring refactor must touch `scoring.py` in one place.
- The Decision Engine's projection is guaranteed equal to the post-state actual score; verified by `tests/test_decision_drift_guard.py` running on every CI build.
- If `scoring.py` ever changes signature, all consumers must be updated atomically in the same PR.
