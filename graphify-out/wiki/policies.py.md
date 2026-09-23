# policies.py

> 43 nodes · cohesion 0.12

## Key Concepts

- **policies.py** (32 connections) — `app/api/v1/policies.py`
- **PolicyEngine** (25 connections) — `app/governance/policies/engine.py`
- **_get_org_id()** (12 connections) — `app/api/v1/policies.py`
- **create_policy()** (11 connections) — `app/api/v1/policies.py`
- **evaluate_all_policies()** (10 connections) — `app/api/v1/policies.py`
- **update_policy()** (10 connections) — `app/api/v1/policies.py`
- **EnforcementMode** (10 connections) — `app/models/governance_policy.py`
- **evaluate_policy()** (9 connections) — `app/api/v1/policies.py`
- **Session** (9 connections)
- **User** (9 connections)
- **PolicyType** (9 connections) — `app/models/governance_policy.py`
- **policy.py** (9 connections) — `app/schemas/policy.py`
- **get_evaluation_history()** (8 connections) — `app/api/v1/policies.py`
- **get_policy()** (8 connections) — `app/api/v1/policies.py`
- **list_policies()** (8 connections) — `app/api/v1/policies.py`
- **PolicyResponse** (8 connections) — `app/schemas/policy.py`
- **get_policy_violations()** (7 connections) — `app/api/v1/policies.py`
- **PolicyViolationResponse** (7 connections) — `app/schemas/policy.py`
- **.create_policy()** (6 connections) — `app/governance/policies/engine.py`
- **PolicyEvaluationResponse** (6 connections) — `app/schemas/policy.py`
- **PolicyCreateRequest** (5 connections) — `app/schemas/policy.py`
- **PolicyEvaluateAllResponse** (5 connections) — `app/schemas/policy.py`
- **PolicyEvaluationLogResponse** (5 connections) — `app/schemas/policy.py`
- **PolicyUpdateRequest** (5 connections) — `app/schemas/policy.py`
- **get** (4 connections)
- *... and 18 more nodes in this community*

## Relationships

- [policies/engine.py](policies-engine.py.md) (16 shared connections)
- [User](User.md) (10 shared connections)
- [BaseModel](BaseModel.md) (7 shared connections)
- [app/db/database.py](app-db-database.py.md) (6 shared connections)
- [mobile.py](mobile.py.md) (5 shared connections)
- [get_user_org_id](get_user_org_id.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)
- [inventory.py](inventory.py.md) (1 shared connections)

## Source Files

- `app/api/v1/policies.py`
- `app/governance/policies/engine.py`
- `app/models/governance_policy.py`
- `app/schemas/policy.py`

## Audit Trail

- EXTRACTED: 116 (75%)
- INFERRED: 38 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*