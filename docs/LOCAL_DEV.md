# Local Development (Windows PowerShell)

This guide runs AIRS fully local (frontend + backend + Firebase Auth emulator) without touching production.

## 1. Prerequisites

- Python 3.11+
- Node.js 20+
- Firebase CLI (`npm i -g firebase-tools`)
- `gcloud` (optional for deploy workflows)

## 2. Create Backend Local Env

From repo root:

```powershell
Copy-Item .env.dev.example .env.dev
```

Required values in `.env.dev`:

```env
ENV=local
DATABASE_URL=sqlite:///./airs_dev.db
CORS_ALLOW_ORIGINS=http://localhost:5173
FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
```

## 3. Run DB Migrations

```powershell
$env:ENV="local"
py -3 -m alembic upgrade head
```

## 4. Frontend Env

Use `frontend/.env.development`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_PROJECT_ID=gen-lang-client-0384513977
```

`frontend/src/lib/firebase.ts` is configured to use Auth Emulator only in development mode.

## 5. Run the Stack

Option A (single command):

```powershell
make dev
```

Option B (3 terminals):

Terminal 1 (backend):
```powershell
$env:ENV="local"
py -3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (frontend):
```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Terminal 3 (Firebase Auth emulator):
```powershell
firebase emulators:start --only auth --project demo-airs
```

## 6. Validate Contracts Quickly

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/health/cors
curl http://localhost:8000/health/llm
```

Expected:
- `/health` => `{"status":"ok"}`
- `/health/cors` includes `http://localhost:5173`
- `/health/llm` returns `llm_enabled`, `provider/model`, and `runtime_check`
