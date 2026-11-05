# ResilAI Sprint 1.8 + Sprint 2 Implementation Specification

**Document Type:** Principal Architect Specification
**Status:** Approved for Execution
**Target Environment:** Staging Only

---

## 1. Architecture Review & Technical Debt Analysis

### Current Architecture State
The current ResilAI architecture successfully separates deterministic scoring (`app/services/scoring.py`) from AI narrative generation (`app/services/ai_narrative.py`), satisfying the core invariant. The backend uses FastAPI + SQLAlchemy, and the frontend is React + Vite + Tailwind.

### Identified Technical Debt
1. **Frontend Bloat & Orphaned Routes:**
   - `Dashboard.tsx` has grown to ~1,400 lines, mixing layout, data fetching, and widget rendering.
   - `App.tsx` contains orphaned or outdated routes (e.g., `SentinelDashboard.tsx`, `PilotDashboard.tsx`).
   - `TechStack.tsx` and `Integrations.tsx` currently function as flat lists rather than intelligence hubs.
2. **Missing Immutable Ledger:**
   - Score deltas are calculated on the fly but not immutably persisted. There is no `ReadinessLedger` for historical point-in-time auditing.
3. **Hardcoded Integrations:**
   - Existing integrations (e.g., Splunk) are built as one-off API hooks rather than using a vendor-agnostic adapter pattern (`Connector -> Evidence Adapter -> Evidence Registry`).
4. **Mocked Services:**
   - `cve_enrichment.py` currently relies on mock NVD/KEV data for staging.

---

## 2. Alignment with PRODUCT_MOAT

This specification ensures strict adherence to the `PRODUCT_MOAT.md`:
*   **LLMs never score:** The new Executive Decision Engine re-uses the deterministic `calculate_readiness_delta()` function.
*   **Telemetry over Questionnaires:** The Evidence Network establishes a robust pipeline for ingesting live configuration state from Splunk, Wazuh, and AWS.
*   **Evidence over Self-Attestation:** Introduction of the **Evidence Confidence** score (formerly Trust Score) mathematically weights the reliability of telemetry over human input.

---

## 3. Implementation Specification

### Feature A: Readiness Intelligence (Readiness Drivers & Ledger)

*   **Business objective:** Provide executives with an auditable, prioritized list of what is impacting their readiness score and what immediate actions to take.
*   **UX objective:** Replace static lists with an interactive "Readiness Drivers" widget and an "Executive Actions" panel ("What to do Monday morning").
*   **Backend architecture:** Introduce `readiness_drivers.py` to extract and sort impacts from `scoring.py`. Introduce `readiness_ledger.py` to intercept score recalculations and write immutable records.
*   **Frontend architecture:** Refactor `Dashboard.tsx` to extract widgets into separate components. Implement `SlideOver.tsx` for deep-dives into specific drivers.
*   **APIs:**
    *   `GET /api/v1/readiness/drivers?org_id={id}`
    *   `GET /api/v1/readiness/actions?org_id={id}`
    *   `GET /api/v1/readiness/ledger?org_id={id}`
    *   `GET /api/v1/readiness/timeline?org_id={id}`
*   **Database changes:** Create `ReadinessLedgerEntry` (UUID, org_id, timestamp, previous_score, new_score, delta, driver_type, driver_item, impact, evidence_source, created_by).
*   **Dependencies:** Requires successful resolution of `calculate_readiness_delta()`.
*   **Risks:** High write volume to the Ledger if score recalculations trigger too frequently.
*   **Acceptance criteria:** Every score change creates an immutable ledger row. The Dashboard correctly surfaces the top 5 positive and negative drivers.
*   **Testing strategy:** Unit tests for driver extraction logic. Integration tests simulating scoring changes and verifying ledger writes.

---

### Feature B: Technology Intelligence & AI Estate

*   **Business objective:** Pivot from a generic "Asset Inventory" to a readiness-focused view of the technology stack, highlighting end-of-life (EOL), KEVs, and AI governance gaps.
*   **UX objective:** Split the monolithic Tech Stack page into 6 focused tabs (Inventory, Lifecycle, Exposure, Dependencies, Timeline, Insights). Rename AI Inventory to "AI Estate".
*   **Backend architecture:** Introduce `technology_intelligence.py` as an orchestration layer over discovery and CVE enrichment. Add AI finding rules (`AI-001` to `AI-010`) to `findings.py`. Add `ai_frameworks.py` for coverage calculation.
*   **Frontend architecture:** Replace `TechStack.tsx` with `TechnologyIntelligence.tsx` using a tabbed routing structure. Ensure readiness impact points are prominent on every item card.
*   **APIs:**
    *   `GET /api/v1/technology/inventory` (rich items with readiness impact)
    *   `GET /api/v1/technology/lifecycle`
    *   `GET /api/v1/technology/exposure`
    *   `GET /api/v1/frameworks/coverage`
