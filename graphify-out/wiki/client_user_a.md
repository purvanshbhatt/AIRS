# client_user_a

> 4 nodes · cohesion 0.67

## Key Concepts

- **client_user_a()** (4 connections) — `tests/test_tenant_isolation.py`
- **client_user_b()** (4 connections) — `tests/test_tenant_isolation.py`
- **fixture** (2 connections)
- **Create a test client authenticated as User A.** (2 connections) — `tests/test_tenant_isolation.py`

## Relationships

- [make_auth_override](make_auth_override.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)

## Source Files

- `tests/test_tenant_isolation.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*