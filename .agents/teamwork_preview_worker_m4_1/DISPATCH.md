## Task Assignment for teamwork_preview_worker_m4_1

**Mission**: Execute Milestone 4 (Phase 9 Staging Deployment & Live Staging Validation).

**Instructions**:
1. Read `P:\projects\AIRS\.agents\ORIGINAL_REQUEST.md` completely.
2. Read `P:\projects\AIRS\.agents\teamwork_preview_explorer_m1_2\handoff.md` and `P:\projects\AIRS\.agents\teamwork_preview_spec_miner_m1_1\handoff.md`.
3. Backend Staging Deployment (Cloud Run):
   - Check `gcp/env.staging.yaml` and ensure `CLOUD_RUN_SERVICE_URL` or `API_BASE_URL` is set to the Cloud Run staging service URL (e.g. `https://airs-api-staging-40384513977.us-central1.run.app` or current active Cloud Run service URL).
   - Ensure `CORS_ALLOW_ORIGINS` includes `https://airs-staging-0384513977.web.app`, `https://airs-staging-0384513977.firebaseapp.com`, `https://staging.resilai.org`, `http://localhost:5173`.
   - Execute backend Cloud Run deployment using `scripts/deploy_cloud_run.ps1` or gcloud deployment commands.
4. Frontend Staging Deployment (Firebase Hosting):
   - Check `frontend/.env.staging` or environment variables to ensure `VITE_API_BASE_URL` points to the Cloud Run staging URL.
   - Execute frontend production build for staging (`npm run build:staging` or `npm run build` in `frontend/`).
   - Execute deployment to Firebase Hosting staging target (`airs-staging-0384513977`) using `scripts/deploy_frontend.ps1` or `firebase deploy --only hosting:staging --project gen-lang-client-0384513977`.
5. Live Staging Validation & Verification:
   - Verify frontend staging URL accessibility (`https://airs-staging-0384513977.web.app`).
   - Verify Firebase Auth login flow and session persistence without 401 redirect loops.
   - Verify backend REST API calls succeed with HTTP 200/304 and zero CORS errors.
   - Verify First-Class Sales Demo Mode (Acme Health Systems) renders 98% health, safe_to_open, and read-only mutation guards on staging.
6. Generate `STAGING_TEST_REPORT.md`:
   - Document complete deployment metadata, live staging URLs, authentication test results, CORS header checks, Demo Mode validation matrix, and network latency logs.
   - Write file to BOTH `P:\projects\AIRS\STAGING_TEST_REPORT.md` and `.gemini/antigravity/brain/` artifact directory.
7. MANDATORY INTEGRITY WARNING:
   DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
8. Write detailed handoff report to `P:\projects\AIRS\.agents\teamwork_preview_worker_m4_1\handoff.md` and send message to parent.
