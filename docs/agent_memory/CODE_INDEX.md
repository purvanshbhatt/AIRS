# Core Service Map

## Assessment Lifecycle
`app/services/assessment.py`
Purpose:
Manages the CRUD operations and state transitions of the core Audit Confidence assessments.
Dependencies:
`scoring.py`, `firestore_sync`, `database.py`
Do Not Modify:
Schema relationships without corresponding alembic migrations.

---

## Deterministic Scoring
`app/services/scoring.py`
Purpose:
Calculates numerical readiness and compliance scores completely deterministically.
Dependencies:
`findings.py`, `telemetry.py`
Do Not Modify:
LLM MUST NEVER BE ALLOWED TO GENERATE SCORES IN THIS MODULE. Scoring is strictly rule-based.

---

## Verification Engine
`app/services/verification.py`
Purpose:
Verifies assessment answers against hard telemetry from connected systems (e.g. Wazuh, Splunk).
Dependencies:
`telemetry_ingestion.py`, `control_verification.py`
Important:
Verification replaces self-attestation. Prioritize evidence.

---

## Technology Intelligence (Auto-Discovery)
`app/services/discovery/orchestrator.py`
Purpose:
Synchronously or asynchronously builds the tech stack registry by scanning environment telemetry.
Dependencies:
`wazuh_client.py`, `splunk.py`

---

## Narrative Generation
`app/services/ai_narrative.py` & `app/services/intelligence.py`
Purpose:
Gemini narrative generation for explaining findings and generating board-level reports.
Models:
gemini-3-flash
Dependencies:
score snapshots, findings
Important:
No scoring logic allowed here. Only text analysis and summarization.

---

## Trust Dashboard
`frontend/src/pages/Dashboard.tsx`
Purpose:
Executive view of Audit Confidence and Verification Status.
Dependencies:
`frontend/src/api.ts`
