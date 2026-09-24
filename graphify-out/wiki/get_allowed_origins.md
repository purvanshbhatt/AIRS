# get_allowed_origins

> 24 nodes · cohesion 0.13

## Key Concepts

- **get_allowed_origins()** (24 connections) — `app/core/cors.py`
- **TestGetAllowedOrigins** (16 connections) — `tests/test_cors.py`
- **.test_dev_mode_auto_adds_localhost()** (3 connections) — `tests/test_cors.py`
- **.test_dev_mode_empty_still_has_localhost()** (3 connections) — `tests/test_cors.py`
- **.test_env_var_not_set_dev_mode()** (3 connections) — `tests/test_cors.py`
- **.test_prod_mode_no_auto_localhost()** (3 connections) — `tests/test_cors.py`
- **.test_prod_mode_rejects_localhost()** (3 connections) — `tests/test_cors.py`
- **.test_prod_mode_rejects_non_https()** (3 connections) — `tests/test_cors.py`
- **.test_deduplication()** (2 connections) — `tests/test_cors.py`
- **.test_invalid_origins_filtered()** (2 connections) — `tests/test_cors.py`
- **.test_multiple_origins_comma_separated()** (2 connections) — `tests/test_cors.py`
- **.test_single_origin()** (2 connections) — `tests/test_cors.py`
- **.test_trailing_slash_removed()** (2 connections) — `tests/test_cors.py`
- **.test_whitespace_trimmed()** (2 connections) — `tests/test_cors.py`
- **.test_wildcard_blocked_in_production()** (2 connections) — `tests/test_cors.py`
- **.test_wildcard_in_development()** (2 connections) — `tests/test_cors.py`
- **Get the list of allowed CORS origins with environment-aware behavior. Reads…** (1 connections) — `app/core/cors.py`
- **Tests for get_allowed_origins function.** (1 connections) — `tests/test_cors.py`
- **In dev mode, localhost:3000 and localhost:5173 are auto-added.** (1 connections) — `tests/test_cors.py`
- **In dev mode with no CORS_ALLOW_ORIGINS, localhost is still added.** (1 connections) — `tests/test_cors.py`
- **In prod mode, localhost origins are rejected.** (1 connections) — `tests/test_cors.py`
- **In prod mode, non-HTTPS origins are rejected.** (1 connections) — `tests/test_cors.py`
- **In prod mode, localhost is NOT auto-added.** (1 connections) — `tests/test_cors.py`
- **When env var not set in dev mode, still gets localhost.** (1 connections) — `tests/test_cors.py`

## Relationships

- [is_localhost_origin](is_localhost_origin.md) (4 shared connections)
- [health.py](health.py.md) (2 shared connections)
- [main.py](main.py.md) (2 shared connections)
- [.cors_origins_list](cors_origins_list.md) (1 shared connections)
- [validate_origin](validate_origin.md) (1 shared connections)

## Source Files

- `app/core/cors.py`
- `tests/test_cors.py`

## Audit Trail

- EXTRACTED: 46 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*