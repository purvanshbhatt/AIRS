# middleware.py

> 31 nodes · cohesion 0.10

## Key Concepts

- **middleware.py** (17 connections) — `app/core/middleware.py`
- **CORSErrorSafetyMiddleware** (9 connections) — `app/core/middleware.py`
- **global_exception_handler()** (8 connections) — `app/core/middleware.py`
- **http_exception_handler()** (7 connections) — `app/core/middleware.py`
- **Request** (7 connections)
- **validation_exception_handler()** (7 connections) — `app/core/middleware.py`
- **RequestIdMiddleware** (6 connections) — `app/core/middleware.py`
- **.dispatch()** (5 connections) — `app/core/middleware.py`
- **._get_cors_origin()** (5 connections) — `app/core/middleware.py`
- **.dispatch()** (5 connections) — `app/core/middleware.py`
- **SecurityHeadersMiddleware** (5 connections) — `app/core/middleware.py`
- **generate_request_id()** (4 connections) — `app/core/logging.py`
- **set_request_id()** (4 connections) — `app/core/logging.py`
- **JSONResponse** (4 connections)
- **Response** (3 connections)
- **.dispatch()** (3 connections) — `app/core/middleware.py`
- **BaseHTTPMiddleware** (3 connections)
- **Set the request ID in context.** (1 connections) — `app/core/logging.py`
- **Generate a new unique request ID.** (1 connections) — `app/core/logging.py`
- **.__init__()** (1 connections) — `app/core/middleware.py`
- **Exception** (1 connections)
- **HTTPException** (1 connections)
- **AIRS Middleware Production-grade middleware for request tracking, logging,…** (1 connections) — `app/core/middleware.py`
- **Inject standard security response headers on every response.** (1 connections) — `app/core/middleware.py`
- **Middleware that generates a unique request ID for each request. - Generates or…** (1 connections) — `app/core/middleware.py`
- *... and 6 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [main.py](main.py.md) (7 shared connections)
- [is_localhost_origin](is_localhost_origin.md) (4 shared connections)
- [get_safe_error_response](get_safe_error_response.md) (2 shared connections)
- [sentinel.py](sentinel.py.md) (2 shared connections)
- [TestCORSErrorSafetyMiddleware](TestCORSErrorSafetyMiddleware.md) (1 shared connections)

## Source Files

- `app/core/logging.py`
- `app/core/middleware.py`

## Audit Trail

- EXTRACTED: 69 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*