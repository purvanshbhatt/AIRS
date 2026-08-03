# ResilAI — REST API Overview

## 📡 Base URLs

* **Production**: `https://airs-api-227825933697.us-central1.run.app`
* **Staging**: `https://airs-api-staging-knu3wsxymq-uc.a.run.app`

---

## 🔑 Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check |
| `GET` | `/api/v1/readiness` | Returns deterministic readiness scores & ledger |
| `GET` | `/api/v1/evidence` | Retrieves normalized telemetry evidence graph |
| `GET` | `/api/v1/decisions` | Returns decision drift analysis |
| `POST` | `/api/v1/reports/board-story` | Generates executive board narrative report |
| `GET` | `/api/v3/clinic/readiness` | Real-time Clinic Readiness v3.0 state |
