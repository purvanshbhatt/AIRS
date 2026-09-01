# Design Partner Deployment Reality

## LOCAL
**Frontend:** http://localhost:5173 (Vite Dev Server)
**Backend:** http://localhost:8000 (FastAPI Uvicorn)
**API Base URL:** http://localhost:8080 (Configured in `.env.development`)

## STAGING
**Frontend:** https://resilai-staging.web.app (Firebase Hosting)
**Backend:** https://airs-api-staging-227825933697.us-central1.run.app (Cloud Run)
**API Base URL:** https://airs-api-staging-227825933697.us-central1.run.app (Configured in `.env.staging`)
**Revision:** Latest active

## PRODUCTION
**Frontend:** https://resilai.org (Firebase Hosting)
**Backend:** https://api.resilai.org (Cloud Run via Domain Mapping)
**API Base URL:** https://api.resilai.org (Configured in `.env.production`)
**Revision:** Latest active

## Deployment mismatch:
**Yes**

**exact cause:**
In the LOCAL environment, the frontend's `VITE_API_BASE_URL` in `.env.development` is configured as `http://localhost:8080`, but the FastAPI backend natively runs on port `8000`. This completely severs local frontend-backend connectivity, forcing the frontend to rely on mock data or fail.
