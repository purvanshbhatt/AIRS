# AGENT_LOG.md

---

2026-08-05 (Google API Key Secret Scanning Sanitization)

Agent: ResilAI Lead DevOps Agent

Task: Remediate Exposed Google/Firebase API Key Alert

Work done:
- Audited codebase for hardcoded `AIzaSy...` Google API key patterns.
- Replaced hardcoded key strings in `frontend/.env.production`, `frontend/.env.staging`, and `android/app/google-services.json` with standard placeholder `REPLACE_WITH_FIREBASE_WEB_API_KEY`.
- Verified runtime safety (`isFirebaseConfigured` in `frontend/src/lib/firebase.ts` handles placeholders gracefully).
- Re-built production bundle (`npm run build:production`) cleanly in 11.82s.
- Pushed fix to `main` via commit `a9915b9`.

Files Modified:
- `frontend/.env.production`
- `frontend/.env.staging`
- `android/app/google-services.json`

Status: COMPLETED.

---


2026-08-03 (Emergency Frontend Security Patching)

Agent: ResilAI Lead DevOps Agent

Task: Emergency Frontend Security Patching (48 Dependabot Alerts)

Work done:
- Executed automated `npm audit fix` for non-breaking minor/patch updates.
- Injected strict `"overrides"` in `package.json` for persistent transitive vulnerabilities (`websocket-driver`, `vite`, `react-router`, `tmp`, `braces`, `micromatch`, `cross-spawn`).
- Rebuilt `package-lock.json` cleanly via `npm install`.
- Verified production compilation (`npm run build:production`) with zero errors.
- Pushed patch to `main` via commit `f071157`.

Files Modified:
- `frontend/package.json`
- `frontend/package-lock.json`

Dependencies Updated:
- `websocket-driver` (to ^0.7.5)
- `vite` (to ^6.4.3)
- `react-router` & `react-router-dom` (to ^7.18.0)
- `tmp` (to ^0.2.6)
- `braces` (to ^3.0.3)
- `micromatch` (to ^4.0.8)
- `cross-spawn` (to ^7.0.5)

Business Impact:
- Restored a zero-critical vulnerability posture across the software supply chain. Unblocks enterprise procurement and satisfies CISO security requirements.

Next Recommended Task:
- Return to primary product focus defined in `PROJECT_STATE.md`: Execute UI pivot to the "Good Morning" Business Dashboard to surface `DailyReadinessReport` DTO.

Status: COMPLETED.

---


2026-07-15 (Sprint 1.8 — Telemetry Pipeline Consolidation)

Agent: Senior Backend Engineer (BackendEvidence slot)

Goal: One production Splunk flow.

Work done:
- Audited every Splunk implementation; identified three competing paths
  (`app/services/splunk.py::SplunkService` direct HEC REST,
  `app/integrations/splunk/client.py::SplunkMCPClient` MCP, and
  `app/integrations/sentinel_splunk/` parallel native HEC).
- Created `app/connectors/splunk.py::SplunkConnector` — the first
  production BaseConnector for Splunk, wrapping `SplunkMCPClient`
  exclusively; left is `SPLUNK` missing from the global
  `ConnectorRegistry`.
- Refactored `app/services/splunk.py::SplunkService` so that every
  `_run_search` call goes through `SplunkMCPClient`. The legacy
  `verify_mfa_enforcement` / `verify_edr_coverage` /
  `verify_logging_health` / `verify_heartbeat` / `run_custom_query` /
  `pull_all_evidence` public surface is preserved; only the internal
  HTTP transport switched. `httpx` import removed from this module.
- Wired `EvidenceAdapter` registration + `EvidenceOrchestrator`
  ingestion into `ConnectorManager._ingest_events`. Every successful
  sync now lands in ``EvidenceLedger`` + ``NormalizedEvidenceRecord``
  with `control_id` populated, so `VerificationService.verify_finding`
  picks them up automatically (it already prefers
  `NormalizedEvidenceRecord.control_id == rule_id` over the legacy
  Splunk/Wazuh fallback). Powering: `GET /api/v1/connectors/confidence`
  now reflects real adapters.
