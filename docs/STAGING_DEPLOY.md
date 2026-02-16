# Staging Deployment Runbook

Use this to deploy safely to staging first, then promote to production.

## Backend: Cloud Run Staging (`airs-api-staging`)

1. Ensure staging env file exists and is updated:

- `gcp/env.staging.yaml`
- Set `CORS_ALLOW_ORIGINS` to your staging frontend origin(s)

2. Deploy staging service:

```powershell
make deploy-staging
```

Optional Secret Manager bindings (recommended):

```powershell
make deploy-staging STAGING_SECRETS="GEMINI_API_KEY=projects/gen-lang-client-0384513977/secrets/GEMINI_API_KEY:latest"
```

The deploy script blocks accidental production overwrite unless `--prod` is passed.

## Frontend: Firebase Hosting Staging Target

Create staging hosting site once:

```powershell
firebase hosting:sites:create airs-staging
firebase target:apply hosting airs-staging airs-staging
```

Build and deploy frontend to staging:

```powershell
cd frontend
npm ci
npm run build:staging
cd ..
firebase deploy --only hosting:airs-staging
```

## CORS Update Checklist

When staging URL changes:

1. Update `frontend/.env.staging` `VITE_API_BASE_URL`
2. Update backend `gcp/env.staging.yaml` `CORS_ALLOW_ORIGINS`
3. Re-deploy backend staging (`make deploy-staging`)
4. Rebuild/redeploy frontend staging (`npm run build:staging` + `firebase deploy --only hosting:airs-staging`)

## Promote to Production

Backend (explicit guarded deploy):

```powershell
make deploy-prod
```

Frontend production:

```powershell
cd frontend
npm ci
npm run build:production
cd ..
firebase deploy --only hosting:airs
```

Production deploy guard: `scripts/deploy_cloud_run.sh` refuses deployment to `airs-api` unless `--prod` is present (handled by `make deploy-prod`).
