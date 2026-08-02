# ResilAI Task Queue

> This file is the single source of truth for execution status across the ResilAI builder pipeline. Builder agents pick the next READY task; no planning required.
> Status values: `READY` · `BLOCKED` · `IN_PROGRESS` · `COMPLETED` · `FAILED`
> Owners: `Backend` (Core) · `BackendIntel` (Intelligence) · `BackendEvidence` (Verification) · `Frontend` · `DevOps`
> Source: Sprint 1.8 + Sprint 2 execution plan produced by GLM 5.2 (Principal Execution Planner).

---

## Sprint 1.8 — Trust & Verification Hardening

### Telemetry Pipeline Consolidation (cutover 2026-07-15)

| Task | Status | Summary |
|------|--------|---------|
| `SP1.8-T1-SPL-CONNECTOR` | COMPLETED 2026-07-15 | `app/connectors/splunk.py::SplunkConnector` (@register_connector, MCP-only) created. |
| `SP1.8-T1-SPL-SVC-ROUTING` | COMPLETED 2026-07-15 | `app/services/splunk.py::SplunkService` now delegates `_run_search` to `SplunkMCPClient`. Public surface preserved. |
| `SP1.8-T1-REG-ORCH-INGEST` | COMPLETED 2026-07-15 | `ConnectorManager._ingest_events` calls `EvidenceOrchestrator.ingest_collection_result` + registers Splunk/Wazuh `EvidenceAdapter` on first sync. |
| `SP1.8-T1-INT-SENTDEL` | COMPLETED 2026-07-15 | Deleted `app/integrations/sentinel_splunk/` (third Splunk intent) + orphan `app/api/routes/sentinel_test.py` + junk `app/api/import urllib.py` + 4 dead hackathon scripts. |
| `SP1.8-T1-API-EVIDENCE` | COMPLETED 2026-07-15 | `pull_splunk_evidence` rewritten without inline mocks. `configure_splunk_hec` persists canonical {mcp_url,api_key} blob. v1 `/splunk/*` routes refactored to read Connector rows. |
| `SP1.8-T1-INIT-EXPORT` | COMPLETED 2026-07-15 | `app/services/evidence/__init__.py` re-exports ABC + registry symbols; `tests/test_evidence_adapter_base.py` now passes. |
| `SP1.8-T1-CONF-RESP` | COMPLETED 2026-07-15 | `OrgConfidenceResponse.details` renamed to `.connectors`; `tests/test_connectors_confidence_api.py` now passes. |
| `SP1.8-T1-STAGING-ENV` | COMPLETED 2026-07-15 | `gcp/env.staging.yaml` extended with `SPLUNK_MCP_URL` and `SPLUNK_MCP_API_KEY`. |

---

### Sprint Tasks (Existing - see below for full detail)

### Phase A — Readiness Drivers & Readiness Ledger (Feature A)

---

#### TASK S1.8-A1
- **Title:** ReadinessLedgerEntry model + Alembic migration
- **Status:** COMPLETED
- **Owner:** Backend
- **Completed at:** 2026-07-12 — 8/8 unit tests passing; migration `9a1c0b3d2e4f` adds `readiness_ledger_entries` table with idempotency index `(org_id, timestamp, new_score)`.
- **Epic:** A — Readiness Drivers & Ledger
- **Complexity:** Medium
- **Files:**
  - Create: `app/models/readiness_ledger.py`
  - Create: `alembic/versions/<rev>_readiness_ledger_entry.py`
  - Modify: `app/models/__init__.py`
- **Models:** `ReadinessLedgerEntry` (UUID, org_id, timestamp, previous_score, new_score, delta, driver_type, driver_item, impact, evidence_source, created_by)
- **APIs:** none
- **Dependencies:** none
- **Acceptance:**
  - Migration runs clean up and down on staging.
  - Insert/select round-trips via SQLAlchemy 2.0.
  - UPDATE raises at ORM layer (write-once enforcement).
- **Unit tests:** `tests/test_readiness_ledger_model.py`
- **Integration tests:** none
- **Risks:** Migration failure on existing staging rows.
- **Rollback:** `alembic downgrade -1`; drop new table.
- **Deliverables:** Schema + migration.

---

#### TASK S1.8-A2
- **Title:** Lock `calculate_readiness_delta()` as single source of score-delta computation
- **Status:** COMPLETED
- **Owner:** Backend
- **Completed at:** 2026-07-12 — added module-level ADR-007 isolation guard + `calculate_readiness_delta()` contract documentation. 8/8 unit tests passing. Function signature frozen; no LLM imports detected by AST scan. Implementation is purely additive (no behavioral change to existing scoring).
- **Epic:** A
- **Complexity:** Medium
- **Files:**
  - Modify: `app/services/scoring.py`
- **APIs:** none
- **Dependencies:** S1.8-A1
- **Acceptance:**
  - Returns previous/new/delta/impact breakdown.
  - No imports from `ai_narrative.py`, `intelligence.py`, `narrative/*`, `llm_narrative.py`, `google.genai`.
- **Unit tests:** `tests/test_calculate_delta.py`
- **Integration tests:** trigger scoring twice; assert delta matches.
- **Risks:** Hidden indirect LLM imports.
- **Rollback:** Restore prior pure scoring.
- **Deliverables:** Hardened scoring contract.

