# Sprint 3 Orchestration Plan — Platform Consolidation & Production Readiness

## Overview
ResilAI Sprint 3 requires consolidating legacy components, themes, and authentication into the unified Domain Architecture, deploying backend and frontend to staging environments (Cloud Run + Firebase Hosting), validating live staging integration, and producing all 13 canonical deliverable reports.

## Milestones

### Milestone 1: Survey & Codebase Audit
- Dispatch 3 Explorers / Spec Miners (`teamwork_preview_explorer` / `teamwork_preview_spec_miner`) to analyze `P:\projects\AIRS\frontend` and root `AIRS`.
- Audit existing providers, layouts, legacy components, route definitions, theme system, Firebase Auth setup, and Sales Demo Mode state.
- Formulate precise pruning list and consolidation plan without deleting active references.

### Milestone 2: Consolidation Phases 1-4 (Pruning, Design System, Theme, Routing & State)
- Dispatch Workers (`teamwork_preview_worker`) to remove dead references and prune retired components safely.
- Remap theme tokens and CSS variables in `index.css` to `DESIGN_SYSTEM.md`.
- Unify routing and state management into a single source of truth.
- Verify `npm run build` after each pruning step to ensure zero regressions.

### Milestone 3: Consolidation Phases 5-8 (Firebase Auth, Terminology, Demo Mode, Performance)
- Reconnect Firebase Auth with proper session persistence, token refresh, and login flow.
- Overhaul terminology across frontend ("Verification" -> "Health Check").
- Configure First-Class Sales Demo Mode (Acme Health Systems) with rich mock data.
- Optimize frontend bundles, lazy loading, and asset delivery.

### Milestone 4: Phase 9 Staging Deployment & E2E Staging Validation
- Deploy backend to Cloud Run staging service.
- Deploy frontend to Firebase Hosting staging environment.
- Perform live E2E testing against staging URLs (auth persistence without 401 loops, backend API calls without CORS errors, full Acme Health Systems demo flow).
- Note: Localhost validation alone is prohibited; staging validation is mandatory.

### Milestone 5: 13 Deliverables & Forensic Integrity Audit Gate
- Generate/update all 13 canonical deliverable reports in `.gemini/antigravity/brain/`:
  1. `PRODUCT_MAP.md`
  2. `STAGING_TEST_REPORT.md`
  3. `UI_INVENTORY.md`
  4. `DESIGN_SYSTEM.md`
  5. `FEATURE_MAP.md`
  6. `ROUTE_MAP.md`
  7. `COMPONENT_MAP.md`
  8. `FRONTEND_ARCHITECTURE.md`
  9. `API_CONTRACT.md`
  10. `STATE_MANAGEMENT.md`
  11. `PERFORMANCE_AUDIT.md`
  12. `SECURITY_AUDIT.md`
  13. `RELEASE_NOTES.md`
- Dispatch 2 Reviewers (`teamwork_preview_reviewer`) and 2 Challengers (`teamwork_preview_challenger`).
- Dispatch 1 Forensic Auditor (`teamwork_preview_auditor`) for final integrity verification.
- Pass all gates (Build 0 errors, Zero TS/ESLint warnings, Staging E2E pass, Clean Audit).
