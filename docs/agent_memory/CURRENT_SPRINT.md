# Sprint

Goal:
Telemetry Pipeline Consolidation — one production path:
Splunk MCP → Evidence Adapter → Evidence Registry → Verification
Engine → Deterministic Scoring.

Tasks:

[Done]
- 2026-08-31 ResilAI Authenticated Product Experience & Product Identity Refactoring:
- 2026-09-01 Backend Executive Capabilities & Explainability Layer:
  - Created deterministic explanation service (`app/services/explanation.py`) leveraging Gemini strictly for narrative translation (no scoring, no finding modification) with fallback mechanisms.
  - Built org-scoped API contracts (`POST /api/orgs/{org_id}/explanations`, `GET /api/orgs/{org_id}/onboarding`, `POST/GET /api/orgs/{org_id}/reports`).
  - Implemented `ExecutiveReportGenerator` wrapper integrating deterministic framework alignments (NIST CSF 2.0) into the professional PDF generation.
  - Enforced strict tenant isolation on all new endpoints and report access using Firebase UID owner filtering.
  - Automated testing: Built `test_framework_validation.py`, `test_encryption_validation.py`, `test_explanation_service.py`, `test_demo_isolation.py`, `test_tenant_isolation_v2.py`. 81/81 backend tests pass.
  - Overhauled authenticated dashboard into a 5-stage narrative hierarchy (*Readiness Hero → Why → Needs Attention → Recommended Actions → Evidence Provenance*).
  - Built 4-tier progressive disclosure model in `ExecutiveExplanation.tsx` and `AIDrawer.tsx`.
  - Implemented 6-step guided Getting Started workflow (`Onboarding.tsx`) with per-org persistence and persistent top-bar trigger.
  - Implemented contextual Demo Mode banner and dismissible section guidance across all main pages.
  - Added "Explain for Leadership" drawer calling backend `/api/v1/clinic/{org_id}/explain` (0 client-side LLM calls / 0 client-side scoring).
  - Modernized Documents and Governance pages removing legacy 5-domain questionnaire framing.
  - Verified with 124/124 passing Vitest unit tests and clean production compilation.
- 2026-08-25 Maidensail Dofollow Badge Integration & Production Landing Page Deployment:
  - Embedded the Maidensail startup verification badge (`<a href="https://maidensail.com/startup/resilai" rel="dofollow"><img src="https://maidensail.com/badge/resilai.svg?theme=dark" alt="Featured on Maidensail" height="44"></a>`) in `Landing.tsx` footer.
  - Resolved UI component library exports and variant compatibility in `Badge.tsx`, `Toast.tsx`, and `ui/index.ts`.
  - Built production bundle (`dist-production/assets/index-CZYEJhN2.js`) with 0 errors.
  - Deployed to Firebase Hosting (`resilai-marketing`) and verified live on `https://resilai.org`.
- 2026-08-23 Production Organization Lifecycle Self-Healing, Executive Homepage Experience & Tech Stack Restoration:
  - Multi-Container Cache Miss Fallback: Added `firestore_get_org` in `app/db/firestore.py` and connected `OrganizationService.get()` / `get_all()` to Firestore fallback with owner isolation verification.
  - Reactive Stale ID Self-Healing: Enhanced `useActiveOrg.ts` with reactive state that detects obsolete/deleted organization IDs in `localStorage` and smoothly pivots to the user's first valid organization without 404 traps.
  - Zero-Org Handshake across All Readiness Pages: Guarded `TodayPage.tsx`, `NeedsAttentionPage.tsx`, `RecoveryReadinessPage.tsx`, `ActivityPage.tsx`, and `TechnologyIntelligence.tsx` with clean workspace setup cards for new users.
  - Recoverable Error States: Upgraded `<ErrorState />` in `ReadinessStates.tsx` with "Create Organization", "Reset Workspace", and "Demo Sandbox" CTAs.
  - Restored Tech Stack Navigation & Routing: Re-added "Tech Stack & Inventory" to L3 (IT & Security) navigation in `AppSidebar.tsx`, added route redirects for `/tech-stack`, `/technology`, `/inventory` in `App.tsx`, and wired `TechnologyIntelligence.tsx` to `useActiveOrg()`.
  - Executive-First Home Page Experience: Upgraded `Landing.tsx` hero graphic to an interactive Executive Morning Brief Card (plain-English posture + safeguards) with a toggle to technical telemetry/cURL/JSON streams.
  - Verification: 57/57 backend tests passing, `npm run build` and `npm run build:staging` passing with code 0.
