# ADR-010: Evidence Confidence is Deterministic

**Date:** 2026-07-12
**Status:** Accepted
**Supersedes:** None
**Extends:** ADR-001, ADR-009

## Context

Spec Feature C introduces an "Evidence Confidence" score (formerly Trust Score) that aggregates the reliability of telemetry from all connected evidence sources. Because it is consumed by the Trust Dashboard and influences executive decision-making, hallucinating this number would destroy trust identically to hallucinating a readiness score.

## Decision

`app/services/evidence_confidence.py` computes a 0–100 score via the fixed formula:

```
confidence = freshness_weight × uptime_weight × success_rate_weight × completeness_weight
```

All four factors are deterministic, sourced from adapter `health()` output and the existing Connector/Evidence tables. No LLM is permitted in this module. The bytecode guard in `tests/test_llm_isolation.py` enforces this at CI time.

## Consequences

- The metric is reproducible: identical adapter health states produce identical scores.
- Third-party API degradation drops the score deterministically; the UI must surface the cause (stale / unavailable / partial), not silently lower the gauge.
- Adjusting factor weights requires a new ADR; it is not a runtime config.
