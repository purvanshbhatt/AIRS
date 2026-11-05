# mobile.py

> 23 nodes · cohesion 0.15

## Key Concepts

- **mobile.py** (22 connections) — `app/api/v1/mobile.py`
- **PolicyEvaluationLog** (12 connections) — `app/models/governance_policy.py`
- **get_mobile_dashboard()** (10 connections) — `app/api/v1/mobile.py`
- **governance_policy.py** (10 connections) — `app/models/governance_policy.py`
- **get_mobile_alerts()** (8 connections) — `app/api/v1/mobile.py`
- **get_mobile_score_trend()** (8 connections) — `app/api/v1/mobile.py`
- **get_mobile_simulations()** (8 connections) — `app/api/v1/mobile.py`
- **get_org_or_404()** (8 connections) — `app/api/v1/mobile.py`
- **Session** (5 connections)
- **get** (4 connections)
- **User** (4 connections)
- **.get_evaluation_history()** (3 connections) — `app/governance/policies/engine.py`
- **Base** (2 connections)
- **Organization** (1 connections)
- **Mobile Executive API Optimized, compressed endpoints for the iOS/Android…** (1 connections) — `app/api/v1/mobile.py`
- **Return historical scores for sparkline rendering.** (1 connections) — `app/api/v1/mobile.py`
- **Return the most recent threat simulation runs.** (1 connections) — `app/api/v1/mobile.py`
- **Return recent policy violations as mobile alerts.** (1 connections) — `app/api/v1/mobile.py`
- **Return an aggregated executive summary for the mobile dashboard.** (1 connections) — `app/api/v1/mobile.py`
- **Retrieve historical evaluation logs for a policy.** (1 connections) — `app/governance/policies/engine.py`
- **.__repr__()** (1 connections) — `app/models/governance_policy.py`
- **GovernancePolicy — Policy Definition & Enforcement. Manages organizational…** (1 connections) — `app/models/governance_policy.py`
- **Append-only log of governance policy evaluations. Design Rationale: -…** (1 connections) — `app/models/governance_policy.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [User](User.md) (5 shared connections)
- [Organization](Organization.md) (5 shared connections)
- [policies.py](policies.py.md) (5 shared connections)
- [policies/engine.py](policies-engine.py.md) (5 shared connections)
- [ContinuousScoringEngine](ContinuousScoringEngine.md) (3 shared connections)
- [simulations.py](simulations.py.md) (3 shared connections)
- [inventory.py](inventory.py.md) (3 shared connections)

## Source Files

- `app/api/v1/mobile.py`
- `app/governance/policies/engine.py`
- `app/models/governance_policy.py`

## Audit Trail

- EXTRACTED: 63 (84%)
- INFERRED: 12 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*