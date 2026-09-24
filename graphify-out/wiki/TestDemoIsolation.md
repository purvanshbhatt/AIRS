# TestDemoIsolation

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestDemoIsolation** (5 connections) — `tests/test_demo_isolation.py`
- **.test_demo_and_real_orgs_do_not_share_data()** (4 connections) — `tests/test_demo_isolation.py`
- **.test_owner_uid_isolation()** (4 connections) — `tests/test_demo_isolation.py`
- **.test_real_org_has_no_demo_data()** (4 connections) — `tests/test_demo_isolation.py`
- **Validate demo data never leaks into real organizations.** (1 connections) — `tests/test_demo_isolation.py`
- **A real organization created by a real user should have no demo telemetry.** (1 connections) — `tests/test_demo_isolation.py`
- **Demo orgs and real orgs should have different owner_uids.** (1 connections) — `tests/test_demo_isolation.py`
- **Organizations are strictly isolated by owner_uid.** (1 connections) — `tests/test_demo_isolation.py`

## Relationships

- [Organization](Organization.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)

## Source Files

- `tests/test_demo_isolation.py`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*