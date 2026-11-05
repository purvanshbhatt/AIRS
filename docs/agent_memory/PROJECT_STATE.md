# ResilAI Current State

Version: 1.0.0-design-partner-ready
Telemetry Pipeline Consolidation cut over: 2026-07-15
Design Partner Ready declared: 2026-08-10

Current Goal:
Execute the Design Partner EAP (Early Access Program) with 3-5 real healthcare organizations. The core loop (Connect -> Verify -> Understand -> Act) is now end-to-end operational across the L1/L2/L3 workspaces.

Core Architecture:
- Frontend: React (18.3.1) + Vite (6.4.1) + TypeScript (5.5.3) + TailwindCSS (4.1.18)
- Backend: FastAPI (0.115+) (Python 3.11+) + SQLAlchemy (2.0+)
- Database: Firestore (Primary Persistence, via firebase-admin 6.5+) + SQLite (In-Memory Cache)
- Hosting: Firebase Hosting (Frontend), Google Cloud Run (Backend)
- LLM: Gemini 3 Flash (via google-genai 1.0+). Some subsystems use Gemini 2.5 Flash.
- Splunk Telemetry: SplunkMCPClient (app/integrations/splunk/client.py) — the single backend Splunk intent. `app/connectors/splunk.py::SplunkConnector` and `app/services/splunk.py::SplunkService` both delegate to it.

Rules:
- LLM never calculates scores. Scoring remains deterministic.
- Gemini is only used to generate narratives and unstructured text extraction.
- Verification engine uses telemetry from connected systems (Wazuh, Splunk, etc.).
- Splunk telemetry flows through `SplunkMCPClient` exclusively; no direct HEC REST in production paths.
- Scoring consumes normalized `EvidenceRecord` shapes; never vendor-specific payloads.
- Microsoft integrations prioritized for the enterprise market.

Recent Changes (2026-08-14):
- Real Customer End-to-End & Telemetry Causality Proven: Built `scripts/staging_real_customer_e2e.py` and `tests/test_real_customer_e2e.py` proving real customer lifecycle, real HTTP transport to Splunk MCP Server, SHA-256 evidence hashing, rule-based verification, deterministic score calculation, and telemetry causality (score drops and recovers in response to live telemetry state). Documented in `docs/staging/REAL_CUSTOMER_E2E.md`.
- Connector Architecture Fix: Updated `app/connectors/base.py` to support `org_id` parameter alias in `Connector.__init__` and pass through `events` in `ConnectorSyncResult`.
- Splunk Health Check & Auth Fix: Updated `app/connectors/splunk.py` to accept `healthy` and `ok` status codes from Splunk MCP Server.

Recent Changes (2026-07-15):
- `app/connectors/splunk.py::SplunkConnector` — new canonical production connector (`@register_connector`, `CONNECTOR_TYPE="splunk"`), wraps `SplunkMCPClient`, executes four MCP searches per sync (MFA, EDR, logging heartbeat, notable) and yields `NormalizedEvent` records.
- `app/services/splunk.py::SplunkService` — internal HTTP transport switched to `SplunkMCPClient._request`; public `verify_*` and `run_custom_query` surface unchanged.
- `app/services/connector_manager.py::_ingest_events` — calls `EvidenceOrchestrator.ingest_collection_result` after the legacy `TelemetryEvent` write, AND registers the splunk/wazuh `EvidenceAdapter` instances on first sync.
- `app/services/evidence/__init__.py` — re-exports `EvidenceAdapter`, `EvidenceRecord`, `AdapterHealth`, `EvidenceRegistry`, `get_instance`, `reset_instance`.
- `app/schemas/evidence.py::OrgConfidenceResponse` — `details` field renamed to `connectors` to match Dashboard gauge shape.
- `gcp/env.staging.yaml` — `SPLUNK_MCP_URL` + `SPLUNK_MCP_API_KEY` added.

Recent Changes (pre-2026-07-15):
- Made tech stack discovery asynchronous to prevent timeouts.
- Added Assessment Archive logic via `AssessmentService.archive` and `DELETE` endpoint.
- Added `CORSErrorSafetyMiddleware` to guarantee CORS headers on ALL responses including 5xx errors and Cloud Run timeouts.
- Expanded `CORS_ALLOW_ORIGINS` in `gcp/env.prod.yaml` with all Firebase Hosting domains.
- Added `ReadinessLedgerEntry` model + Alembic migration `9a1c0b3d2e4f`. Idempotency index, 0–100 score range validator, FK to organizations.
- Locked `calculate_readiness_delta()` as the single source of scoring per ADR-007. Runtime isolation guard scans `sys.modules` for forbidden LLM imports at module load; expanded docstring documents the deterministic contract.
- `app/services/readiness_drivers.py` — `extract_drivers()` and `extract_action_items()`.
- `app/services/readiness_ledger.py` — `record_score_change()`, `attach_to_scoring()`, `score_and_record()`.
- `app/api/v1/readiness.py` + `app/schemas/readiness.py` — 4 GET endpoints `/api/v1/readiness/{drivers,actions,ledger,timeline}`.
- `app/services/lifecycle/normalization.py` extended with `resolve_eol_status()`.

Current Workstreams:

[IN PROGRESS]
1. Telemetry Pipeline (cutover 2026-07-15)
Owner: Backend Agent
Status: Operational — Splunk MCP → Evidence Adapter → Evidence
Registry → Verification Engine → Deterministic Scoring now executes
on the canonical SplunkConnector + ConnectorManager path. Adapter-
based confidence gauge at GET /api/v1/connectors/confidence now
returns real, computed scores.

2. Trust Dashboard
Owner: Frontend Agent
Status: Dashboard lists assessments & scores.

3. Assessment Lifecycle
Owner: Backend Agent / Frontend Agent
Status: Archive functionality recently implemented.

4. Sprint 1.8 Phase A — Readiness Drivers & Ledger
Owner: Backend Core Agent
Status: S1.8-A1..A5 COMPLETED 2026-07-12. Drivers/actions/ledger/
timeline endpoints live.

Dependencies:
- Trust Dashboard requires: `getAssessments` API
- Discovery Engine requires: Wazuh, Splunk API configurations
- /api/v1/connectors/confidence requires: registered `EvidenceAdapter`
  instances (wiring automation added 2026-07-15)
- Splunk verification requires: an active Splunk Connector row with
  `mcp_url` + `api_key` credentials.

