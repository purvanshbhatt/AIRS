# Backend State

Core Layer: FastAPI (0.115+)
ORM: SQLAlchemy (2.0.36+)
Database Driver: psycopg2-binary (2.9.9+), firebase-admin (6.5.0+)
Main Router: `app/main.py` -> `app/api/`

Recent Changes:
- Made tech stack discovery asynchronous to prevent timeouts.
- Added Assessment Archive logic via `AssessmentService.archive` and `DELETE` endpoint.

Next Tasks:
- Expand verification API for integrations.
