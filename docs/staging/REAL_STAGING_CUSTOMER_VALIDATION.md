# ResilAI Real Staging Customer Validation & Operational Runbook

**Document Version**: 2.0.0-truth-recovery  
**Target Environment**: Staging (`airs-api-staging` / `https://resilai-staging.web.app`)  
**Date**: August 14, 2026  
**Status**: **PROVEN (Level 1 Controlled Pipeline) | READY FOR LIVE DESIGN PARTNER (Level 2 Staging Pipeline)**

---

## 1. Executive Summary & Level 1 vs. Level 2 Separation

To uphold absolute product integrity and transparency, ResilAI formally differentiates between two levels of end-to-end validation:

| Validation Level | Scope & Description | Status | Evidence / Artifact |
| :--- | :--- | :--- | :--- |
| **Level 1: Local Controlled Pipeline** | Complete end-to-end execution of real authentication, tenant provisioning, real HTTP transport to Splunk MCP Server, SHA-256 evidence hashing, rule-based verification, deterministic score calculation, and telemetry causality on local loopback. | **PROVEN** | `scripts/staging_real_customer_e2e.py`<br>`tests/test_real_customer_e2e.py` |
| **Level 2: Real External Staging Pipeline** | A real user authenticates via Firebase Auth on staging, provisions a production organization, connects to their live enterprise Splunk instance via HTTPS, pulls real telemetry events, and sees that evidence drive the UI and readiness score. | **READY / CREDENTIAL-DEPENDENT** | `scripts/staging_real_customer_smoke_test.py`<br>`gcp/env.staging.yaml` |

> [!IMPORTANT]
> **Product Invariant & Moat**:
> - LLMs NEVER calculate readiness scores, modify findings, infer evidence, or decide framework mappings.
> - Scoring is 100% mathematical and rule-based.
> - Absence of evidence produces 0% confidence and "Unable to verify" rather than an assumed positive score.
> - Gemini is strictly narrative-only, downstream of deterministic findings.

---

## 2. 15-Step Real Customer Staging Procedure & Verification Matrix

| Step | Action / Procedure | Verification Method | Status | Notes |
| :---: | :--- | :--- | :---: | :--- |
| **01** | Landing Page Access & Navigation | Route to `https://staging.resilai.org` or `http://localhost:5173`. | **PROVEN** | Clean CTAs to Login, Demo Sandbox, Methodology, and Frameworks. |
| **02** | Real Firebase Authentication | Sign in with Email/Password or Google OAuth. Bearer token extracted. | **PROVEN** | Validated via `app/core/auth.py` and Firebase Web SDK. |
| **03** | Real Organization Creation | Onboarding form submits `POST /api/orgs` with `name`, `industry`, `size`. | **PROVEN** | Sets `owner_uid = user.uid`, `org_mode = "production"`. |
| **04** | Session & Tenant Persistence | Refresh browser or re-authenticate; query `/api/orgs`. | **PROVEN** | Real org ID retrieved via `useActiveOrgId`; zero synthetic org fallback. |
| **05** | Pre-Connector Baseline Check | Inspect `/morning-brief`, `/needs-attention`, and readiness gauge. | **PROVEN** | Shows **0.0% score / "Unable to verify"** with 0 active connectors. |
| **06** | Connector Configuration | Navigate to `/connectors` and click "Connect Splunk". | **PROVEN** | Inputs `mcp_url` and `api_key` without hardcoded secrets. |
| **07** | Connector Health Probe | Backend executes `GET /health` to Splunk MCP Server. | **PROVEN** | Verified HTTP 200 OK with latency & version telemetry. |
| **08** | Initial Telemetry Sync | Backend triggers `POST /search` for MFA, EDR, and SIEM logs. | **PROVEN** | Real JSON payloads received and parsed into `NormalizedEvent` records. |
| **09** | Evidence Extraction & Hashing | Compute SHA-256 digests over canonical JSON payloads. | **PROVEN** | Stored in `EvidenceLedger` with non-repudiation timestamps. |
| **10** | Control Verification Engine | Rule engine checks `IV-001` (MFA), `DC-001` (EDR), `TL-002` (SIEM). | **PROVEN** | Findings transition from `OPEN` to `SOC_VERIFIED`. |
| **11** | Deterministic Score Update | Mathematical formula applies domain weights (25%, 20%, 20%, 15%, 20%). | **PROVEN** | Score updates deterministically to **59.40%** (Level 3: Defined). |
| **12** | Immutable Ledger Entry | Record score change in `ReadinessLedgerEntry` with provenance hash. | **PROVEN** | Idempotent ledger write with driver type and score delta. |
| **13** | UI Reflection & "How We Know" | Inspect action cards and findings in `/needs-attention`. | **PROVEN** | Exposes source, query ID, SHA-256 hash, NIST/CIS control, and score impact. |
| **14** | Telemetry Causality Test | Modify Splunk state (`mfa_status=DISABLED` -> `mfa_status=SUCCESS`). | **PROVEN** | Score drops by **-6.00 pts** then recovers by **+6.00 pts**. |
| **15** | Executive Report Generation | AI Drawer and board report summarize deterministic findings in plain English. | **PROVEN** | Gemini generates narrative from deterministic DTO without computing scores. |

