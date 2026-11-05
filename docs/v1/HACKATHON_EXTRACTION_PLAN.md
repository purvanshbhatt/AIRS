# Sentinel Hackathon Extraction Plan
**Target Standalone Repository**: `resilai-sentinel-splunk`

## 1. Component Inventory & Categorization

| Component Path | Function | Status | Justification |
| -------------- | -------- | ------ | ------------- |
| `app/integrations/splunk/` | Splunk API client, models, and webhook ingestion | **KEEP** | Core driver of the Agentic Operations submission. |
| `app/sentinel/evidence/` | Telemetry mapping, evidence generation, Enum structures | **KEEP** | Essential for translating raw signals into deterministic control states. |
| `app/sentinel/board_intelligence/` | Gemini-powered executive report generation | **KEEP** | Primary "Agentic" output mechanism for the hackathon showcase. |
| `app/api/routes/sentinel.py` | FastAPI endpoints for ingestion and reports | **KEEP** | Need the API surface to receive webhooks and serve UI. |
| `app/sentinel/twin/` | Ransomware/Simulation Digital Twin Engine | **REPLACE** | Relies entirely on the AIRS core scoring engine. Moving this requires duplicating scoring math. Replace with API calls to Core. |
| `app/sentinel/readiness/` | Evidence-to-Framework mapping | **KEEP** | Necessary for mapping evidence to generic question IDs. |
| `scripts/demo_sentinel.py` | Hackathon Demo Flow script | **KEEP** | Essential for judging/submission. |

---

## 2. Dependency Chain & Source Mapping

### A. Splunk Ingestion
* **Source:** `app/integrations/splunk/service.py`, `app/integrations/splunk/client.py`
* **Required Imports:** `httpx` (or `requests`), FastAPI `BackgroundTasks`.
* **External Services:** Splunk Enterprise / Splunk MCP.
* **Migration Requirements:** Can be migrated cleanly. Will need a localized `db/database.py` or SQLite equivalent if moving to a microservice.

### B. Evidence Generation
* **Source:** `app/sentinel/evidence/engine.py`
* **Required Imports:** `app.core.rubric.get_rubric()` 
* **Breakage Risk:** Requires the core `rubric.py` JSON/dict structures to resolve frameworks.
* **Migration Requirements:** Must either bundle `app/core/rubric.py` + `rubric.json`, or query the core platform for framework details.

### C. Digital Twin Simulation
* **Source:** `app/sentinel/twin/engine.py`
* **Required Imports:** `app.services.scoring.calculate_scores`, `app.models.assessment.*`
* **Breakage Risk:** **HIGH.** The Digital Twin requires the full `Assessment` ORM object and the core `calculate_scores()` logic. If extracted natively, you violate the architectural principle *"Do not create duplicate scoring engines."*
* **Migration Requirements:** Must be converted from local function calls to HTTP REST calls (e.g., `POST https://api.resilai.com/v1/assessments/{id}/simulate`).

### D. Board Intelligence
* **Source:** `app/sentinel/board_intelligence/generator.py`
* **Required Imports:** `google-genai`
* **External Services:** Google Gemini API (Flash 2.5).
* **Migration Requirements:** Clean extraction. Purely deterministic template generation.

---

## 3. Structural Breakages (What Fails on Copy)

If the `app/sentinel` folder is naively copied to `resilai-sentinel-splunk`:
1. **`ModuleNotFoundError: No module named 'app.models.telemetry_event'`**: Standalone repo lacks the core SQLAlchemy models.
2. **`ModuleNotFoundError: No module named 'app.services.scoring'`**: Cannot run Digital Twin simulations without copying the massive, complex scoring engine.
3. **`ModuleNotFoundError: No module named 'app.core.rubric'`**: Cannot map evidence to framework names.
4. **Database Context (`Session`)**: The standalone repo will not have access to the primary AIRS PostgreSQL database unless explicitly configured (which violates microservice data isolation).

---

## 4. Recommended Minimum Code Set (Standalone Submission)

To cleanly separate Sentinel into `resilai-sentinel-splunk` while preserving architectural integrity, we recommend building an **Event-Driven Microservice** instead of a monolithic clone.

### The Minimum Viable Standalone Stack:

1. **FastAPI Ingestion Layer (`main.py`)**
   * Endpoint to receive Splunk webhooks (`/webhooks/splunk`).
   * Lightweight SQLite/PostgreSQL to queue events.

2. **Splunk Integration Module**
   * Splunk API client to poll/query for historical events.
   * Telemetry normalizer to produce unified Event schemas.

3. **Evidence Engine (`engine.py`)**
   * Maps telemetry to `EvidenceType` enums.
   * Maps `EvidenceType` to Generic Control IDs (e.g., `rs_03`).

4. **Integration Client (`resilai_client.py`)** -> *[REPLACES TWIN ENGINE]*
   * Instead of calculating the readiness drop locally, the standalone Sentinel uses an HTTP client to `POST` the evidence directly to the Core AIRS Platform's Digital Twin API.
   * *The core platform does the math and returns the dropped score.*

5. **Board Intelligence Engine (`generator.py`)**
   * Takes the resulting score drop from the Core API.
   * Uses Gemini to generate the executive PDF/JSON.

**Conclusion:** 
By replacing local imports with HTTP API requests, the `resilai-sentinel-splunk` repository becomes a true, decoupled "Agentic Operations" agent. It acts as an intelligent intermediary between the customer's Splunk instance, Google Gemini, and the ResilAI core engine.
