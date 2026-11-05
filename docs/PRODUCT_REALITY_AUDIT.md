# Product Reality Audit

Based on a strict codebase review of the AIRS (ResilAI) repository as of August 10, 2026.

## 1. What is real?
- **Authentication:** Firebase Authentication (`signInWithGoogle`, `signInWithEmail`) is fully implemented in `frontend/src/contexts/AuthContext.tsx`.
- **Database:** SQLAlchemy + SQLite/PostgreSQL backend (`app/db/database.py`) modeling organizations, users, and telemetry events.
- **Evidence Framework:** `ConnectorManager` handles connector synchronization. `WazuhConfig`, `SplunkConnector`, and `ElasticService` are actual connectors with live heartbeat/health check API routes in `app/api/v1/integrations.py`.
- **API Middleware:** `CORSErrorSafetyMiddleware` and proper API routing are active in `app/main.py`.

## 2. What is simulated?
- **Organizations:** An empty organization state falls back to creating `My's Clinic` or assigning the user to `sandbox-org` or `ResilAI Sandbox Clinic` (e.g. `api.ts`, `AuthContext.tsx`).
- **Telemetry Data (in Demo Mode):** `MOCK_ACME_DAILY_READINESS` and `MOCK_SANDBOX_DAILY_READINESS` are injected when `isDemo` is true or the org ID is hardcoded to `sandbox-org` (found in `frontend/src/api.ts`).
- **Technical UI Elements:** Some dashboard elements (like 92% Technology Health or 4 Active Risks) in `Dashboard.tsx` are hardcoded placeholders in the React components, rather than populated from live API data.

## 3. What is hardcoded?
- **Demo Mode Flags:** `DemoModeContext.tsx` sets `organizationName` to `'ResilAI Sandbox Clinic'`.
- **Dashboard Metrics:** Several metrics in `Dashboard.tsx` (like incident readiness score fallback to 72, Executive explanation texts, framework mappings) are hardcoded arrays.
- **Default Organization IDs:** `sandbox-org` and `default-org` are referenced in multiple backend services (e.g., `app/api/v1/simulations.py`, `app/api/clinic/router.py`).

## 4. What is deterministic?
- **Governance Scoring:** The Governance Health Index (GHI) is calculated deterministically via `governance_engine.py` (e.g., 40% audit, 30% lifecycle, 20% SLA, 10% compliance).
- **Control Verification:** Drift monitoring and SIEM health checks rely on explicit database queries to `TelemetryEvent`.

## 5. What is LLM-generated?
- **Narratives only:** The LLM (Gemini) generates executive summaries, business impact, and remediation narratives via `app/services/llm_narrative.py`. It is explicitly firewalled from modifying scores (as validated in `app/api/narratives.py`).

## 6. What data reaches the readiness engine?
- **Telemetry Events:** Normalized logs from Splunk, Wazuh, and Elastic are stored as `TelemetryEvent` rows and analyzed by the rules engine for gap analysis.

## 7. What data reaches the dashboard?
- **Aggregated Readiness State:** The frontend consumes `getDailyReadinessReport`, `getGovernanceHealthIndex`, and `getEvidenceConfidence`. However, the frontend currently falls back to mock data if the backend returns nothing or the user is in demo mode.

## 8. What endpoints are production capable?
- `/api/v1/integrations/splunk/configure`
- `/api/v1/integrations/splunk/logging-health`
- `/api/v1/integrations/wazuh/agent-status`
- `/api/v1/auth/me`
- `/api/v1/organizations` (CRUD operations)

## 9. What endpoints still use demo/mock behavior?
- Frontend functions in `api.ts` intercept requests for `sandbox-org` and return `MOCK_SANDBOX_DAILY_READINESS`.
- Some backend telemetry endpoints default to `sandbox-org` if no `org_id` is passed, which injects seed data.

## 10. What is tenant-scoped?
- Almost all tables (e.g. `organizations`, `assessments`, `telemetry_events`, `connectors`) have an `org_id` column and foreign keys.

## 11. What is not tenant-scoped?
- Globally hardcoded mock configurations (e.g., `MOCK_ACME_DAILY_READINESS`).

## 12. Which integrations actually ingest evidence?
- **Splunk:** Implemented in `app/integrations/splunk/client.py`.
- **Wazuh:** Implemented in `app/services/wazuh_client.py`.
- **Elastic:** Implemented in `app/services/elastic.py`.

## 13. Which integrations are UI-only?
- Several UI connectors in `Connectors.tsx` (e.g. Okta, SentinelOne) have visual presence but no backend ingestion equivalent beyond generic Webhook mapping.

## 14. What is the current billing state?
- **None:** There are no Stripe SDKs, billing models, or subscription webhooks present in the codebase.

## 15. What is the actual deployment topology?
- **Backend:** FastAPI application designed for Google Cloud Run (evident from `gcp/env.*.yaml`).
- **Frontend:** React + Vite application deployed to Firebase Hosting (`firebase.json`).
- **Data:** Cloud SQL (PostgreSQL) and Firestore for configuration sync.
