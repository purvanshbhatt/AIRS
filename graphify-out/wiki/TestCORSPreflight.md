# TestCORSPreflight

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestCORSPreflight** (4 connections) — `tests/test_backend_contract_verification.py`
- **.test_cors_preflight_localhost()** (2 connections) — `tests/test_backend_contract_verification.py`
- **.test_cors_preflight_staging_origin()** (2 connections) — `tests/test_backend_contract_verification.py`
- **CORS preflight must respond correctly for all allowed origins.** (1 connections) — `tests/test_backend_contract_verification.py`
- **OPTIONS preflight from staging.resilai.org → 204 with CORS headers.** (1 connections) — `tests/test_backend_contract_verification.py`
- **OPTIONS from localhost (dev) should succeed in local/staging ENV.** (1 connections) — `tests/test_backend_contract_verification.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_backend_contract_verification.py`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*