# TestAuthDependencyIntegrityV2

> 5 nodes · cohesion 0.40

## Key Concepts

- **TestAuthDependencyIntegrityV2** (6 connections) — `tests/test_tenant_isolation_v2.py`
- **.test_require_auth_exists()** (2 connections) — `tests/test_tenant_isolation_v2.py`
- **.test_require_org_admin_exists()** (2 connections) — `tests/test_tenant_isolation_v2.py`
- **.test_user_class_has_uid()** (2 connections) — `tests/test_tenant_isolation_v2.py`
- **Validate auth module exposes correct dependencies.** (1 connections) — `tests/test_tenant_isolation_v2.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [User](User.md) (2 shared connections)

## Source Files

- `tests/test_tenant_isolation_v2.py`

## Audit Trail

- EXTRACTED: 6 (67%)
- INFERRED: 3 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*