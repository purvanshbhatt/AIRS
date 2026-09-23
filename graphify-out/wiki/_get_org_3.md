# _get_org

> 20 nodes · cohesion 0.19

## Key Concepts

- **_get_org()** (15 connections) — `app/api/reliability.py`
- **simulate_reliability()** (11 connections) — `app/api/reliability.py`
- **accept_recommendation()** (9 connections) — `app/api/reliability.py`
- **get_downtime_budget()** (8 connections) — `app/api/reliability.py`
- **get_reliability_history()** (8 connections) — `app/api/reliability.py`
- **get_reliability_index()** (8 connections) — `app/api/reliability.py`
- **Session** (8 connections)
- **User** (8 connections)
- **get_sla_advisor()** (7 connections) — `app/api/reliability.py`
- **get** (5 connections)
- **GET /api/governance/{org_id}/reliability-index/confidence** (4 connections) — `app/api/reliability.py`
- **_check_rate_limit()** (3 connections) — `app/api/reliability.py`
- **post** (2 connections)
- **Organization** (1 connections)
- **POST /api/governance/{org_id}/reliability-index/simulate** (1 connections) — `app/api/reliability.py`
- **POST /api/governance/{org_id}/reliability-index/accept-recommendation** (1 connections) — `app/api/reliability.py`
- **Block if user exceeds simulation rate limit.** (1 connections) — `app/api/reliability.py`
- **Resolve org with tenant isolation.** (1 connections) — `app/api/reliability.py`
- **GET /api/governance/{org_id}/reliability-index** (1 connections) — `app/api/reliability.py`
- **BreachSimulationRequest** (1 connections)

## Relationships

- [app/db/database.py](app-db-database.py.md) (11 shared connections)
- [User](User.md) (7 shared connections)
- [calculate_rcs](calculate_rcs.md) (5 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [simulate_breach](simulate_breach.md) (2 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [_make_org](_make_org.md) (1 shared connections)

## Source Files

- `app/api/reliability.py`

## Audit Trail

- EXTRACTED: 54 (82%)
- INFERRED: 12 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*