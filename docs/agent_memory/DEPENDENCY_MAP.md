# Dependency Map

**Verification Engine**
Depends On:
- Telemetry Connectors (Wazuh, Splunk APIs)
- DB Models (Control Evidence)
Provides:
- Verification Status (Verified, Unverified)
Used By:
- Assessment Scoring Engine
- Trust Dashboard

---

**Assessment Scoring Engine**
Depends On:
- Verification Engine (telemetry status)
- Base Framework Rules (deterministic matrix)
Provides:
- Overall Audit Confidence Score
Used By:
- Narrative Generator
- Trust Dashboard

---

**Narrative Generator (Gemini)**
Depends On:
- Assessment Scoring Engine Output
- Verification Engine Evidences
Provides:
- Explanations, Board-Level Summaries
Used By:
- Reports API
- Frontend Modals

---

**Trust Dashboard (UI)**
Depends On:
- `getAssessments` API
- `getVerification` API
Provides:
- User Interface
Used By:
- End User / CISO