---

#### TASK S1.8-A3
- **Title:** Readiness Driver extraction module
- **Status:** COMPLETED
- **Owner:** Backend
- **Completed at:** 2026-07-12 — `app/services/readiness_drivers.py` created. `extract_drivers()` returns sorted top-5 positive/negative drivers. `extract_action_items()` renders executive-monday-morning list. Read-only consumer of scoring per ADR-007. 8/8 unit tests passing.
- **Epic:** A
- **Complexity:** Small
- **Files:**
  - Create: `app/services/readiness_drivers.py`
- **APIs:** none (service layer)
- **Dependencies:** S1.8-A2
- **Acceptance:**
  - Returns sorted top-5 positive and top-5 negative drivers `{driver_type, driver_item, impact, evidence_source}`.
  - No DB writes, no LLM. Read-only import of `scoring.py`.
- **Unit tests:** `tests/test_readiness_drivers.py`
- **Integration tests:** none
- **Risks:** Drift from scoring semantics.
- **Rollback:** Remove module; endpoints return 503.
- **Deliverables:** Driver extraction service.

---

#### TASK S1.8-A4
- **Title:** Readiness Ledger write hook (idempotent)
- **Status:** COMPLETED
- **Owner:** Backend
- **Completed at:** 2026-07-12 — `app/services/readiness_ledger.py` created. `record_score_change()` provides idempotent insert on `(org_id, timestamp, new_score)`. `attach_to_scoring()` wraps `calculate_readiness_delta` so a single call both scores and writes a ledger row. `score_and_record()` is the convenience entrypoint. 7/7 tests passing. No edits to scoring.py itself (deterministic contract preserved per ADR-007).
- **Epic:** A
- **Complexity:** Medium
- **Files:**
  - Create: `app/services/readiness_ledger.py`
  - Modify: `app/services/scoring.py` (invocation point)
- **Acceptance:**
  - Every recalculation produces exactly one ledger row.
  - Replay of same `(org_id, timestamp, new_score)` no-ops (idempotency key).
- **Unit tests:** `tests/test_ledger_write_hook.py`
- **Integration tests:** scoring + ledger; verify row count == recalc count.
- **Risks:** High write volume on Firestore.
- **Rollback:** Remove write hook; scoring operates degraded without ledger.
- **Deliverables:** Ledger write hook + idempotency.

---

#### TASK S1.8-A5
- **Title:** Readiness API surface — 4 endpoints
- **Status:** COMPLETED
- **Owner:** Backend
- **Completed at:** 2026-07-12 — `app/api/v1/readiness.py` + `app/schemas/readiness.py` + router registration. Endpoints: `/readiness/drivers`, `/readiness/actions`, `/readiness/ledger`, `/readiness/timeline`. 11/11 tests passing; 200/404/422 status codes verified. Drivers + actions endpoints are read-only consumers of `calculate_readiness_delta()` (ADR-007). Ledger + timeline endpoints read the immutable `ReadinessLedgerEntry` table (ADR-008).
- **Epic:** A
- **Complexity:** Medium
- **Files:**
  - Create: `app/api/v1/readiness.py`
  - Create: `app/schemas/readiness.py`
  - Modify: `app/api/v1/__init__.py` (register router)
- **APIs:**
  - `GET /api/v1/readiness/drivers?org_id=`
  - `GET /api/v1/readiness/actions?org_id=`
  - `GET /api/v1/readiness/ledger?org_id=`
  - `GET /api/v1/readiness/timeline?org_id=`
- **Acceptance:**
  - 200 with documented shape; 404 unknown org; 422 missing org_id.
- **Unit tests:** `tests/test_readiness_api.py`
- **Integration tests:** mount router; hit staging endpoint.
- **Risks:** Async I/O blocking request.
- **Rollback:** Unregister router; endpoints 404.
- **Deliverables:** 4 endpoints + schemas + router wiring.

---

#### TASK S1.8-A6
- **Title:** Frontend — Readiness Drivers widget + SlideOver (Dashboard refactor)
- **Status:** COMPLETED
- **Owner:** Frontend
- **Epic:** A
- **Complexity:** Large
- **Files:**
  - Modify: `frontend/src/pages/Dashboard.tsx`
  - Create: `frontend/src/components/dashboard/ReadinessDrivers.tsx`
  - Create: `frontend/src/components/common/SlideOver.tsx`
  - Modify: `frontend/src/api.ts`
- **Acceptance:**
  - Dashboard widgets extracted to separate components.
  - SlideOver displays driver detail including `evidence_source`.
  - No client-side scoring logic.
- **Unit tests:** component tests (per existing frontend setup)
- **Integration tests:** load Dashboard with stubbed APIs; top-5 positive + top-5 negative render.
- **Risks:** Dashboard regression from refactor.
- **Rollback:** Revert `Dashboard.tsx` to previous revision.
- **Deliverables:** Refactored Dashboard + 2 new components.

---

### Phase B — Technology Intelligence + AI Estate (Feature B)

---

