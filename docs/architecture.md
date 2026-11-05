# Architecture Overview

ResilAI architecture is API-first with a decoupled frontend and backend.

## Stack

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + SQLAlchemy + Alembic
- Auth: Firebase Auth
- Hosting: Firebase Hosting + Google Cloud Run
- AI Narrative: Gemini via `google-genai`

## Data Flow

1. User completes assessment in frontend
2. Backend stores answers and computes deterministic score
3. Findings map to MITRE/CIS/OWASP references
4. Narrative and executive artifacts are generated
5. Integrations consume data via API keys or webhooks

## Trust Boundaries

- Browser <-> API over HTTPS
- Firebase token-based user identity
- Backend authorization and org scoping
- Secrets injected via environment or secret manager

For full details, see `../ARCHITECTURE.md`.
