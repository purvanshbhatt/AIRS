# is_localhost_origin

> 24 nodes · cohesion 0.13

## Key Concepts

- **is_localhost_origin()** (12 connections) — `app/core/cors.py`
- **test_cors.py** (12 connections) — `tests/test_cors.py`
- **cors.py** (11 connections) — `app/core/cors.py`
- **is_trusted_origin()** (10 connections) — `app/core/cors.py`
- **TestIsLocalhostOrigin** (7 connections) — `tests/test_cors.py`
- **TestIsTrustedOrigin** (7 connections) — `tests/test_cors.py`
- **log_cors_config()** (4 connections) — `app/core/cors.py`
- **.test_127_0_0_1()** (2 connections) — `tests/test_cors.py`
- **.test_empty()** (2 connections) — `tests/test_cors.py`
- **.test_ipv6_loopback()** (2 connections) — `tests/test_cors.py`
- **.test_localhost()** (2 connections) — `tests/test_cors.py`
- **.test_not_localhost()** (2 connections) — `tests/test_cors.py`
- **.test_cloud_run_domain()** (2 connections) — `tests/test_cors.py`
- **.test_firebase_web_app_domain()** (2 connections) — `tests/test_cors.py`
- **.test_firebaseapp_domain()** (2 connections) — `tests/test_cors.py`
- **.test_resilai_domain()** (2 connections) — `tests/test_cors.py`
- **.test_untrusted_domain()** (2 connections) — `tests/test_cors.py`
- **CORS Configuration Helper Single source of truth for CORS allowed origins.…** (1 connections) — `app/core/cors.py`
- **Log the CORS configuration at startup. Shows: - Current ENV (prod/dev) -…** (1 connections) — `app/core/cors.py`
- **Check if an origin matches trusted production/staging domain patterns.** (1 connections) — `app/core/cors.py`
- **Check if an origin is a localhost/loopback origin.** (1 connections) — `app/core/cors.py`
- **Tests for CORS configuration helper.** (1 connections) — `tests/test_cors.py`
- **Tests for is_localhost_origin function.** (1 connections) — `tests/test_cors.py`
- **Tests for is_trusted_origin function.** (1 connections) — `tests/test_cors.py`

## Relationships

- [middleware.py](middleware.py.md) (4 shared connections)
- [get_allowed_origins](get_allowed_origins.md) (4 shared connections)
- [health.py](health.py.md) (3 shared connections)
- [validate_origin](validate_origin.md) (3 shared connections)
- [main.py](main.py.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [TestCORSErrorSafetyMiddleware](TestCORSErrorSafetyMiddleware.md) (1 shared connections)

## Source Files

- `app/core/cors.py`
- `tests/test_cors.py`

## Audit Trail

- EXTRACTED: 54 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*