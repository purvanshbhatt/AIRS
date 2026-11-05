# Deployment Reality

| Environment | URL | Firebase Site | Hosting Target | Cloud Run API | Git/Build Source | Status |
| ----------- | --- | ------------- | -------------- | ------------- | ---------------- | ------ |
| Local       | `http://localhost:5173` | N/A | N/A | Local / Staging API | `frontend/dist` (Dev) | Active |
| Staging     | `https://resilai-staging.web.app` | `resilai-staging` | `resilai-staging` | `https://airs-api-staging-227825933697.us-central1.run.app` | `frontend/dist-staging` | Active |
| Production  | `https://resilai.org` | `resilai-marketing` | `marketing` | `https://airs-api-227825933697.us-central1.run.app` | `frontend/dist-production` | Active |

## Frontend Config
- Firebase project: `gen-lang-client-0384513977`
- Staging Firebase Site: `resilai-staging`
- Staging Firebase Target: `resilai-staging`
- Production Firebase Site: `resilai-marketing`
- Environments: `.env.staging`, `.env.production`
- Output directories: `frontend/dist-staging`, `frontend/dist-production`, `frontend/dist-demo`

## Backend Config
- GCP Project ID: `gen-lang-client-0384513977`
- Cloud Run Staging: `airs-api-staging-227825933697.us-central1.run.app`
- Cloud Run Prod: `airs-api-227825933697.us-central1.run.app`
- Auth Configuration: Handled via Firebase Auth matching `gen-lang-client-0384513977`
- Persistence: Firestore (SQLite in-memory cache)
- Env files: `gcp/env.staging.yaml`, `gcp/env.prod.yaml`