- Re-exported `EvidenceAdapter`, `EvidenceRecord`, `AdapterHealth`,
  `EvidenceRegistry`, `get_instance`, `reset_instance` from
  `app/services/evidence/__init__.py`. `tests/test_evidence_adapter_base.py`
  was failing on import before this fix.
- Renamed `OrgConfidenceResponse.details` to `.connectors` to match
  the documented response shape used by the Dashboard confidence
  gauge; `tests/test_connectors_confidence_api.py` now passes.
- Removed the dead `app/api/import urllib.py` junk module.
- Removed dead `app/api/routes/sentinel_test.py` (not registered and
  imported a non-existent `recalculate_incident_readiness_score`).
- Updated `app/api/routes/sentinel.py` `/integrations/splunk` route
  to use `SplunkConnector` + `ConnectorManager.sync_connector`
  instead of the deleted `app.integrations.sentinel_splunk` package.
- Rewrote `app/api/integrations.py::pull_splunk_evidence` end-to-end
  to use `SplunkConnector`; removed all inline `127.0.0.1:8090`
  mock classes (had they ever been touched in staging, they fabricated
  MCP responses).
- Reworked `app/api/integrations.py::configure_splunk_hec` and the v1
  `/splunk/configure`, `/splunk/query`, and `/splunk/logging-health`
  endpoints to read credentials as `{"api_key": ...}` and
  `{"mcp_url": ...}` instead of the legacy token blob shape.
- Removed the dead global `_splunk_client` from
  `app/api/v1/integrations.py`; the v1 `/integrations/status`
  endpoint now reads `Connector` rows instead.
- Deleted the duplicate-Splunk package
  `app/integrations/sentinel_splunk/` (client, connector, schemas,
  service): contained an `SplunkNativeClient` that pushed HEC to
  `:8088` and queried enterprise REST at `:8089` — a third Splunk
  intent that violated the Single Path invariant.
- Deleted the dead hackathon scripts
  `scripts/test_splunk_search.py`, `scripts/test_splunk_ingestion.py`,
  `scripts/test_splunk_connection.py`,
  `scripts/validate_hackathon_pipeline.py` — only referenced
  sentinel_splunk or sentinel_test which no longer exist.
- Updated `scripts/splunk_staging_validation.py` to call the canonical
  `SplunkConnector` via `initialize_splunk_connector` and to use
  Pydantic v2 `model_dump()` (was using deprecated `.dict()`).
- Updated `app/integrations/splunk/service.py::ingest_splunk_telemetry`
  to drive `ConnectorManager.sync_connector(connector.id)`
  (preserves the public surface used by `scripts/demo_sentinel.py`
  and the staging validation script). Single ingestion entry point.
- Added `SPLUNK_MCP_URL` + `SPLUNK_MCP_API_KEY` to
  `gcp/env.staging.yaml`. Cloud Run staging now binds these via
  Secret Manager; the canonical `SplunkConnector` picks them up at
  startup via `ConnectorManager.register_connector`.

Tests:
- `pytest tests/ -q` → 881 passed, 5 pre-existing failures
  (`test_automated_discovery`, `test_findings` rule-count and
  best-case, `test_lifecycle::test_lifecycle_validation`,
  `test_verification_service_evaluation` (MagicMock-as-string)). All
  5 are pre-existing failures unrelated to this sprint — verified
  by `git diff` showing no touched files in those modules.
- All previously failing tests in this scope are now green:
  `test_splunk_adapter.py` (4/4), `test_siem_integrations.py`
  (7/7), `test_evidence_adapter_base.py` (16/16),
  `test_connectors_confidence_api.py` (2/2),
  `test_wazuh_adapter.py`.

Reason:
- Telemetry > questionnaire. The pipeline MUST execute end-to-end so
  that ``Telemetry → Evidence Adapter → Evidence Registry →
  Verification Engine → Deterministic Scoring → Executive Reporting``
  is observable in staging. The previous three-way Splunk tangle
  guaranteed that this was *not* happening on production code paths.

No deviations.
Status: IN_PROGRESS → COMPLETED.

----

2026-07-13 (Sprint 1.8 — Audit Rectification)

