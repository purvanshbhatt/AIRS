# ResilAI Current State

Version: 0.4.0-beta

Current Goal:
Trust & Verification Release

Core Architecture:
- Frontend: React (18.3.1) + Vite (6.4.1) + TypeScript (5.5.3) + TailwindCSS (4.1.18)
- Backend: FastAPI (0.115+) (Python 3.11+) + SQLAlchemy (2.0+)
- Database: Firestore (Primary Persistence, via firebase-admin 6.5+) + SQLite (In-Memory Cache)
- Hosting: Firebase Hosting (Frontend), Google Cloud Run (Backend)
- LLM: Gemini 3 Flash (via google-genai 1.0+). Some subsystems use Gemini 2.5 Flash.

Rules:
- LLM never calculates scores. Scoring remains deterministic.
- Gemini is only used to generate narratives and unstructured text extraction.
- Verification engine uses telemetry from connected systems (Wazuh, Splunk, etc.).
- Microsoft integrations prioritized for the enterprise market.

Current Workstreams:

[IN PROGRESS]
1. Technology Intelligence & Auto-Discovery
Owner: Backend Agent
Status: Implemented async background sync

2. Trust Dashboard
Owner: Frontend Agent
Status: Dashboard lists assessments & scores

3. Assessment Lifecycle
Owner: Backend Agent / Frontend Agent
Status: Archive functionality recently implemented

Dependencies:
- Trust Dashboard requires: `getAssessments` API
- Discovery Engine requires: Wazuh, Splunk API configurations

