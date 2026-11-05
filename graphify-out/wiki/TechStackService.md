# TechStackService

> 44 nodes · cohesion 0.07

## Key Concepts

- **TechStackService** (25 connections) — `app/services/governance/tech_stack.py`
- **list_items()** (11 connections) — `app/api/tech_stack.py`
- **_verify_org()** (10 connections) — `app/api/tech_stack.py`
- **create_item()** (9 connections) — `app/api/tech_stack.py`
- **update_item()** (9 connections) — `app/api/tech_stack.py`
- **delete_item()** (8 connections) — `app/api/tech_stack.py`
- **TechStackItem** (7 connections)
- **.get_summary()** (6 connections) — `app/services/governance/tech_stack.py`
- **.update()** (6 connections) — `app/services/governance/tech_stack.py`
- **TestTechStackSummary** (6 connections) — `tests/test_governance.py`
- **Session** (5 connections)
- **User** (5 connections)
- **.create()** (5 connections) — `app/services/governance/tech_stack.py`
- **.enrich_response()** (5 connections) — `app/services/governance/tech_stack.py`
- **.get()** (5 connections) — `app/services/governance/tech_stack.py`
- **.list_all()** (4 connections) — `app/services/governance/tech_stack.py`
- **.test_summary_all_current()** (4 connections) — `tests/test_governance.py`
- **.test_summary_mixed()** (4 connections) — `tests/test_governance.py`
- **.test_summary_with_eol()** (4 connections) — `tests/test_governance.py`
- **.test_summary_empty_stack()** (3 connections) — `tests/test_governance.py`
- **.delete()** (2 connections) — `app/services/governance/tech_stack.py`
- **.__init__()** (2 connections) — `app/services/governance/tech_stack.py`
- **BackgroundTasks** (1 connections)
- **delete** (1 connections)
- **get** (1 connections)
- *... and 19 more nodes in this community*

## Relationships

- [test_reliability.py](test_reliability.py.md) (8 shared connections)
- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [._setup](_setup.md) (6 shared connections)
- [User](User.md) (5 shared connections)
- [_make_org](_make_org.md) (5 shared connections)
- [.classify_risk](classify_risk.md) (4 shared connections)
- [Organization](Organization.md) (2 shared connections)

## Source Files

- `app/api/tech_stack.py`
- `app/services/governance/tech_stack.py`
- `tests/test_governance.py`

## Audit Trail

- EXTRACTED: 94 (92%)
- INFERRED: 8 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*