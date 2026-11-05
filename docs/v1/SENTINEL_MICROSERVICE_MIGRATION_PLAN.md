# Sentinel Microservice Migration Plan

## Objective
Convert Sentinel from a deeply coupled module into a completely isolated microservice. Sentinel will operate with its own API namespace, environment variables, database schema, and deployment configuration.

## Target Architecture

```
[Splunk Enterprise / Data Sources]
      │ (Webhook HTTP POST)
      ▼
┌─────────────────────────────────────────────────────┐
│  resilai-sentinel-staging (Standalone Service)      │
│                                                     │
│  [API Endpoint: /api/sentinel/webhooks/splunk]      │
│  [API Endpoint: /api/sentinel/twin]                 │
│                                                     │
│  1. Evidence Engine                                 │
│  2. Digital Twin Simulator                          │
│  3. Board Intelligence (Gemini)                     │
│                                                     │
│  [Local DB: SQLite / Sentinel Schema]               │
└──────────────────────┬──────────────────────────────┘
                       │ 
                       │ (Internal HTTP API: Bearer Token)
                       ▼
┌─────────────────────────────────────────────────────┐
│  resilai-api (Core Platform)                        │
│                                                     │
│  [API Endpoint: /api/v1/assessments/simulate]       │
│  [API Endpoint: /api/v1/rubric/mapping]             │
│                                                     │
│  1. AIRS Scoring Engine                             │
│  2. Rubric Mapping                                  │
│  3. Production Database (Assessment Mutations)      │
└─────────────────────────────────────────────────────┘
```

## Migration Steps

### Step 1: Establish Sentinel Boundaries
1. **Database:** Create `app/sentinel/db/database.py` utilizing a separate connection (e.g. `sentinel_dev.db`).
2. **Configuration:** Create `app/sentinel/core/config.py` using a prefix-isolated `.env` parser (e.g., `SENTINEL_DB_URL`, `SENTINEL_GEMINI_KEY`).
3. **App Initialization:** Create `app/sentinel/main.py` allowing Sentinel to be booted via `uvicorn app.sentinel.main:app` instead of sharing the global `app.main.py`.

### Step 2: Decouple Data Models
1. Sentinel must not touch `app.models`. It must establish:
   - `SentinelTelemetryEvent`
   - `TelemetryEvidence` (moved to `sentinel/db/models.py`)
   - `SentinelSimulation` (moved to `sentinel/db/models.py`)

### Step 3: API Client Implementation
1. Create `app/sentinel/adapters/airs_client.py`.
2. This HTTP client will perform GET/POST requests against the Core AIRS API using an internal Service Account Token (`SENTINEL_AIRS_API_KEY`).
3. Replace `calculate_scores()` in `app/sentinel/twin/engine.py` with `AirsClient.simulate_assessment_score()`.
4. Replace `get_domain_nist_function()` in `app/sentinel/evidence/engine.py` with `AirsClient.resolve_framework_mapping()`.

### Step 4: Routing Refactor
1. Relocate `app/api/routes/sentinel.py` to `app/sentinel/api/routes.py`.
2. Refactor Sentinel to use its local `get_db` dependency instead of the global platform `get_db`.

### Step 5: Verification
Run a regression loop inside the `resilai-sentinel-staging` container:
- Confirm `Splunk` telemetry arrives.
- Confirm `AirsClient` successfully asks Core to score a hypothetical Twin scenario.
- Confirm production database (`airs_dev.db`) log sizes remain unchanged (Zero Mutation Rule).
