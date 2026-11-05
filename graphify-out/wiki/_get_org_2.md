# _get_org

> 21 nodes · cohesion 0.17

## Key Concepts

- **_get_org()** (14 connections) — `app/api/governance.py`
- **update_profile()** (12 connections) — `app/api/governance.py`
- **applicable_frameworks()** (9 connections) — `app/api/governance.py`
- **get_governance_forecast()** (9 connections) — `app/api/governance.py`
- **get_governance_health_index()** (8 connections) — `app/api/governance.py`
- **get_profile()** (8 connections) — `app/api/governance.py`
- **uptime_analysis()** (8 connections) — `app/api/governance.py`
- **Session** (7 connections)
- **User** (7 connections)
- **get** (5 connections)
- **BackgroundTasks** (1 connections)
- **Organization** (1 connections)
- **put** (1 connections)
- **PUT /api/governance/{org_id}/profile** (1 connections) — `app/api/governance.py`
- **GET /api/governance/{org_id}/applicable-frameworks** (1 connections) — `app/api/governance.py`
- **GET /api/governance/{org_id}/uptime-analysis** (1 connections) — `app/api/governance.py`
- **GET /api/governance/{org_id}/health-index** (1 connections) — `app/api/governance.py`
- **GET /api/governance/{org_id}/forecast** (1 connections) — `app/api/governance.py`
- **Helper: resolve org with tenant isolation or 404.** (1 connections) — `app/api/governance.py`
- **GET /api/governance/{org_id}/profile** (1 connections) — `app/api/governance.py`
- **OrganizationProfileUpdate** (1 connections)

## Relationships

- [app/db/database.py](app-db-database.py.md) (9 shared connections)
- [User](User.md) (7 shared connections)
- [Organization](Organization.md) (5 shared connections)
- [_make_org](_make_org.md) (2 shared connections)
- [compliance.py](compliance.py.md) (1 shared connections)
- [governance_forecast.py](governance_forecast.py.md) (1 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)

## Source Files

- `app/api/governance.py`

## Audit Trail

- EXTRACTED: 51 (82%)
- INFERRED: 11 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*