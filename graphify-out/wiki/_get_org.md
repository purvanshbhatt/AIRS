# _get_org

> 17 nodes · cohesion 0.21

## Key Concepts

- **_get_org()** (14 connections) — `app/api/drift.py`
- **check_shadow_ai()** (8 connections) — `app/api/drift.py`
- **create_drift_baseline()** (8 connections) — `app/api/drift.py`
- **get_drift_analysis()** (8 connections) — `app/api/drift.py`
- **get_regulatory_forecast()** (8 connections) — `app/api/drift.py`
- **get_drift_timeline()** (7 connections) — `app/api/drift.py`
- **Session** (7 connections)
- **User** (7 connections)
- **get** (5 connections)
- **Organization** (1 connections)
- **post** (1 connections)
- **GET /api/governance/{org_id}/drift** (1 connections) — `app/api/drift.py`
- **GET /api/governance/{org_id}/drift/timeline** (1 connections) — `app/api/drift.py`
- **GET /api/governance/{org_id}/drift/shadow-ai** (1 connections) — `app/api/drift.py`
- **GET /api/governance/{org_id}/drift/regulatory-forecast** (1 connections) — `app/api/drift.py`
- **Resolve org with tenant isolation.** (1 connections) — `app/api/drift.py`
- **POST /api/governance/{org_id}/drift/baseline** (1 connections) — `app/api/drift.py`

## Relationships

- [_make_org](_make_org.md) (8 shared connections)
- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [User](User.md) (6 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `app/api/drift.py`

## Audit Trail

- EXTRACTED: 44 (86%)
- INFERRED: 7 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*