# health.py

> 25 nodes · cohesion 0.12

## Key Concepts

- **health.py** (19 connections) — `app/api/routes/health.py`
- **get_product_info()** (8 connections) — `app/core/product.py`
- **cors_health()** (7 connections) — `app/api/routes/health.py`
- **health_check()** (6 connections) — `app/api/routes/health.py`
- **product.py** (6 connections) — `app/core/product.py`
- **HealthResponse** (5 connections) — `app/api/routes/health.py`
- **CORSHealthResponse** (4 connections) — `app/api/routes/health.py`
- **llm_health()** (4 connections) — `app/api/routes/health.py`
- **LLMHealthResponse** (4 connections) — `app/api/routes/health.py`
- **get** (4 connections)
- **system_health()** (4 connections) — `app/api/routes/health.py`
- **ProductInfo** (3 connections) — `app/api/routes/health.py`
- **SystemHealthResponse** (3 connections) — `app/api/routes/health.py`
- **_resolve_git_sha()** (3 connections) — `app/core/product.py`
- **Request** (1 connections)
- **Health check endpoint for Cloud Run and load balancer probes.** (1 connections) — `app/api/routes/health.py`
- **LLM status endpoint. Returns the current LLM configuration for verification and…** (1 connections) — `app/api/routes/health.py`
- **CORS diagnostic endpoint. Returns the current CORS configuration for…** (1 connections) — `app/api/routes/health.py`
- **Health check response with multi-cloud observability.** (1 connections) — `app/api/routes/health.py`
- **LLM status response for verification and demo confidence.** (1 connections) — `app/api/routes/health.py`
- **CORS configuration diagnostic response.** (1 connections) — `app/api/routes/health.py`
- **Health check endpoint. Returns a status for load balancer health probes across…** (1 connections) — `app/api/routes/health.py`
- **Product metadata helpers.** (1 connections) — `app/core/product.py`
- **Resolve a short git SHA from env or local repository, if available.** (1 connections) — `app/core/product.py`
- **Return product metadata for API responses.** (1 connections) — `app/core/product.py`

## Relationships

- [main.py](main.py.md) (5 shared connections)
- [BaseModel](BaseModel.md) (5 shared connections)
- [is_localhost_origin](is_localhost_origin.md) (3 shared connections)
- [get_allowed_origins](get_allowed_origins.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [get_rubric](get_rubric.md) (1 shared connections)

## Source Files

- `app/api/routes/health.py`
- `app/core/product.py`

## Audit Trail

- EXTRACTED: 55 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*