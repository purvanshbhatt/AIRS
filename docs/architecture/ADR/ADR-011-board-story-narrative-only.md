# ADR-011: Board Story is Narrative-Only

**Date:** 2026-07-12
**Status:** Accepted
**Supersedes:** None
**Extends:** ADR-002, ADR-007

## Context

Spec Feature D requires a multi-section Board Story view with 10 canonical sections. The risk is the LLM injecting fabricated metrics, scores, or trend lines into narrative prose — which would break the "LLMs never score" invariant by implication.

## Decision

`app/services/ai_narrative.py` (and its `narrative/*` helpers) emits exactly 10 sections in a fixed, code-defined order. Section existence/IDs are determined by code, never by the LLM. The LLM only generates prose within each section.

A post-parse validator (`S2-A2` task) rejects any numeric value appearing in the narrative that does not trace back to the source scoring snapshot. Rejection triggers a deterministic fallback prose generator, not blank output.

## Consequences

- Even a fully compromised Gemini prompt cannot fabricate metrics that reach the user — fabricated numbers are stripped before rendering.
- Board Story structure is stable across regenerations, enabling section-level diffing and caching.
- The Board Story page (`BoardStory.tsx`) renders 10 sections deterministically and treats prose as opaque strings — never parsing numbers from narrative back into the UI.
