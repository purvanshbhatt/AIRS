# Sprint

Goal:
Telemetry Pipeline Consolidation — one production path:
Splunk MCP → Evidence Adapter → Evidence Registry → Verification
Engine → Deterministic Scoring.

Tasks:

[Done]
- S1.8-C5: Implemented EvidenceNetwork.tsx, updated Dashboard.tsx header confidence gauge, and aliased Integrations.tsx.
- S2-A4: Implemented BoardStory.tsx boardroom narration client interface with 10 sections and robust fallback modes.
- S2-B5: Implemented DecisionEngine.tsx investment projection tool with direct actions toggle.
- S2-B6: Implemented BusinessUnits.tsx risk heatmap and built the Dashboard PersonaSwitcher.
- S2-C3: Cleaned up orphaned dashboard routes (SentinelDashboard, PilotDashboard) and saved backup route configs in .deprecated_routes.txt.
- 2026-07-13 Audit: NO PASS — 26 findings (F-001..F-026), 22 fix tasks registered.
- 2026-07-15 Backend: deleted `app/integrations/sentinel_splunk/` (third Splunk implementation); canonical `app/connectors/splunk.py::SplunkConnector` created; `app/services/splunk.py::SplunkService` now routes its search through `SplunkMCPClient`; `EvidenceOrchestrator.ingest_collection_result` + `EvidenceAdapter` registration wired into `ConnectorManager._ingest_events`; `OrgConfidenceResponse.details` renamed to `.connectors` matching Dashboard gauge; dead code (sentinel_test.py, junk `app/api/import urllib.py`, four dead hackathon scripts) removed; `SPLUNK_MCP_URL` + `SPLUNK_MCP_API_KEY` added to `gcp/env.staging.yaml`; 881 pytest passing.

[In Progress]
- S1.8-AUDIT-FIX-A01 — server-side Board Story PDF endpoint (CRITICAL).

[Blocked]
- S1.8-AUDIT-FIX-B01 — depends on FIX-D01.

