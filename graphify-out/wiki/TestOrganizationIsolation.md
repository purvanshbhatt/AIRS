# TestOrganizationIsolation

> 9 nodes · cohesion 0.25

## Key Concepts

- **TestOrganizationIsolation** (6 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_delete_user_b_organization()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_get_user_b_organization_by_id()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_see_user_b_organizations()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_update_user_b_organization()** (3 connections) — `tests/test_tenant_isolation.py`
- **User A should get 404 when trying to access User B's org by ID.** (2 connections) — `tests/test_tenant_isolation.py`
- **User A should get 404 when trying to delete User B's org.** (1 connections) — `tests/test_tenant_isolation.py`
- **Test that organizations are isolated per user.** (1 connections) — `tests/test_tenant_isolation.py`
- **User A should not see User B's organizations in list.** (1 connections) — `tests/test_tenant_isolation.py`

## Relationships

- [make_auth_override](make_auth_override.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_tenant_isolation.py`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*