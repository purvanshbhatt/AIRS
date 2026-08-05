## Task Assignment for teamwork_preview_worker_m3_1

**Mission**: Execute Milestone 3 (Phases 5-8 Consolidation: Firebase Auth, Terminology Overhaul, Sales Demo Mode, and Performance).

**Instructions**:
1. Read `P:\projects\AIRS\.agents\ORIGINAL_REQUEST.md` completely.
2. Read `P:\projects\AIRS\.agents\teamwork_preview_explorer_m1_2\handoff.md` and `P:\projects\AIRS\.agents\teamwork_preview_spec_miner_m1_1\handoff.md`.
3. Firebase Auth & Session Persistence:
   - In `frontend/src/lib/firebase.ts`, explicitly import `setPersistence` and `browserLocalPersistence` from `firebase/auth` and invoke `setPersistence(auth, browserLocalPersistence)`.
   - In `frontend/src/contexts/AuthContext.tsx`, ensure `auth.authStateReady()` is awaited before setting loading to false or initializing token provider, preventing the 401 race condition during page load.
4. Terminology Overhaul ("Verification" -> "Health Check"):
   - Perform systematic terminology refactoring across `frontend/src`:
     - Rename customer-facing labels from "Verification" to "Health Check" (e.g. `AIDrawer.tsx` -> "Deterministic Evidence & Health Check", `EvidenceNetwork.tsx` -> "Evidence Network & Health Check", `VerificationSummaryGrid.tsx` -> "Health Check Summary").
     - In `src/types/readiness.ts`, add backwards-compatible type interface mapping (`health_check` property alongside legacy `verification` alias).
5. First-Class Sales Demo Mode (Acme Health Systems):
   - Standardize default organization name in `api.ts` / `DemoModeContext.tsx` as `"Acme Health Systems"`.
   - Ensure demo mode mutation firewall in `api.ts` blocks POST/PUT/DELETE requests with toast alert `"Read-Only Demo: Saving changes is disabled in the interactive demo."`.
   - Verify `getDailyReadinessReport` returns full non-empty dataset (98% clinic health, `safe_to_open`, 7 healthy connectors, verified backups).
6. Performance & Bundle Optimization:
   - In `frontend/vite.config.ts`, verify or configure `manualChunks` split strategy for heavy dynamic modules (graph visualizations, evidence networks).
7. Verification:
   - Run `npm run build` in `P:\projects\AIRS\frontend`.
   - Verify exit code 0 and zero TypeScript compilation errors.
8. MANDATORY INTEGRITY WARNING:
   DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
9. Write detailed handoff report to `P:\projects\AIRS\.agents\teamwork_preview_worker_m3_1\handoff.md` and send message to parent.
