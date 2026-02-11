# AIRS Staging + Safe Local Auth

This project has a **production demo** already deployed:

- Frontend: `https://gen-lang-client-0384513977.web.app`
- API: `https://airs-api-227825933697.us-central1.run.app`

This guide helps you create a **separate staging environment** (Firebase + Cloud Run) and run locally without polluting production users.

---

## Option 1 (Recommended): Local Firebase Auth Emulator

This keeps **all users local** (no writes to production/staging Firebase Auth).

### 1) Install Firebase CLI

Follow Firebase CLI install docs, then from repo root run:

```bash
firebase --version
```

### 2) Start only the Auth emulator

From repo root:

```bash
firebase emulators:start --only auth
```

By default this repo config runs:

- Auth emulator: `http://localhost:9099`
- Emulator UI: `http://localhost:4000`

### 3) Point the frontend to emulator + local API

Copy the example env file:

```bash
cp frontend/.env.development.local.example frontend/.env.development.local
```

Then uncomment the **Option A** emulator block in `frontend/.env.development.local`.

### 4) Run locally

Backend:

```bash
make dev
```

Frontend (separate terminal):

```bash
make frontend-dev
```

---

## Option 2: Separate Firebase Project for Staging

Use this when you want a staging site that behaves like production, but **does not touch production users**.

### 1) Create a new Firebase project

In Firebase Console:

1. Create project (example ID: `airs-staging-xxxx`)
2. Enable **Authentication** providers you need (Google, Email/Password, etc.)
3. Create a **Web App** and copy its config values

### 2) Create staging frontend env

Copy:

```bash
cp frontend/.env.staging.example frontend/.env.staging
```

Fill in:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_API_BASE_URL` (your staging Cloud Run URL)

### 3) Deploy hosting to staging (does NOT affect prod)

Build with staging mode:

```bash
cd frontend
npm run build:staging
cd ..
```

Deploy to your staging project:

```bash
firebase deploy --only hosting --project <your-staging-project-id>
```

---

## Notes

- Avoid creating `frontend/.env.local` unless you really mean to override **all** modes (including production builds).
- For staging, use `vite build --mode staging` (or `npm run build:staging`) so it never reads production values from `frontend/.env.production`.