#### TASK S1.8-B1
- **Title:** GlobalSoftwareCatalog EOL strict normalization
- **Status:** COMPLETED
- **Owner:** BackendIntel
- **Completed at:** 2026-07-12 — added `resolve_eol_status()` in `app/services/lifecycle/normalization.py`. Strict major.minor lookup; unmapped entries return `end_of_life: "unknown"` (never True/False). All 15 tests passing (5 normalization-engine + 10 EOL-resolution).
- **Epic:** B
- **Complexity:** Medium
- **Files:**
  - Modify: `app/services/lifecycle/normalization.py`
  - Modify: `app/models/software_catalog.py`
  - Modify: `app/models/lifecycle_catalog.py`
- **Dependencies:** none
- **Acceptance:**
  - Normalized version not matching an entry returns `end_of_life: unknown`, not `true`.
  - EOL flag set only on exact major.minor match.
- **Unit tests:** `tests/test_normalization_eol.py`
- **Integration tests:** round trip with seed `lifecycle_catalog`.
- **Risks:** Mismatches leaking as false EOL positives.
- **Rollback:** Restore prior loose matcher.
- **Deliverables:** Hardened normalization.

---

#### TASK S1.8-B2
- **Title:** Technology Intelligence orchestrator
- **Status:** COMPLETED
- **Owner:** BackendIntel
- **Completed at:** 2026-07-13 — `app/services/technology_intelligence.py` orchestrator created, applying CVE enrichments to TechStackItem instances to annotate readiness impact. Tests pass in `tests/test_technology_intelligence.py`.
- **Epic:** B
- **Complexity:** Medium
- **Files:**
  - Create: `app/services/technology_intelligence.py`
  - Reuse: `app/services/discovery/orchestrator.py`, `app/services/cve/cve_enrichment.py`
- **Acceptance:**
  - Returns items with `readiness_impact` annotation; EOL/KEV pass-through.
  - Pure orchestration, no new business rules.
- **Unit tests:** `tests/test_technology_intelligence.py`
- **Risks:** Orchestrator recycling stale discovery data.
- **Rollback:** Drop module; UI falls back to flat TechStack.
- **Deliverables:** Orchestrator service.

---

#### TASK S1.8-B3
- **Title:** AI finding rules AI-001..AI-010
- **Status:** COMPLETED
- **Owner:** BackendIntel
- **Completed at:** 2026-07-12 — 10 AI-Governance rules (AI-001..AI-010) added to `app/services/findings.py`. Standalone `evaluate_ai_governance_findings()` does the deterministic classification against an inventory. No LLM. 18/18 tests passing.
- **Epic:** B
- **Complexity:** Small
- **Files:**
  - Modify: `app/services/findings.py`
- **Acceptance:**
  - 10 deterministic rules, each emits `{rule_id, severity, remediation}`.
  - None invoke an LLM.
- **Unit tests:** `tests/test_ai_findings.py`
- **Risks:** Rules drifting into scoring territory.
- **Rollback:** Remove rules AI-001..AI-010; prior findings unaffected.
- **Deliverables:** 10 deterministic finding rules.

---

#### TASK S1.8-B4
- **Title:** AI frameworks coverage calculator (NIST AI RMF + MITRE ATLAS)
- **Status:** COMPLETED
- **Owner:** BackendIntel
- **Completed at:** 2026-07-13 — `app/services/ai_frameworks.py` implemented. `calculate_ai_framework_coverage()` accurately retrieves unique mapped controls via `FrameworkMappingRegistry` joining to `Assessment` per `org_id`. Tests (2/2) passing in `tests/test_ai_frameworks_coverage.py`.
- **Epic:** B
- **Complexity:** Medium
- **Files:**
  - Create: `app/services/ai_frameworks.py`
  - Reuse: `app/models/framework_registry.py`, `app/models/framework_mapping.py`
- **Acceptance:**
  - Returns 0–100 coverage per framework, deterministic, no LLM.
- **Unit tests:** `tests/test_ai_frameworks_coverage.py`
- **Risks:** Framework mapping staleness.
- **Rollback:** Disable module; endpoint returns 503.
- **Deliverables:** Coverage calculator.

---

#### TASK S1.8-B5
- **Title:** AiAsset enum expansion (Vector DBs, MCP Servers, Agent Frameworks)
- **Status:** COMPLETED
- **Owner:** BackendIntel
- **Completed at:** 2026-07-12 — `AIAssetType` enum expanded with `mcp_server`, `mcp_client`, `agent_framework`, `embedding_pipeline`, `rag_corpus`, `training_dataset`, `evaluation_pipeline`, `prompt_library`. Migration `c4e8f3a91b50` (no-op on SQLite; ALTER on Postgres). 18/18 tests passing.
- **Epic:** B
- **Complexity:** Small
- **Files:**
  - Modify: `app/models/ai_asset.py`
  - Create: Alembic migration for enum type if needed
- **Acceptance:**
  - New enum values persist and round-trip.
  - Migration up/down clean.
- **Unit tests:** `tests/test_ai_asset_enum.py`
- **Risks:** Enum migration failing on staged-in rows.
- **Rollback:** `alembic downgrade -1`.
- **Deliverables:** Expanded enum + migration.

---

