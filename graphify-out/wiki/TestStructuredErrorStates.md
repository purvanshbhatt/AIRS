# TestStructuredErrorStates

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestStructuredErrorStates** (4 connections) — `tests/test_backend_contract_verification.py`
- **.test_404_returns_structured_error()** (2 connections) — `tests/test_backend_contract_verification.py`
- **.test_error_responses_never_expose_stack_traces()** (2 connections) — `tests/test_backend_contract_verification.py`
- **Backend must return structured errors that allow frontend to distinguish…** (1 connections) — `tests/test_backend_contract_verification.py`
- **Unknown route → structured 404, not a raw exception.** (1 connections) — `tests/test_backend_contract_verification.py`
- **Security: error responses must not include Python tracebacks or internal file…** (1 connections) — `tests/test_backend_contract_verification.py`

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