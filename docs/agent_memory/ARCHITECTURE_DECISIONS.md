# Architecture Decisions

> Formal ADR records live in `docs/architecture/ADR/`. The summaries below are the canonical index. New ADRs are numbered sequentially and MUST NOT reuse or renumber existing IDs.

ADR-001
Decision: Use deterministic scoring.
Reason: Enterprise trust. LLMs should not generate scores randomly.
Status: Permanent.

ADR-002
Decision: Gemini only generates narratives.
Reason: Prevents hallucination in critical security assessment data.
Status: Permanent.

ADR-003
Decision: Verification state system.
States: VERIFIED, PARTIAL, SELF_ATTESTED, UNVERIFIED
Status: Accepted.

ADR-004
Decision: SQLite Cache over Firestore
Reason: Firestore reads can be slow and expensive. The API synchronizes Firestore data into a local SQLite cache on startup for fast reads.
Status: Active.

ADR-005
Decision: Asynchronous Auto-Discovery
Reason: External API calls (Wazuh, Splunk) take longer than typical API timeout windows. Auto-discovery must run in the background.
Status: Active.

ADR-006
Decision: CORSErrorSafetyMiddleware wraps entire middleware stack.
Reason: Cloud Run strips CORS headers on 5xx/504 responses. A safety-net middleware must be the outermost layer to catch errors and guarantee CORS headers are always present. It must always be the LAST `add_middleware()` call in `app/main.py`.
Status: Permanent.

ADR-007
Decision: Deterministic Scoring Invariant — single source `calculate_readiness_delta()`; bytecode guard forbids narrative imports.
Reason: Sprint 1.8/2 add consumers (drivers, ledger, decision engine); prevent silent duplication.
Status: Permanent. Extends ADR-001.
Record: `docs/architecture/ADR/ADR-007-deterministic-scoring-invariant.md`

ADR-008
Decision: Readiness Ledger is immutable (write-once, idempotent insert).
Reason: Point-in-time audit reconstruction; prevent future agents rewriting readiness history.
Status: Accepted. Extends ADR-001, ADR-003.
Record: `docs/architecture/ADR/ADR-008-readiness-ledger-immutable.md`

ADR-009
Decision: Evidence Adapters are vendor-agnostic (`EvidenceAdapter` ABC + registry).
Reason: Adding SentinelOne/CrowdStrike/Okta must not require touching verification or scoring.
Status: Accepted. Extends ADR-003, ADR-005.
Record: `docs/architecture/ADR/ADR-009-evidence-adapter-vendor-agnostic.md`

ADR-010
Decision: Evidence Confidence is deterministic (Freshness × Uptime × Success Rate × Completeness). No LLM.
Reason: This metric influences executive trust; hallucinating it destroys trust like hallucinating a readiness score.
Status: Accepted. Extends ADR-001, ADR-009.
Record: `docs/architecture/ADR/ADR-010-evidence-confidence-deterministic.md`

ADR-011
Decision: Board Story is narrative-only (10 fixed sections; numeric-trace validator rejects fabricated metrics).
Reason: Prevent the LLM from inserting fabricated scores into board-level prose.
Status: Accepted. Extends ADR-002, ADR-007.
Record: `docs/architecture/ADR/ADR-011-board-story-narrative-only.md`

ADR-012
Decision: Decision Engine delegates to scoring; `project_readiness()` MUST equal post-state actual score (regression-enforced).
Reason: Spec's anti-drift AC; preserve scoring invariant under what-if projection.
Status: Accepted. Extends ADR-001, ADR-007.
Record: `docs/architecture/ADR/ADR-012-decision-engine-delegates-to-scoring.md`