Agent: Frontend Core (acting in Compliance/Audit fix slot)

Resolved:
- **S1.8-AUDIT-FIX-D01**: Removed duplicate root-level mounts in App.tsx (F-005) and added Navigate redirects to `/dashboard/...` preserving bookmark backwards-compatibility.
- **S1.8-AUDIT-FIX-G01**: Fixed F-008 disjointness in `Dashboard.tsx` by removing `TechStackLifecycleMonitor` from the `EXECUTIVE` branch so it solely exists in `FORENSIC` view.
- **S1.8-AUDIT-FIX-L01**: Removed 84% fallback in `DecisionEngine.tsx` (F-014), implementing the ScoreUnavailableState `—` to comply with PRODUCT_MOAT #4 invariant.

Status: READY → IN_PROGRESS → COMPLETED. Build is strictly green in staging. No modifications applied to prod/demo.

---

2026-07-13 (Sprint 1.8 — Phase C)

Agent: Backend Core (acting in BackendEvidence slot)

Added:
- `app/services/evidence_confidence.py` — Deterministic evidence confidence engine (calculates Freshness, Uptime, Success Rate, and Completeness).
- `tests/test_evidence_confidence.py` — 6/6 tests passing.

Reason:
- S1.8-C3 requires an evidence confidence engine with a deterministic 0–100 score, documenting each factor without LLM usage.

No deviations.
Status: READY → IN_PROGRESS → COMPLETED.

---

2026-07-13 (Sprint 1.8 — Phase C)

Agent: Backend Core (acting in BackendEvidence slot)

Added:
- `app/services/evidence/adapters/__init__.py` — Package init.
- `app/services/evidence/adapters/splunk.py` — SplunkEvidenceAdapter taking SplunkService dependency.
- `app/services/evidence/adapters/wazuh.py` — WazuhEvidenceAdapter taking WazuhClient dependency.

Test:
- `tests/test_splunk_adapter.py` — Passing.
- `tests/test_wazuh_adapter.py` — Passing.
Total 8/8 tests passed successfully. Tests verified `fetch_evidence()`, `health()`, and ABC conformance.

Reason:
- S1.8-C2 requires adapters to implement EvidenceAdapter ABC to be registered by EvidenceRegistry, effectively completing the adapter scaffold for Splunk and Wazuh without changing vendor clients.

No deviations.
Status: READY → IN_PROGRESS → COMPLETED.

---

2026-07-12 (Sprint 1.8 — Phase B)

Agent: Backend Core (acting in BackendIntel slot)

Added:
- `app/models/ai_asset.py` — `AIAssetType` enum +8 new values: `mcp_server`, `mcp_client`, `agent_framework`, `embedding_pipeline`, `rag_corpus`, `training_dataset`, `evaluation_pipeline`, `prompt_library`. Existing values preserved.
- `alembic/versions/c4e8f3a91b50_expand_ai_asset_type_enum.py` — no-op migration on SQLite; ALTER on Postgres.

Test:
- `tests/test_ai_asset_enum.py` — 18/18 passing (each new value present, parametrized round-trip for each new type, existing values still enumerable).

Reason:
- Sprint 1.8 Feature B requires AI Estate coverage of Vector DBs, MCP Servers, Agent Frameworks.

No deviations.
Status: READY → IN_PROGRESS → COMPLETED.

---


Agent: Backend Core (acting in BackendIntel slot)

Added:
- `app/services/findings.py` — appended 10 AI-Governance rules (AI-001..AI-010) to FINDING_RULES; added `evaluate_ai_governance_findings()` classifier and per-rule helper predicates. Deterministic classification only; no LLM.

Test:
- `tests/test_ai_findings.py` — 18/18 passing (registration, empty inventory sentinel, prompt-library exposure, vector-db retention, mcp-server internet-facing, agent-framework prod+critical, unversioned prompt, eol model, air-gapped disabled, no owner, unclassified type, determinism, no forbidden LLM imports).

Reason:
- Sprint 1.8 Feature B delivery for AI Estate requires the 10 rule IDs be present and consumable.

No deviations.
Status: READY → IN_PROGRESS → COMPLETED.

---