#### TASK S1.8-B6
- **Title:** Technology Intelligence API surface — 4 endpoints
- **Status:** COMPLETED
- **Owner:** BackendIntel
- **Completed at:** 2026-07-13 — Added `GET /api/v1/technology/inventory`, `lifecycle`, `exposure` in `app/api/v1/technology.py` and `GET /api/v1/frameworks/coverage` in `app/api/v1/frameworks.py`. Tests passing.
- **Epic:** B
- **Complexity:** Medium
- **Files:**
  - Create: `app/api/v1/technology.py`
  - Extend: `app/api/v1/frameworks.py`
  - Modify: `app/api/v1/__init__.py`
  - Create: `app/schemas/technology.py`
- **APIs:**
  - `GET /api/v1/technology/inventory`
  - `GET /api/v1/technology/lifecycle`
  - `GET /api/v1/technology/exposure`
  - `GET /api/v1/frameworks/coverage`
- **Acceptance:** documented shape; 422 on missing fields; 404 unknown org.
- **Unit tests:** `tests/test_technology_api.py`
- **Integration tests:** mount router; hit staging.
- **Risks:** Router mounting order with existing v1 routers.
- **Rollback:** Unregister router.
- **Deliverables:** 4 endpoints.

---

#### TASK S1.8-B7
- **Title:** Frontend — `TechnologyIntelligence.tsx` + AI Estate (6 tabs)
- **Status:** COMPLETED
- **Owner:** Frontend
- **Epic:** B
- **Complexity:** Large
- **Files:**
  - Replace: `frontend/src/pages/TechStack.tsx` → `frontend/src/pages/TechnologyIntelligence.tsx`
  - Modify: `frontend/src/App.tsx` (route)
  - Create: `frontend/src/components/technology/*.tsx` (6 tab components)
  - Modify: `frontend/src/api.ts`
- **Acceptance:**
  - 6 tabs (Inventory, Lifecycle, Exposure, Dependencies, Timeline, Insights) render with stubbed data.
  - Each item card surfaces readiness impact.
- **Unit tests:** component tests per tab.
- **Integration tests:** E2E navigate 6 tabs.
- **Risks:** Tab state collision.
- **Rollback:** Restore `TechStack.tsx` + route.
- **Deliverables:** New page + 6 tab components.

---

### Phase C — Evidence Network & Evidence Confidence (Feature C)

---

#### TASK S1.8-C1
- **Title:** `EvidenceAdapter` ABC + `EvidenceRegistry`
- **Status:** COMPLETED
- **Owner:** BackendEvidence
- **Completed at:** 2026-07-13 — `app/services/evidence/__init__.py`, `base_adapter.py`, `registry.py` verified. 16/16 unit tests passing.
- **Epic:** C
- **Complexity:** Medium
- **Files:**
  - Create: `app/services/evidence/__init__.py`
  - Create: `app/services/evidence/base_adapter.py`
  - Create: `app/services/evidence/registry.py`
- **Acceptance:**
  - `EvidenceAdapter` defines `fetch_evidence()`, `normalize()`, `health()`.
  - Registry resolves adapter by connector name; no vendor imports in base.
- **Unit tests:** `tests/test_evidence_adapter_base.py`
- **Risks:** Vendor lock-in leaking into base.
- **Rollback:** Remove package; evidence path falls back to existing Splunk direct hook.
- **Deliverables:** Adapter pattern + registry scaffold.

---

#### TASK S1.8-C2
- **Title:** Splunk + Wazuh adapter implementations
- **Status:** COMPLETED
- **Owner:** BackendEvidence
- **Completed at:** 2026-07-13 — `splunk.py`, `wazuh.py` adapters created. Both passed conformance and logic tests. 8/8 tests passing.
- **Epic:** C
- **Complexity:** Medium
- **Files:**
  - Create: `app/services/evidence/adapters/splunk.py`
  - Create: `app/services/evidence/adapters/wazuh.py`
  - Reuse: `app/services/splunk.py`, `app/services/wazuh_client.py`
- **Acceptance:**
  - Both adapters pass ABC conformance.
  - Existing Splunk behavior unchanged; Wazuh adapter reads via `wazuh_client.py`.
- **Unit tests:** `tests/test_splunk_adapter.py`, `tests/test_wazuh_adapter.py`
- **Integration tests:** adapter produces evidence accepted by `app/services/verification.py`.
- **Risks:** Per-vendor failures breaking the registry.
- **Rollback:** Registry returns 503 for failing adapter.
- **Deliverables:** 2 production adapters.

---

#### TASK S1.8-C3
- **Title:** Evidence Confidence engine (Freshness × Uptime × Success Rate × Completeness)
- **Status:** COMPLETED
- **Owner:** BackendEvidence
- **Completed at:** 2026-07-13 — `evidence_confidence.py` created and 6/6 tests passing for deterministic scoring logic.
- **Epic:** C
- **Complexity:** Small
- **Files:**
  - Create: `app/services/evidence_confidence.py`
- **Acceptance:**
  - Returns deterministic 0–100; each factor documented; no LLM.
- **Unit tests:** `tests/test_evidence_confidence.py`
- **Risks:** Weighting drift.
- **Rollback:** Disable metric; endpoint returns 503.
- **Deliverables:** Confidence engine.

---

