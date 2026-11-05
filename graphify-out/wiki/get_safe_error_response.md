# get_safe_error_response

> 14 nodes · cohesion 0.18

## Key Concepts

- **get_safe_error_response()** (7 connections) — `app/core/logging.py`
- **SafeJsonFormatter** (6 connections) — `app/core/logging.py`
- **._format_message()** (4 connections) — `app/core/logging.py`
- **Any** (4 connections)
- **.format()** (4 connections) — `app/core/logging.py`
- **._format_value()** (4 connections) — `app/core/logging.py`
- **._sanitize_data()** (4 connections) — `app/core/logging.py`
- **LogRecord** (2 connections)
- **Exception** (1 connections)
- **Format event data as readable message.** (1 connections) — `app/core/logging.py`
- **Create a safe error response that doesn't expose internal details. Logs the…** (1 connections) — `app/core/logging.py`
- **JSON-style log formatter that's safe for production. Does not include sensitive…** (1 connections) — `app/core/logging.py`
- **Format a value for logging.** (1 connections) — `app/core/logging.py`
- **Remove sensitive keys from data.** (1 connections) — `app/core/logging.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (5 shared connections)
- [EventLogger](EventLogger.md) (2 shared connections)
- [middleware.py](middleware.py.md) (2 shared connections)

## Source Files

- `app/core/logging.py`

## Audit Trail

- EXTRACTED: 25 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*