*   **Database changes:** Expand `AiAsset` enum types (Vector DBs, MCP Servers, Agent Frameworks).
*   **Dependencies:** `GlobalSoftwareCatalog` (for lifecycle).
*   **Risks:** False positives in EOL detection due to normalized version string mismatches.
*   **Acceptance criteria:** The AI Estate accurately tracks non-traditional assets (e.g., Prompt Libraries). The frontend displays accurate coverage percentages for NIST AI RMF and MITRE ATLAS.
*   **Testing strategy:** E2E UI testing of the 6 tabs. Unit testing for the framework coverage calculator.

---

### Feature C: Evidence Network & Evidence Confidence

*   **Business objective:** Prove control efficacy through live telemetry, creating a massive barrier to entry for competitors relying on manual GRC uploads.
*   **UX objective:** Transform "Integrations" into an "Evidence Graph" showing connector health, evidence count, and a deterministic Evidence Confidence score.
*   **Backend architecture:** Build a vendor-agnostic MCP adapter pattern (`EvidenceAdapter` base class). Implement `Evidence Registry` to normalize incoming data before it hits the Verification Engine. Implement `evidence_confidence.py` (Freshness × Uptime × Success Rate × Completeness).
*   **Frontend architecture:** Create `EvidenceNetwork.tsx` featuring connector status cards and an architecture flow diagram. Add the Evidence Confidence metric to the main Dashboard header.
*   **APIs:**
    *   `GET /api/v1/connectors/confidence`
*   **Database changes:** None (relies on existing Connector and Evidence tables).
*   **Dependencies:** Third-party APIs (Splunk, Wazuh, AWS).
*   **Risks:** Third-party API rate limits or outages dropping the Evidence Confidence score unexpectedly.
*   **Acceptance criteria:** Evidence Confidence calculates deterministically (0-100). The adapter pattern allows swapping Splunk for SentinelOne with zero changes to the Verification Engine.
*   **Testing strategy:** Mock third-party APIs to simulate timeouts, expired tokens, and stale data, ensuring the Evidence Confidence score drops accordingly.

---

### Feature D: Executive Intelligence (Board Story & Decision Engine)

*   **Business objective:** Equip CISOs and CEOs with board-ready narratives and the ability to project ROI on security investments.
*   **UX objective:** Provide a structured, multi-section Board Story view (not just a PDF download). Provide an interactive Executive Decision Engine where users can toggle remediation actions and watch the projected score change.
*   **Backend architecture:** Refactor `ai_narrative.py` to output 10 structured sections. Create `decision_engine.py` that utilizes a "what-if" projection model (feeding hypothetical state into the existing scoring engine).
*   **Frontend architecture:** Create `BoardStory.tsx` and `DecisionEngine.tsx`. Introduce the `Organization Heatmap` to `BusinessUnits.tsx`. Add persona-based widget visibility context.
*   **APIs:**
    *   `POST /api/v1/decisions/project` (Input: proposed actions; Output: projected readiness)
    *   `GET /api/v1/decisions/recommended-actions`
*   **Database changes:** Add `is_clone: bool` and `source_org_id: str` to `Organization` model (architectural prep for Sprint 2.5 Digital Twin).
*   **Dependencies:** Gemini API for the Board Story narrative layer.
*   **Risks:** The Decision Engine projection drifting from the actual score calculation if logic is duplicated. (Mitigation: Re-use the exact same `calculate_readiness_delta` function).
*   **Acceptance criteria:** The Board Story generates 10 distinct sections. The Decision Engine updates the projected score instantly when a user clicks "Patch PostgreSQL".
*   **Testing strategy:** Integration tests ensuring `project_readiness` exactly matches the output of an actual database state change.

---

## 4. Execution Directives for Builders

1.  **Staging First:** All backend deployments must target `airs-api-staging`. All frontend deployments must use `firebase deploy --only hosting:staging`.
2.  **No Schema Changes Without Migrations:** Any updates to models require Alembic revisions.
3.  **Strict Typing:** Ensure TypeScript interfaces perfectly map to Pydantic schemas, especially for the new `ReadinessDriver` and `EvidenceConfidence` models.
4.  **Subagent Handoff:**
    *   *Backend Builder* executes Phase A and B (API & DB).
    *   *Evidence Architect* executes Phase C (Adapter Pattern).
    *   *Frontend Implementer* consumes APIs and builds Phase A, B, C, and D UIs.
