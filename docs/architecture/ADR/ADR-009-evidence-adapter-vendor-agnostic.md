# ADR-009: Evidence Adapters are Vendor-Agnostic

**Date:** 2026-07-12
**Status:** Accepted
**Supersedes:** None
**Extends:** ADR-003, ADR-005

## Context

The Splunk integration in Sprint 1 was a one-off API hook directly coupled to the Verification Engine. This makes adding SentinelOne, CrowdStrike, Okta, or AWS sources require touching verification logic. Spec Feature C mandates a vendor-agnostic adapter pattern.

## Decision

All third-party evidence sources implement the `EvidenceAdapter` ABC in `app/services/evidence/base_adapter.py` and register via `app/services/evidence/registry.py`. The Verification Engine accepts only `Evidence` records produced by an adapter; it has no knowledge of which vendor supplied them.

Swapping Splunk for SentinelOne requires implementing one new adapter class and registering it — no changes to `verification.py`, `scoring.py`, or `scoring_v2.py`.

## Consequences

- Third-party outages degrade to a per-adapter 503 instead of crashing the request.
- The Evidence Confidence metric (`app/services/evidence_confidence.py`) treats all sources uniformly.
- Per-vendor failure modes (token expiry, rate-limit, stale data) must be encoded in the adapter's `health()` method, not leaked upward.
- Adding a new vendor cannot bypass the Verification Engine; this preserves the PRODUCT_MOAT principle that telemetry beats questionnaires.