- 2026-08-21 Frontend — Production Productization & Executive UX Recovery:
  - Organization Onboarding Guard: If a user has no organization established, `TodayPage.tsx` directly renders the "Set up your readiness workspace" card with a `[Create Organization]` CTA, avoiding 404s or unrouted API calls.
  - Polished Zero-Evidence Executive State: When a live organization has 0 connectors / 0 evidence, `TodayPage.tsx` displays the high-taste "Not Yet Verified" executive state ("Your readiness journey starts here", "Status: Not Yet Verified", "What we know: No security systems connected / No telemetry received / No verified evidence available", "Next step: Connect a security system", and the Trust Invariant guarantee).
  - Unmistakable Environment Badges: Updated `ReadinessHeader.tsx` to clearly distinguish `DEMO WORKSPACE (SIMULATED DATA)` in amber vs `LIVE WORKSPACE` in emerald.
  - Pure SVG Icons: Sidebar and headers standardized on Lucide React SVG components with zero font ligature dependencies.
  - Docs & Methodology Overhaul: Updated `/docs/methodology` to feature the 5-Stage Verification Operating Model (1. Connect → 2. Verify → 3. Measure → 4. Explain → 5. Improve) with interactive persona switching (For Healthcare Executives vs For IT & Security).
  - Contextual 404 Error Formatting: Fixed `api.ts` error prefixing to prevent duplicate "Not found: Not Found" strings.
  - Live Deployments & CDN Verification: Deployed all 4 hosting targets via Firebase CLI (`resilai-marketing`, `gen-lang-client-0384513977`, `airs-staging-0384513977`, `resilai-staging`) and verified live assets on `https://resilai.org` and `https://staging.resilai.org`.
- 2026-08-21 Production Organization Lifecycle — Durable Persistence Guarantee & Cold Start Durability Verification:
  - Durable Persistence: Enforced mandatory dual-write to Firestore during organization creation in `app/services/organization.py`. Prevented silent fallback/swallowing on Firestore write failure.
  - Cold Start Durability Suite: Implemented 4 comprehensive tests in `tests/test_production_org_lifecycle.py` verifying org persistence across simulated instance restarts, assessment recovery, readiness scoring determinism post-restart, and cross-tenant isolation.
  - Conftest Fix: Removed mock suppression on `sync_orgs_from_firestore` / `sync_assessments_from_firestore` in `tests/conftest.py` so real sync functions execute under testing.
  - Test Suite Validation: 29/29 lifecycle tests passed, 7/7 explainability tests passed, 21/21 assessment tests passed.
- 2026-08-21 Production Homepage Conversion Optimization (Primary Google Login Flow & Pilot CTA Realignment):
  - Primary Acquisition Path: Replaced public homepage "Request Pilot" CTA with "Get Started" routing directly to Google Login and unified organization onboarding.
  - Value Verification CTAs: Added secondary "See How It Works" anchor link to the 4-step core verification loop (`#how-it-works`) and preserved one-click "Explore Demo Sandbox".
  - Design Partner Qualification Continuity: Preserved underlying `/pilot` route, schema, and `submitEnterprisePilotLead` backend integration for qualified healthcare/MSP design partner conversions.
  - V2 Messaging Alignment: Refreshed headline and value copy to strictly emphasize continuous deterministic control testing and mathematical evidence.
  - Build & Type Validation: Verified `npm run build` and `npm run build:staging` with zero TypeScript or bundling errors.
- 2026-08-19 Production Organization Lifecycle & Real Telemetry Integrity Recovery:
  - Root Cause Fixed: Eliminated unrouted 404 from empty `org_id` strings and prevented demo data injection into real organizations caused by `not pilot.get_mode(org_id)` fallback.
  - Telemetry Pipeline: Wired clinic readiness endpoint directly to real `TelemetryEvent` rows ingested via existing `ConnectorManager` pipeline (no parallel pipeline).
  - Clean Zero-Evidence State: New real organizations with zero connectors/telemetry return honest `status="unknown"`, `clinic_health_pct=0` (zero positive readiness without evidence).
  - Pilot & Demo Mode Isolation: `PilotService.get_mode()` defaults to `PILOT` (real mode); demo seeding and synthetic telemetry are restricted strictly to `OrgMode.DEMO`.
  - Removed demo seeding invocations (`ensure_demo_seed_data`) from production `list_organizations` and `list_assessments` endpoints.
  - Enhanced error contract in `http_exception_handler` with structured error codes (`ORGANIZATION_NOT_FOUND`, `RESOURCE_NOT_FOUND`, `ORG_ID_REQUIRED`).
  - Added atomic organization creation with non-blocking Firestore dual-write resilience.
  - Created 25-case automated test suite in `tests/test_production_org_lifecycle.py` validating full lifecycle, tenant isolation, causality, and AST LLM isolation.
