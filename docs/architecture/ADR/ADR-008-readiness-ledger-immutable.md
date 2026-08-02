# ADR-008: Readiness Ledger is Immutable

**Date:** 2026-07-12
**Status:** Accepted
**Supersedes:** None
**Extends:** ADR-001, ADR-003

## Context

Prior to Sprint 1.8, score deltas were calculated live but never persisted. This made point-in-time audit reconstruction impossible. Spec Feature A requires an immutable `ReadinessLedgerEntry` so every score change is reconstructable.

## Decision

`ReadinessLedgerEntry` rows are write-once. UPDATE and DELETE are forbidden at the ORM layer (SQLAlchemy event listener rejects both) and at the DB layer (revoked grants on the staging role for those statements). Reads are always by `org_id` + ordered by `timestamp`.

Insert is idempotent on `(org_id, timestamp, new_score)` — replaying a recalculation must not produce duplicate rows.

## Consequences

- Every readiness change produces exactly one ledger row.
- Replay/idempotency eliminates storm-of-writes during scoring recompute loops.
- Migration includes the role-grant revocation; rollback re-grants UPDATE/DELETE.
- This ADR protects against future agents silently rewriting readiness history.
