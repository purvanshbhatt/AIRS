# Sentinel Production Readiness Guide

This document serves as the definitive reference for deploying the ResilAI Sentinel module to Staging and Production environments. It outlines all architectural additions, dependencies, deployment steps, and rollback procedures.

---

## 1. Architectural Surface Area

### New Database Tables
Sentinel introduces three new tables. **CRITICAL:** Sentinel tables do not mutate `assessments`, `scores`, or `answers`.
* `telemetry_events` - Stores raw, normalized events ingested from integrations (e.g., Splunk).
* `telemetry_evidence` - Stores deterministic evidence generated from telemetry, mapped to `app.core.rubric` frameworks.
* `sentinel_simulations` - Stores historical records of Digital Twin scenario executions and their deep-copied assessment state.

### New API Routes
All routes are prefixed under `/api/sentinel/`.
* `GET /status` - Health check and telemetry processing status.
* `GET /telemetry` - Lists recent raw telemetry events.
* `GET /evidence` - Lists deterministic evidence mapped from telemetry.
* `POST /twin` - Executes a zero-mutation Digital Twin simulation (e.g., Ransomware).
* `GET /simulations` - Lists historical simulation runs.
* `GET /reports/{simulation_id}` - Generates the Gemini-powered Board Intelligence report for a specific simulation.
* `POST /integrations/splunk` - Triggers an on-demand Splunk ingestion and evidence generation cycle.

---

## 2. Environment Variables & External Dependencies

### Environment Variables Required
```env
# Splunk Integration
SPLUNK_HOST=your-splunk-instance.com
SPLUNK_PORT=8089
SPLUNK_TOKEN=your-splunk-api-token

# Gemini / Board Intelligence
GOOGLE_API_KEY=your-gemini-api-key

# Database
DATABASE_URL=postgresql://user:password@host/dbname
```

### External Dependencies
* **Splunk Enterprise** (or Splunk Cloud) - Source of truth for operational telemetry.
* **Google Gemini API** (`google-genai` package) - Powers the Board Intelligence report generation.
* **SQLAlchemy & Alembic** - For database ORM and migrations.

---

## 3. Deployment Procedure

### Step 1: Database Migration
Before deploying code, ensure the new Sentinel tables are created.
If an Alembic migration has not been generated for the staging/production database yet, run:
```bash
alembic revision --autogenerate -m "Add Sentinel module tables: telemetry_events, telemetry_evidence, sentinel_simulations"
alembic upgrade head
```

### Step 2: Deploy Backend & API
Deploy the Python FastAPI application via your standard CI/CD pipeline (e.g., Google Cloud Run).
Ensure the `SPLUNK_*` and `GOOGLE_API_KEY` environment variables are securely injected into the container environment.

### Step 3: Splunk MCP Verification
Ensure the backend has network line-of-sight to the Splunk instance. Fire a test event in Splunk and monitor the backend logs for ingestion success.

---

## 4. Rollback Procedure

If the Sentinel deployment causes degradation to the core ResilAI scoring engine or frontend, execute the following emergency rollback:

### Code Rollback
Revert the Cloud Run deployment to the previous immutable image hash.
```bash
# Example GCP Command
gcloud run services update resilai-api --image=gcr.io/project/resilai-api:previous-hash
```

### Database Rollback (If Necessary)
Sentinel tables are architecturally isolated. Dropping them will not affect core ResilAI data.
```bash
alembic downgrade -1
```
*(Alternatively, manually drop `sentinel_simulations`, `telemetry_evidence`, and `telemetry_events` if Alembic downgrade fails).*

---

## 5. Monitoring & SLAs

### Health Checks
Monitor the `GET /api/sentinel/status` endpoint. A healthy response should return `200 OK` and `"telemetry_health": "healthy"`.

### Performance SLAs
* **Telemetry Ingestion:** 1,000 events must be ingested and processed in under `5.0 seconds`.
* **Digital Twin Simulation:** Zero mutation of actual assessment records. Time to simulate must remain under `2.0 seconds`.

### Alerting Triggers
Set up monitoring alerts (e.g., Datadog, GCP Cloud Monitoring) for:
* `5xx` errors on `/api/sentinel/twin`
* Exceptions raised by `app.sentinel.board_intelligence.generator` (Gemini API rate limits or failures).
* High latency (>5s) on `/api/sentinel/integrations/splunk`.
