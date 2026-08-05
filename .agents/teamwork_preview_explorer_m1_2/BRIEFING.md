# BRIEFING — 2026-08-04T15:29:00Z

## Mission
Survey Firebase Auth, Backend API contracts, CORS setup, and Staging Infrastructure.

## 🔒 My Identity
- Archetype: explorer
- Roles: teamwork_preview_explorer_m1_2
- Working directory: P:\projects\AIRS\.agents\teamwork_preview_explorer_m1_2
- Original parent: 47c0c19d-36db-48cb-a0a9-5b3b4af6af9e
- Milestone: m1_2

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Inspect P:\projects\AIRS\frontend and root P:\projects\AIRS
- Document 401 login loops, CORS issues on staging, session persistence, Cloud Run & Firebase configs

## Current Parent
- Conversation ID: 47c0c19d-36db-48cb-a0a9-5b3b4af6af9e
- Updated: 2026-08-04T19:25:44Z

## Investigation State
- **Explored paths**:
  - `frontend/src/lib/firebase.ts`, `frontend/src/contexts/AuthContext.tsx`, `frontend/src/api.ts`, `frontend/src/components/ProtectedRoute.tsx`, `frontend/src/App.tsx`, `frontend/src/runtimeConfig.ts`
  - `.env.staging`, `.env.demo`, `.env.development`, `.env.production`
  - `firebase.json`, `.firebaserc`, `gcp/env.staging.yaml`, `gcp/env.demo.yaml`
  - `scripts/deploy_cloud_run.ps1`, `scripts/deploy_frontend.ps1`, `scripts/get_deployment_urls.ps1`
  - `app/main.py`, `app/core/auth.py`, `app/core/config.py`, `app/core/cors.py`, `app/core/middleware.py`, `app/api/v1/config.py`
- **Key findings**:
  1. Race condition in AuthContext token provider hydration causes early unauthenticated API calls -> 401 response -> handleUnauthorized() forced redirect loop to /login.
  2. `app/api/v1/config.py` fallback URL `https://api-staging.resilai.org` overrides frontend API base URL when `CLOUD_RUN_SERVICE_URL` is omitted in `gcp/env.staging.yaml`.
  3. `App.tsx` lines 130-142 forces redirect from `airs-staging-0384513977.web.app` to `staging.resilai.org`.
  4. Absence of explicit `setPersistence(auth, browserLocalPersistence)` in `firebase.ts`.
- **Unexplored areas**: none (full survey completed)

## Key Decisions Made
- Completed thorough read-only investigation across frontend, backend, configs, and deployment infrastructure.
- Generated handoff.md report with 5-component structure.

## Artifact Index
- `P:\projects\AIRS\.agents\teamwork_preview_explorer_m1_2\handoff.md` — Detailed survey & handoff report
