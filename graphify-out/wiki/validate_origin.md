# validate_origin

> 17 nodes · cohesion 0.21

## Key Concepts

- **validate_origin()** (17 connections) — `app/core/cors.py`
- **TestValidateOrigin** (15 connections) — `tests/test_cors.py`
- **.test_empty_origin()** (2 connections) — `tests/test_cors.py`
- **.test_invalid_scheme_ftp()** (2 connections) — `tests/test_cors.py`
- **.test_missing_scheme()** (2 connections) — `tests/test_cors.py`
- **.test_origin_with_path()** (2 connections) — `tests/test_cors.py`
- **.test_origin_with_query()** (2 connections) — `tests/test_cors.py`
- **.test_trailing_slash_accepted()** (2 connections) — `tests/test_cors.py`
- **.test_valid_127_0_0_1()** (2 connections) — `tests/test_cors.py`
- **.test_valid_firebase_hosting()** (2 connections) — `tests/test_cors.py`
- **.test_valid_http_localhost()** (2 connections) — `tests/test_cors.py`
- **.test_valid_https_origin()** (2 connections) — `tests/test_cors.py`
- **.test_valid_https_with_port()** (2 connections) — `tests/test_cors.py`
- **.test_valid_subdomain()** (2 connections) — `tests/test_cors.py`
- **.test_wildcard_is_valid()** (2 connections) — `tests/test_cors.py`
- **Validate a single origin string. Returns: Tuple of (is_valid, error_message)** (1 connections) — `app/core/cors.py`
- **Tests for validate_origin function.** (1 connections) — `tests/test_cors.py`

## Relationships

- [is_localhost_origin](is_localhost_origin.md) (3 shared connections)
- [get_allowed_origins](get_allowed_origins.md) (1 shared connections)

## Source Files

- `app/core/cors.py`
- `tests/test_cors.py`

## Audit Trail

- EXTRACTED: 32 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*