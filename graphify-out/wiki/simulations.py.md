# simulations.py

> 53 nodes · cohesion 0.08

## Key Concepts

- **simulations.py** (25 connections) — `app/api/v1/simulations.py`
- **ThreatSimulationEngine** (18 connections) — `app/simulation/engine.py`
- **SimulationResult** (15 connections) — `app/models/simulation_result.py`
- **SimulationCategory** (14 connections) — `app/models/simulation_result.py`
- **run_simulation()** (11 connections) — `app/api/v1/simulations.py`
- **.run_simulation()** (10 connections) — `app/simulation/engine.py`
- **get_simulation_history()** (9 connections) — `app/api/v1/simulations.py`
- **run_full_assessment()** (9 connections) — `app/api/v1/simulations.py`
- **simulation_result.py** (8 connections) — `app/models/simulation_result.py`
- **SimulationResultResponse** (8 connections) — `app/schemas/simulation.py`
- **_get_org_id()** (7 connections) — `app/api/v1/simulations.py`
- **get_simulation_detail()** (7 connections) — `app/api/v1/simulations.py`
- **trigger_simulation()** (7 connections) — `app/api/v1/simulations.py`
- **Session** (6 connections)
- **User** (6 connections)
- **simulation.py** (6 connections) — `app/schemas/simulation.py`
- **SimulationRunRequest** (6 connections) — `app/schemas/simulation.py`
- **FullAssessmentResponse** (5 connections) — `app/schemas/simulation.py`
- **SimulationResultListResponse** (5 connections) — `app/schemas/simulation.py`
- **._calculate_blast_radius()** (5 connections) — `app/simulation/engine.py`
- **._create_empty_result()** (5 connections) — `app/simulation/engine.py`
- **SimulationRule** (4 connections) — `app/simulation/engine.py`
- **._asset_matches_preconditions()** (4 connections) — `app/simulation/engine.py`
- **._generate_impact_narrative()** (4 connections) — `app/simulation/engine.py`
- **.get_simulation_history()** (4 connections) — `app/simulation/engine.py`
- *... and 28 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [User](User.md) (7 shared connections)
- [simulation/engine.py](simulation-engine.py.md) (6 shared connections)
- [BaseModel](BaseModel.md) (4 shared connections)
- [Organization](Organization.md) (3 shared connections)
- [mobile.py](mobile.py.md) (3 shared connections)
- [inventory.py](inventory.py.md) (3 shared connections)
- [get_user_org_id](get_user_org_id.md) (2 shared connections)

## Source Files

- `app/api/v1/simulations.py`
- `app/models/simulation_result.py`
- `app/schemas/simulation.py`
- `app/simulation/engine.py`

## Audit Trail

- EXTRACTED: 118 (84%)
- INFERRED: 22 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*