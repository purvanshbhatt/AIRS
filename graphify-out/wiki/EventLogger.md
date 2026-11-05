# EventLogger

> 17 nodes · cohesion 0.17

## Key Concepts

- **EventLogger** (12 connections) — `app/core/logging.py`
- **._log_event()** (11 connections) — `app/core/logging.py`
- **.answers_submitted()** (3 connections) — `app/core/logging.py`
- **.assessment_created()** (3 connections) — `app/core/logging.py`
- **.organization_created()** (3 connections) — `app/core/logging.py`
- **.report_generated()** (3 connections) — `app/core/logging.py`
- **.scoring_executed()** (3 connections) — `app/core/logging.py`
- **.error_occurred()** (2 connections) — `app/core/logging.py`
- **.summary_fetched()** (2 connections) — `app/core/logging.py`
- **.__init__()** (1 connections) — `app/core/logging.py`
- **Structured event logger for key business events. All events are logged with…** (1 connections) — `app/core/logging.py`
- **Log an event with structured data.** (1 connections) — `app/core/logging.py`
- **Log assessment creation.** (1 connections) — `app/core/logging.py`
- **Log answers submission.** (1 connections) — `app/core/logging.py`
- **Log scoring execution.** (1 connections) — `app/core/logging.py`
- **Log report generation.** (1 connections) — `app/core/logging.py`
- **Log organization creation.** (1 connections) — `app/core/logging.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [get_safe_error_response](get_safe_error_response.md) (2 shared connections)

## Source Files

- `app/core/logging.py`

## Audit Trail

- EXTRACTED: 27 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*