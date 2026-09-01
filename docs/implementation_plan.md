# ResilAI V2 — Design Partner Product Stabilization Plan

## Goal
Transform ResilAI into an understandable, trustworthy, functional, and demo-ready product for the first 3–5 healthcare design partners. This plan aligns the product with the Executive (L1), Manager (L2), and IT/MSP (L3) levels while preserving the deterministic, evidence-first technical moat.

## Phase 1 — Stabilization

### 1. Acme Health & Tenancy Purge
- `[MODIFY] frontend/src/components/layout/AppLayout.tsx`: Remove hardcoded `<ReadinessHeader orgName="Acme Healthcare" />`. Fetch the actual organization name using `getOrganization(orgId)`.
- `[MODIFY] frontend/src/contexts/DemoModeContext.tsx`: Remove hardcoded 'Acme Health Systems' and 'Acme Health'. Replace with explicit 'Demo Organization' / 'Sandbox' naming.
- `[MODIFY] frontend/src/api.ts`: Ensure `MOCK_ACME_DAILY_READINESS` is strictly bounded to the Sandbox/Demo mode. True authenticated users must never fall back to this payload.
- `[MODIFY] app/services/demo_seed.py`: Update the database seeder to explicitly use 'ResilAI Sandbox Clinic' rather than a generic name.

### 2. Crash Fixes & Route Restoration
- `[MODIFY] frontend/src/features/readiness/RecoveryReadinessPage.tsx`: Fix the crash caused by referencing outdated nested properties (`report.business_continuity.verified_systems` -> `operational_readiness.critical_systems_verified`, etc.).
- `[MODIFY] frontend/src/App.tsx`: Restore the `/documents` route to point to the `DocumentsPage`.
- `[NEW] frontend/src/pages/Documents.tsx`: Create the baseline Stitch-compliant Documents page if completely missing.

### 3. Production CORS Hardening
- `[MODIFY] app/core/middleware.py`: Refactor `CORSErrorSafetyMiddleware` so that during an exception, it safely echoes the requested origin if valid, rather than using a wildcard (`*`) alongside `credentials=true` which violates browser security policies.

### 4. Auth Verification
- `[MODIFY] frontend/src/contexts/AuthContext.tsx`: Verify the Google authentication redirects to the correct active workspace context and handles missing org profiles gracefully.

## Phase 2 — Product Narrative

### Landing Page Overhaul
- `[MODIFY] frontend/src/pages/Landing.tsx`: 
  - Rewrite hero section to focus on: "Know if your healthcare organization is ready before an incident happens."
  - Highlight the CONNECT → VERIFY → UNDERSTAND → ACT loop.
  - Explain the 3-level personas (Owner, Manager, IT).
  - Strip generic GRC/AI jargon and focus on "Deterministic Technical Verification."

## Phase 3 — Documents (First-Class Feature)

### Document Center Implementation
- `[MODIFY] frontend/src/pages/Documents.tsx` or create `frontend/src/features/documents/`:
  - Implement a 3-tab layout: **Executive Reports** (Daily Brief, Monthly Summary), **Evidence Vault** (HIPAA Evidence, Security Policies, Vendor Evidence), and **Audit Trail** (Verification History, Remediation Logs).
  - Ensure reports draw from the server-authoritative `DailyReadinessReport` DTO.

## Phase 4 — Recovery Readiness

### RTO & RPO Visualization
- `[MODIFY] frontend/src/features/readiness/RecoveryReadinessPage.tsx`:
  - Visualize critical systems, backup verification, and identity readiness.
  - Implement explicit empty states for missing evidence: "Unable to verify" instead of defaulting to a healthy state.
  - Display Recovery Blockers prominently.

## Phase 5 — Remediation Trust

### Trust-Based Verification UI
- `[MODIFY] frontend/src/features/readiness/RemediationWorkflow.tsx` (or related action cards):
  - Change the optimistic client-side UI update from "Resolved" to a rigorous state machine: `Problem detected → Remediation requested → Re-checking evidence → Verified / Unable to Verify`.
  - Ensure the action log records the remediation attempt.

## Phase 6 — Integration-Agnostic Evidence Architecture

### Agnostic Architecture Design
- `[MODIFY] app/services/evidence/__init__.py` & `app/services/evidence/registry.py`:
  - Introduce conceptual interfaces for `WebhookEvidenceAdapter` and `ManualUploadAdapter`.
  - Ensure the pipeline can ingest generic JSON webhooks and normalize them into `EvidenceRecord` without requiring a direct connector.

## Phase 7 — MSP-First Readiness

### Tenancy and MSP Architecture
- `[NEW] docs/architecture/MSP_TENANCY_MODEL.md`:
  - Define the logical relationship between Clinic → MSP → ResilAI to support cross-tenant management in the future.
- `[MODIFY] app/schemas/organization.py` (if applicable):
  - Ensure the org model has `parent_org_id` or `managed_by_msp_id` fields prepared for future multi-tenant operations.

## Phase 8 — UI Polish

### Premium Healthcare Aesthetic
- `[MODIFY] frontend/src/index.css` & `frontend/tailwind.config.js`:
  - Implement calm, professional, healthcare-specific colors.
  - Strip excessive gradients or fake telemetry charts from the L1 Executive view.
  - Make the L3 IT Workspace dense, typography-focused, and operational.

## Phase 9 — Design Partner Demo Mode

### Sandbox Isolation
- `[MODIFY] frontend/src/components/layout/AppLayout.tsx`:
  - If `isDemoMode` is true, explicitly render a "SANDBOX" or "DEMO ORGANIZATION" badge in the header so the user knows they are not looking at live telemetry.

## Phase 10 — Verification

### E2E Testing Protocol
- Run `npm run build` and `py -m pytest` successfully.
- Manually execute the 18-point verification checklist provided by the user.

## Post-Implementation Output
Once all phases are complete, I will generate:
1. `docs/agent_memory/CURRENT_SPRINT.md`
2. `docs/agent_memory/NEXT_TASKS.md`
3. `docs/agent_memory/AGENT_LOG.md`
4. `docs/agent_memory/DESIGN_PARTNER_READINESS.md`