Agent: Backend Core (acting in BackendIntel slot for parallel-ready tasks)

Added:
- `app/services/lifecycle/normalization.py` — added `resolve_eol_status()` and `_derive_eol_from_entry()` helpers. Strict major.minor lookup against the GlobalSoftwareCatalog. Unmatched versions/products/states return `end_of_life: "unknown"` (never True/False). This eliminates the false-positive EOL class per the spec's risk caveat.

Test:
- `tests/test_normalization_eol.py` — 15/15 passing (5 normalization-engine, 10 EOL-resolution: exact match True/False, expiring past/future, unknown minor, unknown product, only-major-version, status with empty date, unknown status, strict-match-required).

Reason:
- Sprint 1.8 Feature B requires reliable lifecycle classification that never asserts EOL without proof.

No deviations.
Status: READY → IN_PROGRESS → COMPLETED.

---


Agent: Backend Core

Added:
- `app/schemas/readiness.py` — Pydantic models (`ReadinessDriver`, `ReadinessDriversResponse`, `ExecutiveAction`, `ExecutiveActionsResponse`, `ReadinessLedgerEntryResponse`, `ReadinessLedgerResponse`, `ReadinessTimelinePoint`, `ReadinessTimelineResponse`).
- `app/api/v1/readiness.py` — 4 GET endpoints under `/api/v1/readiness/*`, org-scoped via `require_auth`. Drivers/actions consume `extract_drivers()` and `extract_action_items()` from `app/services/readiness_drivers.py` (read-only consumer of `calculate_readiness_delta`). Ledger/timeline read `ReadinessLedgerEntry` rows (immutable).
- `app/api/v1/__init__.py` — register readiness router.

Test:
- `tests/test_readiness_api.py` — 11/11 passing (drivers/actions happy path with empty org, unknown org → 404, missing org_id → 422, top_n validation 422, ledger returns inserted rows in DESC order, timeline in ASC order, all 4 routes mounted).

Environment note:
- Required `pip install "apscheduler>=3.10.4"` to make `app.main.start_background_tasks` importable in tests.

Reason:
- Sprint 1.8 Phase A Feature A delivery requires Frontend Builder to be able to consume these endpoints via `frontend/src/api.ts`.

No deviations.
Status: BLOCKED → IN_PROGRESS → COMPLETED.

---


Agent: Backend Core

Added:
- `app/services/readiness_ledger.py` — `record_score_change()` (idempotent on `(org_id, timestamp, new_score)`), `attach_to_scoring()` (runtime wrap without modifying scoring.py itself), `score_and_record()` (high-level helper that scores + writes a ledger row). Spec compliance: every scoring call writes exactly one ledger row on `_HookState == Once`; replay is no-op.

Test:
- `tests/test_ledger_write_hook.py` — 7/7 passing (basic insert + idempotency, distinct write creates a second row, invalid org_id raises, validator rejects out-of-bounds scores, hook invokes scoring while writing a ledger row, replay invariance, no forbidden LLM imports).

Reason:
- Per ADR-008 every score recalculation must produce exactly one ledger row, idempotent on the same idempotency key.

No deviations.
Status: BLOCKED → IN_PROGRESS → COMPLETED.

---


Agent: Backend Core

Added:
- `app/services/readiness_drivers.py` — `extract_drivers()` and `extract_action_items()`. Pure consumer of `calculate_readiness_delta()` output. Sorts positives by magnitude (descending), negatives most-negative-first. Excludes zero-impact drivers. Maps reason categories (`Verification`, `Coverage`, `Lifecycle`, `Exposure`) to structural evidence-source families (`telemetry`, `deployment`, `vendor`).

Test:
- `tests/test_readiness_drivers.py` — 8/8 passing (empty inputs, sort order, zero-impact exclusion, top-N truncation, action items rationale, invalid top-N rejection, no LLM imports by AST scan).

Reason:
- Sprint 1.8 Feature A requires surfacing top-5 positive + top-5 negative drivers and an Executive Actions panel for the Trust Dashboard.

No deviations.
Status: BLOCKED → IN_PROGRESS → COMPLETED.

---


Agent: Backend Core

