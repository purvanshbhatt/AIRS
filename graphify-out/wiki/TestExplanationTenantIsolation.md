# TestExplanationTenantIsolation

> 4 nodes · cohesion 0.50

## Key Concepts

- **TestExplanationTenantIsolation** (3 connections) — `tests/test_tenant_isolation_v2.py`
- **.test_explanation_service_requires_both_ids()** (3 connections) — `tests/test_tenant_isolation_v2.py`
- **Validate explanation service requires tenant credentials.** (1 connections) — `tests/test_tenant_isolation_v2.py`
- **ExplanationService must reject empty org_id or owner_uid.** (1 connections) — `tests/test_tenant_isolation_v2.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [ExplanationService](ExplanationService.md) (1 shared connections)

## Source Files

- `tests/test_tenant_isolation_v2.py`

## Audit Trail

- EXTRACTED: 5 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*