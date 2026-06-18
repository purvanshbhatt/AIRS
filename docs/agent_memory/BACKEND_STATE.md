# Backend State

Core Layer: FastAPI (0.115+)
ORM: SQLAlchemy (2.0.36+)
Database Driver: psycopg2-binary (2.9.9+), firebase-admin (6.5.0+)
Main Router: `app/main.py` -> `app/api/`

Recent Changes:
- Made tech stack discovery asynchronous to prevent timeouts.
- Added Assessment Archive logic via `AssessmentService.archive` and `DELETE` endpoint.
- Added `CORSErrorSafetyMiddleware` to guarantee CORS headers on ALL responses including 5xx errors and Cloud Run timeouts.
- Expanded `CORS_ALLOW_ORIGINS` in `gcp/env.prod.yaml` with all Firebase Hosting domains.

Next Tasks:
- Expand verification API for integrations.
