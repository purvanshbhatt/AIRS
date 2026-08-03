# Deployment Guide

## Environments

- **Local**: frontend on Vite, backend on FastAPI, local SQLite
- **Staging**: Firebase staging hosting + Cloud Run staging backend
- **Production**: Firebase production hosting + Cloud Run production backend

## Local Quick Run (PowerShell)

```powershell
Copy-Item .env.dev.example .env.dev
$env:ENV="local"
py -3 -m alembic upgrade head
py -3 -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm ci
npm run dev -- --port 5173
```

## Staging Deploy

```powershell
cd frontend
npm run build:staging
cd ..
firebase deploy --only hosting:staging
bash ./scripts/deploy_cloud_run.sh --service airs-api-staging --region us-central1 --env-file gcp/env.staging.yaml --project gen-lang-client-0384513977
```

## Production Deploy

```powershell
cd frontend
npm run build:production
cd ..
firebase deploy --only hosting:airs
bash ./scripts/deploy_cloud_run.sh --service airs-api --region us-central1 --env-file gcp/env.prod.yaml --project gen-lang-client-0384513977 --prod
```
