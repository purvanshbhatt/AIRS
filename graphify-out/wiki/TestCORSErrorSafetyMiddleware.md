# TestCORSErrorSafetyMiddleware

> 4 nodes · cohesion 0.50

## Key Concepts

- **TestCORSErrorSafetyMiddleware** (5 connections) — `tests/test_cors.py`
- **.test_options_preflight_custom_headers()** (2 connections) — `tests/test_cors.py`
- **.test_options_preflight_trusted_origin_auto_allowed()** (2 connections) — `tests/test_cors.py`
- **Tests for CORSErrorSafetyMiddleware preflight and headers.** (1 connections) — `tests/test_cors.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [is_localhost_origin](is_localhost_origin.md) (1 shared connections)
- [middleware.py](middleware.py.md) (1 shared connections)

## Source Files

- `tests/test_cors.py`

## Audit Trail

- EXTRACTED: 4 (57%)
- INFERRED: 3 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*