#### TASK S1.8-C4
- **Title:** `GET /api/v1/connectors/confidence` (no schema changes)
- **Status:** COMPLETED
- **Owner:** BackendEvidence
- **Epic:** C
- **Complexity:** Small
- **Files:**
  - Extend: `app/api/v1/connectors.py`
  - Create: `app/schemas/evidence.py`
- **Acceptance:**
  - Returns per-connector confidence + org-level aggregate, 0–100; 422 missing org_id.
- **Unit tests:** `tests/test_connectors_confidence_api.py`
- **Integration tests:** mount router; hit staging with mocked adapter.
- **Risks:** Real third-party rate limits dropping score.
- **Rollback:** Endpoint returns 503.
- **Deliverables:** Connector confidence endpoint.

---

#### TASK S1.8-C5
- **Title:** Frontend — `EvidenceNetwork.tsx` + Dashboard Evidence Confidence gauge
- **Status:** COMPLETED
- **Owner:** Frontend
- **Epic:** C
- **Complexity:** Large
- **Files:**
  - Create: `frontend/src/pages/EvidenceNetwork.tsx`
  - Replace/redirect: `frontend/src/pages/Integrations.tsx`
  - Create: `frontend/src/components/evidence/*.tsx`
  - Modify: `frontend/src/pages/Dashboard.tsx`
  - Modify: `frontend/src/App.tsx`
  - Modify: `frontend/src/api.ts`
- **Acceptance:**
  - Integrations route redirects to EvidenceNetwork.
  - Confidence metric renders in Dashboard header.
  - Adapter substitution demo (Splunk ↔ mock SentinelOne) requires no UI change.
- **Unit tests:** component tests for cards + gauge.
- **Integration tests:** E2E simulate stale adapter; assert gauge drops.
- **Risks:** Diagram rendering perf.
- **Rollback:** Restore `Integrations.tsx` route.
- **Deliverables:** New EvidenceNetwork page + Dashboard header metric.

---

## Sprint 2 — Executive Intelligence & Anti-Hallucination Hardening

### Phase A — Board Story Narrative Layer

---

#### TASK S2-A1
- **Title:** Refactor `ai_narrative.py` to emit 10 structured sections
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** D — Board Story
- **Complexity:** Medium
- **Files:**
  - Modify: `app/services/ai_narrative.py`
  - Modify: `app/services/narrative/executive_narrative.py`
  - Create: `app/schemas/board_story.py`
- **Acceptance:**
  - Output has exactly 10 sections in canonical order; section IDs fixed by code, not LLM.
  - LLM only fills prose per section; no scoring in this module.
- **Unit tests:** `tests/test_board_story_schema.py`
- **Risks:** LLM attempting to redefine section set.
- **Rollback:** Revert to free-form emitter; UI shows legacy narrative.
- **Deliverables:** Board Story service + schema.

---

#### TASK S2-A2
- **Title:** Gemini prompt hardening (anti-hallucination numeric-trace validator)
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** D
- **Complexity:** Medium
- **Files:**
  - Modify: `app/services/ai_narrative.py`
  - Modify: `app/services/narrative/llm_client.py`
- **Acceptance:**
  - Any numeric in narrative must trace back to source scoring snapshot.
  - Validation failure triggers deterministic fallback prose, not blank.
- **Unit tests:** `tests/test_narrative_anti_hallucination.py`
- **Risks:** Over-rejection causing empty board stories.
- **Rollback:** Fallback prose generator (deterministic) kicks in.
- **Deliverables:** Hardened prompt + validator.

---

#### TASK S2-A3
- **Title:** `GET /api/v1/reports/board-story?org_id=`
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** D
- **Complexity:** Small
- **Files:**
  - Extend: `app/api/v1/reports.py` (or new `app/api/v1/board_story.py`)
  - Modify: `app/api/v1/__init__.py`
- **Acceptance:** 200 with 10-section body; 404 unknown org; 422 missing org_id.
- **Unit tests:** `tests/test_board_story_api.py`
- **Integration tests:** Mount router; hit staging with stubbed Gemini.
- **Risks:** Gemini rate limits.
- **Rollback:** Endpoint returns cached last-known-good narrative, marked stale.
- **Deliverables:** Board Story endpoint.

---

#### TASK S2-A4
- **Title:** Frontend — `BoardStory.tsx` (multi-section structured view)
- **Status:** COMPLETED
- **Owner:** Frontend
- **Epic:** D
- **Complexity:** Medium
- **Files:**
  - Create: `frontend/src/pages/BoardStory.tsx`
  - Modify: `frontend/src/App.tsx`
  - Modify: `frontend/src/api.ts`
- **Acceptance:**
  - All 10 sections render with section-aware scroll.
  - Missing section shows structured fallback copy.
  - No client-side scoring math.
- **Unit tests:** component tests.
- **Integration tests:** E2E load a board story; section persist across navigation.
- **Risks:** Large narrative causing scroll perf.
- **Rollback:** Hide BoardStory route.
- **Deliverables:** Board Story page.

---

### Phase B — Executive Decision Engine

---

#### TASK S2-B1
- **Title:** Decision Engine "what-if" projection model (delegates to scoring)
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** D — Decision Engine
- **Complexity:** Large
- **Files:**
  - Create: `app/services/decision_engine.py`
  - Read-only: `app/services/scoring.py`