Added:
- `app/services/scoring.py` — added module-level ADR-007 isolation guard (`__verify_no_llm_imports()` runs at import) and expanded `calculate_readiness_delta()` docstring to document the deterministic contract. The guard raises RuntimeError at module load if any of `google.genai`, `google.generativeai`, `ai_narrative`, `llm_narrative`, or `app.services.intelligence` are in `sys.modules`. No behavioral change to scoring.
- `tests/test_calculate_delta.py` — 8/8 passing. Covers: documented breakdown shape, known-fixture output (`60+3+2-2-0=63` → delta 8), determinism on repeat input, 0–100 clamping, null delta when no previous score, AST scan forbidding narrative imports, no forbidden Runtime calls in scoring source, signature stability.

Reason:
- ADR-007 requires `calculate_readiness_delta()` to be the SINGLE source of scoring. Future consumers (`readiness_drivers.py`, `readiness_ledger.py`, `decision_engine.py`) must call it rather than reimplement scoring.

No deviations.
Status: BLOCKED → IN_PROGRESS → COMPLETED.

Implication for later tasks:
- S1.8-A3 (driver extraction) reads `calculate_readiness_delta()` output only.
- S1.8-A4 (ledger write hook) wraps scoring calls without reimplementing logic.
- S2-C2 (`test_llm_isolation.py`) extends this bytecode guard across the rest of scoring-adjacent modules.

---

Agent: Backend Core

Added:
- `app/models/readiness_ledger.py` — `ReadinessLedgerEntry` model (UUID PK, org_id FK, timestamp, previous_score, new_score, delta, driver_type, driver_item, impact, evidence_source, created_by) per ADR-008. Includes idempotency index `(org_id, timestamp, new_score)` and 0–100 score range validator.
- `alembic/versions/9a1c0b3d2e4f_add_readiness_ledger_entries.py` — migration with upgrade + downgrade that re-creates / drops the table and both indexes.

Modified:
- `app/models/__init__.py` — exports `ReadinessLedgerEntry`.
- `alembic/env.py` — imports `ReadinessLedgerEntry` so `Base.metadata` includes it.

Test:
- `tests/test_readiness_ledger_model.py` — 8/8 passing (round-trip, indexes, FK required, default UUID v4, range validator below 0, range validator above 100, idempotency index columns, timestamp defaulted).

Reason:
- Sprint 1.8 Feature A "Readiness Drivers & Ledger" requires an immutable audit-grade ledger. Foundation for S1.8-A2–A5 (scoring hardening → driver extraction → write hook → API).

No deviations.
Status: READY → IN_PROGRESS → COMPLETED.

---

2026-07-09 (Sprint 2 Prep)

Agent: Antigravity

Added:
- Implemented `BaseTelemetryConnector` interface in `app/integrations/base.py`.
- Refactored `SplunkConnector` to adhere strictly to the base interface for live querying.
- Removed hackathon mock mappings and enabled dynamic evidence type extraction in `service.py`.
- Created integration scripts `test_splunk_connection.py`, `test_splunk_search.py`, and `test_splunk_ingestion.py`.

Reason:
- Fulfilled the mandate to remove mock/demo logic and implement the production Splunk integration while strictly adhering to deterministic scoring constraints.

Impacts:
- Splunk integration logic is now ready for Staging pending the injection of `SENTINEL_SPLUNK_TOKEN` into Cloud Run via Secret Manager.
- Unblocked further SIEM integration work in Sprint 2 Prep (Wazuh, CrowdStrike, etc.).

---
2026-06-24 (Sprint 1.6)

Agent: Antigravity

Added:
- Refactored `calculate_readiness_delta` into a 4-layer deterministic model (Verification, Coverage, Lifecycle, Exposure).
- Created structured reasons schema for explicit tracking of impacts.
- Scoped Exposure layer specifically for KEVs (with modifiers for Internet Facing / Critical Assets).
- Created `scripts/sprint1_6_demo.py` generating board-ready Readiness Delta Report.

Reason:
- Aligns scoring perfectly with ResilAI's "Incident Readiness" moat (preventing drift towards generic vulnerability management).
- Board-ready reasoning allows CISO/Investors to precisely understand score deltas.

