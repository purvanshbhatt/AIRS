# ResilAI

ResilAI is an AI incident readiness platform for security teams.  
It measures readiness, maps findings to MITRE/CIS/OWASP, generates executive reports, and supports headless integrations through API keys and webhooks.

## Public Beta

- Staging frontend: `https://airs-staging-0384513977.web.app`
- Staging backend health: `https://airs-api-staging-227825933697.us-central1.run.app/health`
- Staging backend docs: `https://airs-api-staging-227825933697.us-central1.run.app/docs`

Production demo endpoints remain isolated and are not overwritten by staging workflows.

## Core Capabilities

- Deterministic readiness scoring
- Framework mapping: MITRE ATT&CK, CIS Controls v8, OWASP Top 10
- Executive report generation (PDF)
- Integrations:
  - API key pull endpoint (`GET /api/external/latest-score`)
  - Webhook push events (`assessment.scored`)
  - Mock SIEM seed for staging demos
- Operational endpoints:
  - `GET /health`
  - `GET /health/llm`
  - `GET /health/system`

## Architecture

- Frontend: React, TypeScript, Vite, Tailwind
- Backend: FastAPI, SQLAlchemy, Alembic
- Auth: Firebase Auth (real Firebase in staging/prod, emulator in local dev)
- Hosting:
  - Frontend on Firebase Hosting targets
  - Backend on Cloud Run services
- LLM:
  - Gemini SDK via `google.genai`
  - Narratives only (scoring remains deterministic)

## Repository Layout

```text
.
|-- app/                      # FastAPI app
|-- alembic/                  # DB migrations
|-- frontend/                 # React application
|-- docs/                     # Runbooks and product docs
|-- scripts/                  # Deploy/dev scripts
|-- gcp/                      # Environment templates for Cloud Run
`-- .github/workflows/        # CI/CD workflows
```

## Environment Modes

| Mode | Frontend Env File | Backend Env Source | Auth Mode | Typical Use |
|---|---|---|---|---|
| Local dev | `frontend/.env.development` | `.env.dev` + `ENV=local` | Firebase Auth Emulator | Feature development |
| Staging | `frontend/.env.staging` (+ local override for sensitive values) | `gcp/env.staging.yaml` | Real Firebase | Internal demos, QA |
| Production | `frontend/.env.production` | `gcp/env.prod.yaml` | Real Firebase | Public demo/product |

## Local Setup (PowerShell)

1. Install backend dependencies:

```powershell
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
```

2. Create backend local env file:

```powershell
Copy-Item .env.dev.example .env.dev
```

3. Ensure `.env.dev` has at least:

```env
ENV=local
DATABASE_URL=sqlite:///./airs_dev.db
CORS_ALLOW_ORIGINS=http://localhost:5173
```

4. Run migrations:

```powershell
$env:ENV="local"
py -3 -m alembic upgrade head
```

5. Frontend env (`frontend/.env.development`) should include:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_PROJECT_ID=gen-lang-client-0384513977
VITE_FIREBASE_AUTH_DOMAIN=gen-lang-client-0384513977.firebaseapp.com
VITE_FIREBASE_API_KEY=REPLACE_WITH_FIREBASE_WEB_API_KEY
VITE_FIREBASE_AUTH_EMULATOR=http://127.0.0.1:9099
```

6. Run services:

Backend:
```powershell
$env:ENV="local"
py -3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```powershell
cd frontend
npm ci
npm run dev -- --host 0.0.0.0 --port 5173
```

Auth emulator:
```powershell
firebase emulators:start --only auth --project demo-airs
```

## Staging Deploy

Frontend:

```powershell
cd frontend
npm ci
npm run build:staging
cd ..
firebase deploy --only hosting:staging
```

Backend:

```powershell
bash ./scripts/deploy_cloud_run.sh --service airs-api-staging --region us-central1 --env-file gcp/env.staging.yaml --project gen-lang-client-0384513977
```

## Production Deploy

Frontend:

```powershell
cd frontend
npm ci
npm run build:production
cd ..
firebase deploy --only hosting:airs
```

Backend (`--prod` required by guardrail):

```powershell
bash ./scripts/deploy_cloud_run.sh --service airs-api --region us-central1 --env-file gcp/env.prod.yaml --project gen-lang-client-0384513977 --prod
```

## CI/CD

- `push` to `dev`:
  - test backend and frontend build
  - deploy to staging only if required secrets are present
- `push` to `main`:
  - test backend and frontend build
  - deploy to production only if required secrets are present
- security workflow:
  - gitleaks secret scan
  - dependency audit in non-blocking mode for visibility

## Security Notes

- Do not commit real API keys, service credentials, or `.env` secrets.
- Keep Firebase Web API keys out of tracked env files when possible; use local overrides or CI secrets.
- Use Secret Manager bindings for backend runtime secrets in Cloud Run.
- Rotate any key if exposed.

## Documentation

- Local dev runbook: `docs/LOCAL_DEV.md`
- Staging deploy runbook: `docs/STAGING_DEPLOY.md`
- API/Frontend contract map: `docs/dev/contract_map.md`
- Security details: `docs/security.md`
- Privacy details: `docs/privacy.md`

## Contact

- Demo and product contact: `purvansh95b@gmail.com`

## License

GNU AGPL-3.0. See `LICENSE`.