- **Acceptance:**
  - `project_readiness()` returns deterministic projected score.
  - MUST equal post-state actual score (anti-drift AC).
- **Unit tests:** `tests/test_decision_project.py` (20 fixtures)
- **Integration tests:** apply action to staging DB; compare projection to actual scoring.
- **Risks:** Logic duplication causing silent drift.
- **Rollback:** Disable endpoint; projection unavailable.
- **Deliverables:** Decision Engine.

---

#### TASK S2-B2
- **Title:** `GET /api/v1/decisions/recommended-actions`
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** D
- **Complexity:** Small
- **Files:**
  - Create: `app/api/v1/decisions.py`
  - Create: `app/schemas/decision.py`
  - Modify: `app/api/v1/__init__.py`
- **Acceptance:** Ordered actions with `projected_delta` per action; no LLM.
- **Unit tests:** `tests/test_recommended_actions_api.py`
- **Risks:** Recommending action whose projection ≠ actual.
- **Rollback:** Disable endpoint; UI shows no recommendations.
- **Deliverables:** Recommended actions endpoint.

---

#### TASK S2-B3
- **Title:** `POST /api/v1/decisions/project`
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** D
- **Complexity:** Small
- **Files:**
  - Extend: `app/api/v1/decisions.py`
  - Extend: `app/schemas/decision.py`
- **Acceptance:**
  - 200 with per-action projected breakdown.
  - 413/422 on malformed or oversized payload (cap 50 actions).
- **Unit tests:** `tests/test_decisions_project_api.py`
- **Integration tests:** apply projected actions; assert actual delta == projection.
- **Risks:** Payload-size DoS.
- **Rollback:** Cap input to 50 actions; 413 above.
- **Deliverables:** Decision project endpoint.

---

#### TASK S2-B4
- **Title:** Organization model — add `is_clone` + `source_org_id` (Sprint 2.5 prep, schema-only)
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** D
- **Complexity:** Small
- **Files:**
  - Modify: `app/models/organization.py`
  - Create: Alembic migration
- **Acceptance:**
  - Fields present, nullable correctly; migration up/down clean.
  - Existing rows default to `is_clone=false`, `source_org_id=null`.
- **Unit tests:** `tests/test_org_clone_fields.py`
- **Risks:** Migration failure on existing orgs.
- **Rollback:** `alembic downgrade -1`.
- **Deliverables:** Org clone fields + migration.

---

#### TASK S2-B5
- **Title:** Frontend — `DecisionEngine.tsx` (toggle actions → projected score)
- **Status:** COMPLETED
- **Owner:** Frontend
- **Epic:** D
- **Complexity:** Medium
- **Files:**
  - Create: `frontend/src/pages/DecisionEngine.tsx`
  - Modify: `frontend/src/App.tsx`
  - Modify: `frontend/src/api.ts`
- **Acceptance:**
  - Toggle action → debounced re-fetch to `/decisions/project` → updated projection.
  - No client-side scoring math.
- **Unit tests:** component tests.
- **Integration tests:** E2E click "Patch PostgreSQL"; assert projected score step.
- **Risks:** Projection latency causing UI lag.
- **Rollback:** Hide DecisionEngine route.
- **Deliverables:** Decision Engine page.

---

#### TASK S2-B6
- **Title:** Frontend — Organization Heatmap + persona-based widget visibility
- **Status:** COMPLETED
- **Owner:** Frontend
- **Epic:** D
- **Complexity:** Medium
- **Files:**
  - Extend/Create: `frontend/src/pages/BusinessUnits.tsx`
  - Create: `frontend/src/components/dashboard/PersonaContext.tsx`
  - Modify: `frontend/src/pages/Dashboard.tsx` (consumer)
- **Acceptance:**
  - Heatmap colors driven by deterministic readiness data.
  - Persona context filters visible widgets; default = "Executive" (all).
  - No client-side scoring.
- **Unit tests:** component tests (persona A vs B disjoint).
- **Risks:** Persona misconfiguration hiding critical widgets.
- **Rollback:** Default persona shows all widgets.
- **Deliverables:** Heatmap + persona context.

---

### Phase C — Verification Sweep & Acceptance Hardening

---

#### TASK S2-C1
- **Title:** `tests/test_decision_drift_guard.py` — regression test across ≥20 fixtures
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** Sweep
- **Complexity:** Medium
- **Files:**
  - Create: `tests/test_decision_drift_guard.py`
- **Acceptance:**
  - For each fixture set: apply actions to DB → real scoring → `project_readiness()` → exact equality. Drift blocks merge.
- **Unit tests:** (IS the test)
- **Integration tests:** Yes.
- **Risks:** Insufficient fixtures → false pass.
- **Rollback:** CI failure forces investigation; deploy blocked.
- **Deliverables:** Regression guard.

---

#### TASK S2-C2
- **Title:** `tests/test_llm_isolation.py` — bytecode import guard
- **Status:** COMPLETED
- **Owner:** Backend
- **Epic:** Sweep
- **Complexity:** Small
- **Files:**
  - Create: `tests/test_llm_isolation.py`
