# ResilAI
AI Incident Readiness Platform

## Problem
Security teams monitor alerts but cannot easily measure actual incident readiness.

Most organizations can report event volume, ticket counts, or tool coverage, but they still struggle to answer executive questions such as:
- Are we actually prepared to respond to an incident?
- Which control gaps create the highest operational risk?
- How do we explain readiness in business language for leadership and investors?

## Solution
ResilAI combines deterministic governance scoring with AI-generated executive risk narratives.

The platform separates hard, rules-based readiness computation from natural-language explanation so that risk posture is measurable, auditable, and explainable.

## Key Features
- Deterministic readiness scoring
- NIST CSF 2.0 mapping
- AI-generated executive summaries using Gemini
- Cloud-native architecture

## Architecture
ResilAI is built as a layered cloud-native system:
- Frontend: React + Vite dashboard for assessments, posture visualization, and reporting.
- Backend: FastAPI API for organization, assessment, scoring, and reporting workflows.
- Governance scoring engine: deterministic weighted scoring with explicit rubric and controls.
- AI narrative layer: Gemini Flash generates executive-friendly risk narratives and summaries.
- Cloud deployment: Google Cloud Run services with Firestore-backed persistence.

See `ARCHITECTURE.md` for full design details.

## Demo Video
YouTube demo (placeholder):
- https://www.youtube.com/watch?v=YOUR_DEMO_VIDEO_ID

## Tech Stack
- React
- FastAPI
- Gemini Flash
- Google Cloud Run
- Firestore

## Future Roadmap
- SIEM integrations
- Automated incident simulations
- Enterprise RBAC
