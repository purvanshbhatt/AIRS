# ADR-012: Decision Engine Delegates to Scoring

**Date:** 2026-07-12
**Status:** Accepted
**Supersedes:** None
**Extends:** ADR-001, ADR-007

## Context

Sprint 2 introduces `decision_engine.py` for "what-if" projection of remediation actions. The spec explicitly warns: "The Decision Engine projection drifting from the actual score calculation if logic is duplicated."

## Decision

`app/services/decision_engine.py::project_readiness()` does NOT implement scoring. It applies hypothetical state to a transient copy, then calls `calculate_readiness_delta()` from `app/services/scoring.py` exactly as the live path does. The return value of `project_readiness(proposed_actions)` MUST equal the value `calculate_readiness_delta()` returns after the corresponding actual DB state change.

This equality is enforced by `tests/test_decision_drift_guard.py`, which runs on every CI build across ≥ 20 fixture sets. Any drift blocks merge.

## Consequences

- The Decision Engine FRONTEND (`DecisionEngine.tsx`) is forbidden from computing projected scores client-side. It MUST call `POST /api/v1/decisions/project`.
- If `scoring.py` changes semantics, the Decision Engine automatically inherits the change — no parallel update.
- The Organization clone fields (`is_clone`, `source_org_id`) added in S2-B4 are the architectural prep for Sprint 2.5 Digital Twin; they are schema-only in Sprint 2 and have no behavior.
