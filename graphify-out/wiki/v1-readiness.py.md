# v1/readiness.py

> 34 nodes · cohesion 0.12

## Key Concepts

- **v1/readiness.py** (31 connections) — `app/api/v1/readiness.py`
- **get_readiness_actions()** (10 connections) — `app/api/v1/readiness.py`
- **get_readiness_drivers()** (10 connections) — `app/api/v1/readiness.py`
- **schemas/readiness.py** (10 connections) — `app/schemas/readiness.py`
- **get_readiness_ledger()** (8 connections) — `app/api/v1/readiness.py`
- **get_readiness_timeline()** (8 connections) — `app/api/v1/readiness.py`
- **_resolve_org()** (8 connections) — `app/api/v1/readiness.py`
- **_placeholder_scoring_inputs()** (6 connections) — `app/api/v1/readiness.py`
- **_entry_to_response()** (5 connections) — `app/api/v1/readiness.py`
- **Session** (5 connections)
- **ExecutiveAction** (5 connections) — `app/schemas/readiness.py`
- **ExecutiveActionsResponse** (5 connections) — `app/schemas/readiness.py`
- **ReadinessDriver** (5 connections) — `app/schemas/readiness.py`
- **ReadinessDriversResponse** (5 connections) — `app/schemas/readiness.py`
- **ReadinessLedgerEntryResponse** (5 connections) — `app/schemas/readiness.py`
- **ReadinessLedgerResponse** (5 connections) — `app/schemas/readiness.py`
- **ReadinessTimelinePoint** (5 connections) — `app/schemas/readiness.py`
- **ReadinessTimelineResponse** (5 connections) — `app/schemas/readiness.py`
- **get** (4 connections)
- **User** (4 connections)
- **Organization** (1 connections)
- **Readiness Intelligence API (Sprint 1.8 Feature A). Endpoints: GET…** (1 connections) — `app/api/v1/readiness.py`
- **Returns the Organization or raises 404. Note: the spec requires 404 for unknown…** (1 connections) — `app/api/v1/readiness.py`
- **Build a minimal deterministic scoring inputs payload. For now (Phase A), the…** (1 connections) — `app/api/v1/readiness.py`
- **Pydantic schemas for Sprint 1.8 — Readiness Drivers & Ledger API. Strict typing…** (1 connections) — `app/schemas/readiness.py`
- *... and 9 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (9 shared connections)
- [BaseModel](BaseModel.md) (8 shared connections)
- [User](User.md) (5 shared connections)
- [extract_drivers](extract_drivers.md) (5 shared connections)
- [ReadinessLedgerEntry](ReadinessLedgerEntry.md) (2 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [_get_current_state](_get_current_state.md) (1 shared connections)

## Source Files

- `app/api/v1/readiness.py`
- `app/schemas/readiness.py`

## Audit Trail

- EXTRACTED: 86 (89%)
- INFERRED: 11 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*