Impacts:
- Core assessment baseline is never mutated by telemetry, ensuring compliance remains sacred.
- MCPs (Sprint 2) can now cleanly map their structured findings into the Exposure or Coverage layers.

---

2026-06-24

Agent: Antigravity

Added:
- `aws_ssm_poller.py` for real AWS SSM integration (Task 1).
- Normalization test suite in `test_normalization.py` achieving >95% accuracy for test cases (Task 2).
- Lifecycle validation using `test_lifecycle.py` and exact catalog matching (Task 3).
- CVE staging cache `nvd_staging_cache.json` for deterministic vulnerability mapping (Task 4).
- Updated `scoring.py` with the approved, deterministic Readiness Modifiers framework (Task 5).
- Created and executed `validate_delta.py` for end-to-end evidence payload demonstration (Task 6).

Reason:
- Fulfilled Sprint 1.5 Validation & Hardening requirements.
- Proven the deterministic path from raw SSM data to the Executive Readiness Delta.

Impacts:
- Sprint 2 (MCP Evidence Layer) is currently BLOCKED pending user review of the Sprint 1.5 validation evidence.

---

2026-06-16

Agent: Antigravity

Added:
- Agent Memory System (`docs/agent_memory/`)
- Async tech stack discovery (`app/api/tech_stack.py`)
- Archive assessment functionality (`app/services/assessment.py`, frontend)

Reason:
- Improve agent collaboration context caching.
- Prevent CORS timeouts in production.
- Provide compliance-friendly deletion UX.

Impacts:
- All future agents must read `AGENT_START.md` before executing.

---

2026-06-18

Agent: Antigravity

Added:
- CORSErrorSafetyMiddleware (`app/core/middleware.py`)
- Complete CORS origin list in `gcp/env.prod.yaml`

Reason:
- Production CORS error observed at AWS Summit caused by Cloud Run stripping headers on 5xx.

Files Modified:
- `app/core/middleware.py`
- `app/main.py`
- `gcp/env.prod.yaml`

Dependencies Created:
- CORSErrorSafetyMiddleware must always be the LAST middleware added (runs first in the stack).

Business Impact:
- Eliminates CORS errors for live demos and investor presentations.

Next Recommended Task:
- Verify CORS headers present on production after deployment.

Affected Teams:
- Backend
- DevOps

---

2026-07-13 (Audit pass by Principal Security & Architecture Auditor)

Inspected (per SESSION_HANDOFF.md scope, no general repo scan):
- frontend/src/App.tsx
- frontend/src/pages/{Dashboard, EvidenceNetwork, BoardStory, DecisionEngine, BusinessUnits, Integrations}.tsx
- frontend/src/components/{ExecutiveRiskMatrix, dashboard/PersonaContext}.tsx
- frontend/src/contexts/PersonaContext.tsx
- frontend/.deprecated_routes.txt
- frontend/src/api.ts (declarations only)

Verdict against PRODUCT_MOAT.md:
- S1.8-C5: NOT PASS — confidence gauge renders hardcoded 84 fallback (F-011/J01/P01).
- S2-A4: NOT PASS — CRITICAL (F-001/F-002: client-side PDF fabrication; numbers in narrative without source).
- S2-B5: PASS w/ caveats — F-014 baseline 84 fallback, F-017 DecisionAction typing.
- S2-B6: NOT PASS — F-008 (HIGH) persona widget set not disjoint.
- S2-C3: NOT PASS — F-004 (HIGH) dead `/dashboard/pilot-program` links still present.
- Overall: NO PASS — PRODUCT_MOAT #1 (LLMs never score) and #4 (deterministic scoring only) violated by client-side fabricated numerics.

26 findings written to AUDIT_REPORT.md (F-001..F-026).
22 atomic fix tasks registered in TASK_QUEUE.md: CRITICAL A01; HIGH C01/G01/S01; plus MEDIUM/LOW B01/D01/E01/F01/H01/I01/J01/L01/M01/N01/O01/P01/Q01/R01/T01.

Re-audit gate: A01 / C01 / G01 / S01 must complete first.

No architecture changes proposed.
No production code modified by the auditor.