- 2026-08-14 Real Customer E2E Telemetry Causality & Staging Verification (Falsifiable Evidence Proof):
  - Created `scripts/staging_real_customer_e2e.py` and `tests/test_real_customer_e2e.py` verifying the complete real customer lifecycle: Real Auth -> Org Creation -> Invariant Check (0 connectors = 0% confidence) -> Real HTTP Splunk MCP Connector Probe -> SHA-256 Evidence Ingestion -> Verification Engine -> Deterministic Scoring -> Readiness Ledger Recording.
  - Executed Telemetry Causality Test proving mathematical causality: Splunk MFA failure dropped score by -6.00 points; restoring MFA recovered score by +6.00 points.
  - Verified Server-Side Tenant Isolation (User B cannot access User A's data).
  - Fixed Connector class constructor and ConnectorSyncResult event pass-through in `app/connectors/base.py` and `app/connectors/splunk.py`.
  - Documented complete evidence matrix in `docs/staging/REAL_CUSTOMER_E2E.md`.
  - Automated test suite (68 tests) and frontend production bundle verified clean (exit code 0).
- 2026-08-14 Product Integrity Recovery & Real Staging Validation Complete:
  - Fixed Onboarding React hook violation (`useAuth` inside callback) for flawless real organization registration.
  - Restructured Login and Landing architectures: Primary auth path is real credentials (Email/Password & Google OAuth); Sales Evaluation Demo Sandbox is strictly separated with clear simulated data disclaimers.
  - Restored Trust & Transparency in Sidebar and Header: permanent links to `/docs/methodology` (live `GET /api/v1/methodology` with Trust Invariant banner) and `/docs/frameworks`.
  - Enforced Non-Negotiables: 100% deterministic mathematical scoring; zero LLM influence on readiness scoring; evidence invariant ("No evidence → No readiness claim").
  - Executed End-to-End Staging Product Integrity validation script (`scripts/staging_product_integrity_validation.py`): Real organization creation, Splunk telemetry ingestion (`IV-001`, `DC-001`, `TL-002`), deterministic score recomputation, and immutable ledger recording.
  - Verified 156+ automated backend test suites (100% pass rate) and compiled TypeScript staging build with zero errors.
  - Captured complete 13-view screenshot suite verifying desktop and mobile layouts.
- 2026-08-14 Executive UX / E2E Product Readiness QA & Staging + Prod Pipeline Complete:
  - Eliminated all executive trust violations (removed `72`, `84%`, `Elevated` fallbacks; enforced "No evidence → no readiness claim").
  - Plain-English executive UX implemented with zero jargon in business views, preserving technical depth in IT/Operations.
  - Resolved Firebase Auth API key injection and persistent one-click Sandbox Executive Demo mode.
  - Deployed single staging API backend (`airs-api-staging`) and staging frontend (`https://resilai-staging.web.app` / `https://staging.resilai.org`).
  - Executed automated Playwright E2E smoke tests and captured complete video recording `staging_live_demo_recording.webm`.
  - Satisfied Production Deployment Gate with strict production isolation (`airs-api` on Cloud Run via `gcp/env.prod.yaml`, `resilai-marketing` / `https://resilai.org` on Firebase Hosting).
- 2026-08-08 Frontend/Integration: Completed Stitch Frontend Redesign & Backend Integration Audit. Connected Stitch UI views (`Today`, `Needs Attention`, `Recovery`, `Documents`, `Governance`, `Connectors`, `IT Workspace`) directly to server-authoritative backend telemetry, deterministic scoring DTOs, and dynamic multi-tenant org resolution (`useActiveOrgId`). Produced `docs/agent_memory/STITCH_INTEGRATION_AUDIT.md`. Production build verified clean (`npm run build` exit code 0).
- 2026-08-03 DevOps: Emergency SCA Remediation — force-patched frontend dependency graph resolving 48 Dependabot vulnerabilities (`websocket-driver`, `vite`, `react-router`, `tmp`, `braces`, `micromatch`, `cross-spawn`); verified production build; commit `f071157` pushed to `main`.
- S1.8-C5: Implemented EvidenceNetwork.tsx, updated Dashboard.tsx header confidence gauge, and aliased Integrations.tsx.
- S2-A4: Implemented BoardStory.tsx boardroom narration client interface with 10 sections and robust fallback modes.
- S2-B5: Implemented DecisionEngine.tsx investment projection tool with direct actions toggle.
- S2-B6: Implemented BusinessUnits.tsx risk heatmap and built the Dashboard PersonaSwitcher.
- S2-C3: Cleaned up orphaned dashboard routes (SentinelDashboard, PilotDashboard) and saved backup route configs in .deprecated_routes.txt.
- 2026-07-13 Audit: NO PASS — 26 findings (F-001..F-026), 22 fix tasks registered.
- 2026-07-15 Backend: deleted `app/integrations/sentinel_splunk/` (third Splunk implementation); canonical `app/connectors/splunk.py::SplunkConnector` created; `app/services/splunk.py::SplunkService` now routes its search through `SplunkMCPClient`; `EvidenceOrchestrator.ingest_collection_result` + `EvidenceAdapter` registration wired into `ConnectorManager._ingest_events`; `OrgConfidenceResponse.details` renamed to `.connectors` matching Dashboard gauge; dead code (sentinel_test.py, junk `app/api/import urllib.py`, four dead hackathon scripts) removed; `SPLUNK_MCP_URL` + `SPLUNK_MCP_API_KEY` added to `gcp/env.staging.yaml`; 881 pytest passing.

[In Progress]
- None (Sprint goals delivered and verified).

[Blocked]
- None.