- **Acceptance:**
  - Scans `scoring.py`, `decision_engine.py`, `readiness_drivers.py`, `evidence_confidence.py`, `ai_frameworks.py`.
  - Any import from `ai_narrative.py`, `intelligence.py`, `narrative/*`, `llm_narrative.py`, `google.genai` fails CI.
- **Unit tests:** (IS the test)
- **Risks:** New narrative module added without updating guard list.
- **Rollback:** Extend guard list via PR review.
- **Deliverables:** Permanent anti-hallucination guard.

---

#### TASK S2-C3
- **Title:** Orphaned route removal (`SentinelDashboard.tsx`, `PilotDashboard.tsx`)
- **Status:** COMPLETED
- **Owner:** Frontend
- **Epic:** Sweep
- **Complexity:** Small
- **Files:**
  - Modify: `frontend/src/App.tsx`
  - Backup: removed route configs (`.deprecated_routes.txt` for rollback)
- **Acceptance:**
  - Removed routes 404; remaining routes unaffected.
  - Backups of route configs preserved.
- **Unit tests:** component tests for removed paths.
- **Integration tests:** E2E navigate remaining routes; no dead links.
- **Risks:** Breaking a still-used route.
- **Rollback:** Restore route config backup.
- **Deliverables:** Dead-route cleanup.

---

#### TASK S2-C4
- **Title:** Staging build-and-deploy validation (backend + frontend)
- **Status:** BLOCKED — depends on ALL backend tasks above
- **Owner:** DevOps
- **Epic:** Sweep
- **Complexity:** Medium
- **Files:**
  - Modify: `gcp/`, `scripts/` (deploy scripts)
  - Modify: `firebase.json` (staging target)
- **Acceptance:**
  - Backend deployed to `airs-api-staging`.
  - Frontend deployed via `firebase deploy --only hosting:staging`.
  - All endpoints return documented status codes; all frontend routes load.
  - Smoke report produced.
- **Unit tests:** none
- **Integration tests:** full staging smoke — every new endpoint + every new page.
- **Risks:** Cloud Run staging mis-config.
- **Rollback:** Revert deploy to previous revision.
- **Deliverables:** Staging validation report.

---

---
## Audit-Generated Fix Tasks (per `docs/agent_memory/AUDIT_REPORT.md`)

> These tasks were produced by the Principal Security & Architecture Auditor on 2026-07-13 against the SESSION_HANDOFF milestones. Required before re-audit pass; NONE of S1.8-C5 / S2-A4 / S2-B5 / S2-B6 / S2-C3 currently passes PRODUCT_MOAT compliance.

#### TASK S1.8-AUDIT-FIX-A01
- **Title:** Move PDF generation server-side under `/api/v1/reports/board-story.pdf` (replaces client-built PDFs in F-001/F-002)
- **Status:** IN_PROGRESS
- **Owner:** Backend + Frontend
- **Tags:** CRITICAL · PRODUCT_MOAT #1 #4 violation
- **Files:**
  - New: `app/api/v1/reports.py` endpoint (PDF byte stream)
  - Modify: `frontend/src/pages/BoardStory.tsx` (button now uses `<a download>` + endpoint URL)
  - Modify: `frontend/src/components/ExecutiveRiskMatrix.tsx` (same)
  - Modify: `frontend/src/pages/Dashboard.tsx` (same)
- **Dependencies:** S2-A2 (anti-hallucination numeric-trace validator) for fixture data.
- **Acceptance:** Frontend never builds PDF in the browser. All numbers in the PDF body trace back to scoring snapshot fields (verified by `tests/test_narrative_anti_hallucination.py`).
- **Unit tests:** `tests/test_board_story_pdf_endpoint.py` — known-fixture; deterministic; PDF stream begins with `%PDF-` and contains the 10 section IDs.
- **Risks:** None (decommissioning client-built PDF removes a class of risk).
- **Rollback:** Endpoint returns 503; frontend buttons stay disabled.

---

#### TASK S1.8-AUDIT-FIX-B01
- **Title:** Explicit redirect from `/integrations` → `/dashboard/evidence-network`
- **Status:** BLOCKED — depends on S1.8-AUDIT-FIX-D01
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-C01
- **Title:** Remove dead `/dashboard/pilot-program` and `/sentinel` links
- **Status:** READY
- **Owner:** Frontend
- **Tags:** HIGH · Routes-must-404 invariant
- **Files:** `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/GovernanceProfile.tsx`. Sweep all `pages/**/*.tsx` for stale href substrings.
- **Acceptance:** No `<Link>` in `frontend/src/pages/**` points at `/sentinel` or `/pilot-program`. New unit test `tests/frontend/test_link_integrity.py` enforces.
- **Rollback:** Restore prior Link hrefs.

---

#### TASK S1.8-AUDIT-FIX-D01
- **Title:** Single-prefix routing audit / route uniqueness
- **Status:** READY
- **Owner:** Frontend
- **Files:** `frontend/src/App.tsx`
- **Acceptance:** Each page reachable through exactly one canonical path. Legacy top-levels replaced with `<Navigate replace />`.

---

