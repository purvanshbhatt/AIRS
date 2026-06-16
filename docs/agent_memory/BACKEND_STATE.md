# Backend State

Core Layer: FastAPI
ORM: SQLAlchemy
Main Router: `app/main.py` -> `app/api/`

Recent Changes:
- Made tech stack discovery asynchronous to prevent timeouts.
- Added Assessment Archive logic via `AssessmentService.archive` and `DELETE` endpoint.

Next Tasks:
- Expand verification API for integrations.
