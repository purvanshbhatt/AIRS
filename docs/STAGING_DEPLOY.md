# ResilAI Staging and Production Deployment Runbook

This guide documents safe deployment flow with strict staging and production separation.

## 1. Deployment Targets

- Staging backend (Cloud Run): `airs-api-staging`
- Production backend (Cloud Run): `airs-api`
- Staging frontend (Firebase Hosting target): `staging`
- Production frontend (Firebase Hosting target): `airs`

## 2. Preconditions

- `gcloud` authenticated to project `gen-lang-client-0384513977`
- Firebase CLI authenticated
- Required secrets configured in CI/CD:
  - `GCP_SA_KEY`
  - `GCP_PROJECT_ID`
  - `FIREBASE_TOKEN`

## 3. Backend Environment Files

- Staging: `gcp/env.staging.yaml`
- Production: `gcp/env.prod.yaml`

Do not hardcode secrets in these files. Use Secret Manager bindings via deploy flags or CI secrets.

## 4. Deploy Backend to Staging

PowerShell:

```powershell
bash ./scripts/deploy_cloud_run.sh --service airs-api-staging --region us-central1 --env-file gcp/env.staging.yaml --project gen-lang-client-0384513977
```

Optional secret bindings:

```powershell
bash ./scripts/deploy_cloud_run.sh --service airs-api-staging --region us-central1 --env-file gcp/env.staging.yaml --project gen-lang-client-0384513977 --set-secrets "GEMINI_API_KEY=projects/gen-lang-client-0384513977/secrets/GEMINI_API_KEY:latest"
```

Validate:

```powershell
curl https://airs-api-staging-227825933697.us-central1.run.app/health
curl https://airs-api-staging-227825933697.us-central1.run.app/health/system
curl https://airs-api-staging-227825933697.us-central1.run.app/health/llm
```

## 5. Deploy Frontend to Staging

```powershell
cd frontend
npm ci
npm run build:staging
cd ..
firebase deploy --only hosting:staging
```

Validate:
- Open `https://airs-staging-0384513977.web.app`
- Confirm API diagnostics point to staging backend URL
- Confirm Firebase auth works for staging domain

## 6. Promote Backend to Production

Production guard is enforced by `scripts/deploy_cloud_run.sh` and requires `--prod`.

```powershell
bash ./scripts/deploy_cloud_run.sh --service airs-api --region us-central1 --env-file gcp/env.prod.yaml --project gen-lang-client-0384513977 --prod
```

Emergency rollback example:

```powershell
gcloud run services update-traffic airs-api --region us-central1 --to-revisions "airs-api-00065-qpn=100"
```

## 7. Deploy Frontend to Production

```powershell
cd frontend
npm ci
npm run build:production
cd ..
firebase deploy --only hosting:airs
```

Production URL:
- `https://gen-lang-client-0384513977.web.app/`

## 8. CORS Alignment Checklist

When changing frontend URLs:

1. Update frontend API base URL in correct env file:
   - staging: `frontend/.env.staging`
   - production: `frontend/.env.production`
2. Update backend `CORS_ALLOW_ORIGINS` in matching `gcp/env.*.yaml`
3. Redeploy backend
4. Rebuild and redeploy frontend
5. Recheck `/health/cors`

## 9. Firebase Config Checklist

- Never commit real Firebase API keys in tracked env files.
- Use local override (`frontend/.env.staging.local`) for local staging builds.
- Ensure staging and production domains are in Firebase Auth authorized domains.

## 10. CI/CD Behavior

- Push to `dev`:
  - test + staging build
  - deploy staging only when required secrets exist
- Push to `main`:
  - test + production build
  - deploy production only when required secrets exist

Security workflow runs separately for secret scan and dependency audits.
