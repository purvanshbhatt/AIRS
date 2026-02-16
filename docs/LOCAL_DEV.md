# ResilAI Local Development (Windows PowerShell)

This runbook sets up a fully local ResilAI stack that does not touch production resources.

## 1. Prerequisites

- Python 3.11+
- Node.js 20+
- Firebase CLI (`npm i -g firebase-tools`)
- Git Bash or WSL (optional, for bash deploy scripts)

## 2. Backend Environment

Create local backend env file from root:

```powershell
Copy-Item .env.dev.example .env.dev
```

Minimum required values in `.env.dev`:

```env
ENV=local
DATABASE_URL=sqlite:///./airs_dev.db
CORS_ALLOW_ORIGINS=http://localhost:5173
FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
```

Recommended local options:

```env
AIRS_USE_LLM=false
DEMO_MODE=true
AUTH_REQUIRED=false
```

## 3. Backend Install and Migrate

```powershell
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
$env:ENV="local"
py -3 -m alembic upgrade head
```

## 4. Frontend Environment

Create or verify `frontend/.env.development`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME="ResilAI (Local)"
VITE_FIREBASE_PROJECT_ID=gen-lang-client-0384513977
VITE_FIREBASE_AUTH_DOMAIN=gen-lang-client-0384513977.firebaseapp.com
VITE_FIREBASE_API_KEY=REPLACE_WITH_FIREBASE_WEB_API_KEY
VITE_FIREBASE_AUTH_EMULATOR=http://127.0.0.1:9099
```

Important:
- In development mode, frontend auth uses Firebase Auth Emulator from `frontend/src/lib/firebase.ts`.
- In staging/production mode, auth uses real Firebase config.

## 5. Run All Services

Use three terminals.

Terminal A (backend):

```powershell
$env:ENV="local"
py -3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal B (frontend):

```powershell
cd frontend
npm ci
npm run dev -- --host 0.0.0.0 --port 5173
```

Terminal C (auth emulator):

```powershell
firebase emulators:start --only auth --project demo-airs
```

## 6. Quick Validation

Backend checks:

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/health/cors
curl http://localhost:8000/health/llm
curl http://localhost:8000/health/system
```

Expected outcomes:
- `/health` returns status ok
- `/health/cors` contains `http://localhost:5173`
- `/health/system` returns version, environment, llm_enabled, demo_mode

Frontend checks:
- Open `http://localhost:5173`
- Confirm authentication errors are not shown for placeholder keys when emulator is running
- Confirm theme toggle switches light/system/dark

## 7. Common Issues

1. `auth/api-key-not-valid`
- Cause: placeholder `VITE_FIREBASE_API_KEY` used outside development emulator flow.
- Fix: ensure mode is `development` and emulator is running, or supply real staging/prod web API key.

2. `auth/unauthorized-domain`
- Cause: missing domain in Firebase auth allowed domains.
- Fix: add local/staging hostnames in Firebase Auth settings.

3. Backend startup import errors (e.g., `email-validator`)
- Fix:

```powershell
py -3 -m pip install -r requirements.txt
```

## 8. Local-Only Safety Rules

- Never commit `.env.dev`.
- Never commit `.env.*.local` files containing real API keys.
- Keep production API base URLs out of `.env.development`.
- Use local SQLite for development migrations and testing.