#### TASK S1.8-AUDIT-FIX-E01
- **Title:** Rename `PersonaSwitcher` file (currently `components/dashboard/PersonaContext.tsx`)
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-F01
- **Title:** Pass `orgId` to `getEvidenceConfidence()`
- **Status:** READY
- **Owner:** Frontend
- **Files:** `frontend/src/api.ts`, `EvidenceNetwork.tsx`, `Dashboard.tsx`.

---

#### TASK S1.8-AUDIT-FIX-G01
- **Title:** Persona-driven widget matrix (declarative)
- **Status:** READY
- **Owner:** Frontend
- **Tags:** HIGH · S2-B6 acceptance
- **Acceptance:** Persona=EXECUTIVE and Persona=FORENSIC show DISJOINT widget sets. `tests/frontend/test_persona_widget_filter.py` enforces.

---

#### TASK S1.8-AUDIT-FIX-H01
- **Title:** Validate `?org` UUID on board-story / decision / business-unit pages
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-I01
- **Title:** Extract EvidenceNetwork tabs into separate components
- **Status:** READY
- **Owner:** Frontend
- **Acceptance:** `EvidenceNetwork.tsx` is ≤ 200 lines and only contains the header + tab router.

---

#### TASK S1.8-AUDIT-FIX-J01
- **Title:** Confidence gauge: render unavailable state instead of `84` fallback
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-L01
- **Title:** DecisionEngine baseline score: render unavailable state
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-M01
- **Title:** Unify `dataSource` and `persona` toggles
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-N01
- **Title:** Sourced numbers in `getExecutiveExplanation()`
- **Status:** READY
- **Owner:** Frontend
- **Tags:** MEDIUM · PRODUCT_MOAT #4 violation
- **Hard constraint:** No hardcoded fallback risk/MTTR values.

---

#### TASK S1.8-AUDIT-FIX-O01
- **Title:** Tighten `DecisionAction` types (Literal)
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-P01
- **Title:** ScoreUnavailableState component (centralizes F-011/F-014/F-020)
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-Q01
- **Title:** Refresh `.deprecated_routes.txt` to be authoritative
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-R01
- **Title:** Fix Tailwind invalid token `slate-955`
- **Status:** READY
- **Owner:** Frontend

---

#### TASK S1.8-AUDIT-FIX-S01
- **Title:** Strict typing against Pydantic schemas (replace `Record<string, any>`)
- **Status:** READY
- **Owner:** Frontend
- **Tags:** HIGH · Strict-typing invariant
- **Files:** `frontend/src/api.ts` (`DecisionAction`, `ProjectReadinessResponse`, `BoardStorySection`, `OrgConfidenceResponse`).

---

#### TASK S1.8-AUDIT-FIX-T01
- **Title:** Frontend lint: no hardcoded numeric fallback patterns
- **Status:** READY
- **Owner:** Frontend

---



### READY (builder may pick now)
- S1.8-B2, S1.8-B4, S1.8-C4, S2-B1, S2-B4, S2-C2, **S1.8-AUDIT-FIX-A01 (CRITICAL)**, **S1.8-AUDIT-FIX-C01 (HIGH)**, **S1.8-AUDIT-FIX-G01 (HIGH)**, **S1.8-AUDIT-FIX-S01 (HIGH)**

### IN_PROGRESS
- (none)

###


### Blocked — single dependency
- S1.8-A2 → A1
- S1.8-A3 → A2
- S2-A2 → A1
- S2-A4 → A3
- S2-B2 → B1
- S2-B3 → B1
- S2-B5 → B3
- S2-B6 → S1.8-A6
- S2-C3 → S1.8-A6

### Blocked — multi-dependency
- S1.8-A4 → A1, A2, A3
- S1.8-A5 → A3, A4
- S1.8-A6 → A5 (schema lock)
- S1.8-B6 → B2, B4, B5
- S1.8-B7 → B6 (schema lock)
- S1.8-C5 → C4 (schema lock)
- S2-A1 → Sprint 1.8 Phase A scoring feed
- S2-A3 → A1, A2
- S2-C1 → B1, B3
- S2-C4 → ALL backend tasks

### Parallel tracks (no shared dependency)
- Backend track 1 (Readiness): A1 → A2 → A3 → A4 → A5
- Backend track 2 (Tech Intel): B1 → B2 ─┐
                                B3 → B4 ─┴→ B6
                                B5 → B6
- Backend track 3 (Evidence): C1 → C2 → C3 → C4
- Backend track 4 (Sprint 2 prep): B4 (independent; can start now)
- Frontend track (single implementer, sequential): A6 → B7 → C5 → S2-A4 → S2-B5 → S2-B6
- Auditing track (Claude, parallel): runs AFTER each task reaches COMPLETED, before merge

---

## Builder Update Discipline

When picking up a READY task, the builder:
1. Sets the task's Status to `IN_PROGRESS` here.
2. Implements exactly the listed files. No side-quest refactors.
3. Runs the listed tests. All must pass.
4. Sets Status to `COMPLETED` on completion, `FAILED` on failure (with reason appended).
5. Updates `AGENT_LOG.md` with task ID, owner, files, deviation notes.
6. Updates `SESSION_HANDOFF.md` `Next Immediate Task` to the next READY task.
7. After merge, hands off to Claude for audit (architecture, security, PRODUCT_MOAT compliance, regression).