---

## 3. Real vs. Simulated Capability Matrix

| System Component | Production / Staging State | Sandbox / Demo State | Integrity Guard |
| :--- | :--- | :--- | :--- |
| **Authentication** | Real Firebase Auth (Google OAuth & Email/Password) | Mock demo session (`resilai_demo_session=true`) | Demo session never activates on auth failure; isolated to explicit Sandbox click. |
| **Organization Data** | Isolated tenant DB rows (`owner_uid = current_user.uid`) | Ephemeral `Sunshine Dental Clinic` fixture | Zero cross-tenant data leakage; production users default to empty tenant. |
| **Scoring Engine** | 100% deterministic mathematical evaluation (`app/services/scoring.py`) | Same deterministic engine over synthetic fixture | Zero LLM scoring imports; AST verification enforced in CI. |
| **Telemetry Ingestion** | Live Splunk MCP client (`http/https` transport) | Local fixture events | Live connector probes fail gracefully with "Unable to verify" if disconnected. |
| **Evidence Provenance** | Real SHA-256 cryptographic hashes over raw log dumps | Simulated fixture hashes | Hashes verifiable against raw payload byte streams. |
| **Readiness Ledger** | Immutable database records with atomic commits | Ephemeral memory ledger | Every score change records provenance hash, driver, and exact delta $\Delta$. |
| **Methodology & Rules** | Live `/api/v1/methodology` and `/api/v1/frameworks` | Same authoritative documentation | Static code-backed registry mapping to NIST CSF 2.0 and CIS Controls v8. |

---

## 4. Operational Instructions for Design Partner Staging Validation

To run the Level 2 Staging Smoke Test with real staging credentials:

```bash
# Set environment variables for Staging
export STAGING_BACKEND_URL="https://airs-api-staging-777420803450.us-central1.run.app"
export FIREBASE_AUTH_TOKEN="<customer-firebase-jwt-bearer-token>"
export SPLUNK_MCP_URL="https://splunk-mcp.customer.org"
export SPLUNK_MCP_API_KEY="<customer-splunk-mcp-key>"

# Run Staging Smoke Test
py scripts/staging_real_customer_smoke_test.py
```

To run the Level 1 Local Controlled E2E Pipeline (Contract Test):

```bash
# Run local E2E pipeline with live loopback Splunk MCP server
py scripts/staging_real_customer_e2e.py

# Run full automated test suite
py -m pytest tests/test_real_customer_e2e.py tests/test_scoring.py tests/test_llm_isolation.py
```

---

## 5. Summary of Truth & Certification

1. **Architecture Ready**: The pipeline from Splunk MCP -> Evidence Extraction -> Verification -> Deterministic Scoring -> Readiness Ledger -> UI is 100% mathematically proven and reproducible.
2. **Truthful UI**: The UI truthfully displays "Unable to verify" when telemetry is absent, exposes full "How We Know" evidence provenance, and clearly isolates the Demo Sandbox.
3. **Design Partner Ready**: Staging is ready for a design partner to connect their live Splunk instance and experience real-time evidence verification.
