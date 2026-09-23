# TestHealthEndpoints

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestHealthEndpoints** (5 connections) — `tests/test_backend_contract_verification.py`
- **.test_health_alive()** (2 connections) — `tests/test_backend_contract_verification.py`
- **.test_health_cors_config()** (2 connections) — `tests/test_backend_contract_verification.py`
- **.test_health_llm_no_side_effects()** (2 connections) — `tests/test_backend_contract_verification.py`
- **Verify operational health endpoints distinguish alive vs. ready.** (1 connections) — `tests/test_backend_contract_verification.py`
- **GET /health → 200 with status=ok.** (1 connections) — `tests/test_backend_contract_verification.py`
- **GET /health/cors → 200, returns env and allowed_origins.** (1 connections) — `tests/test_backend_contract_verification.py`
- **GET /health/llm → 200, does NOT call LLM, returns config only.** (1 connections) — `tests/test_backend_contract_verification.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_backend_contract_verification.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*