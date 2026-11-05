# generate_detailed_roadmap

> 23 nodes · cohesion 0.13

## Key Concepts

- **generate_detailed_roadmap()** (10 connections) — `app/services/roadmap.py`
- **roadmap.py** (9 connections) — `app/services/roadmap.py`
- **generate_roadmap_item()** (6 connections) — `app/services/roadmap.py`
- **generate_simple_roadmap()** (6 connections) — `app/services/roadmap.py`
- **get_phase_for_finding()** (5 connections) — `app/services/roadmap.py`
- **roadmap_item_to_dict()** (5 connections) — `app/services/roadmap.py`
- **TestRoadmapGenerator** (5 connections) — `tests/test_frameworks.py`
- **Any** (4 connections)
- **RoadmapItem** (4 connections) — `app/services/roadmap.py`
- **.test_detailed_roadmap_structure()** (3 connections) — `tests/test_frameworks.py`
- **.test_phase_assignment_by_severity()** (3 connections) — `tests/test_frameworks.py`
- **.test_simple_roadmap_structure()** (3 connections) — `tests/test_frameworks.py`
- **AIRS Roadmap Generator Service Generates deterministic 30/60/90 day remediation…** (1 connections) — `app/services/roadmap.py`
- **Determine roadmap phase based on severity and effort. Critical/High severity +…** (1 connections) — `app/services/roadmap.py`
- **Generate a detailed roadmap item from a finding. Args: finding: Finding dict…** (1 connections) — `app/services/roadmap.py`
- **Enhanced roadmap item with detailed metadata.** (1 connections) — `app/services/roadmap.py`
- **Convert RoadmapItem to serializable dict.** (1 connections) — `app/services/roadmap.py`
- **Generate a complete 30/60/90 day roadmap from findings. Args: findings: List of…** (1 connections) — `app/services/roadmap.py`
- **Generate simplified roadmap for legacy compatibility. Args: findings: List of…** (1 connections) — `app/services/roadmap.py`
- **Tests for roadmap generation.** (1 connections) — `tests/test_frameworks.py`
- **Critical findings should go to 30-day phase.** (1 connections) — `tests/test_frameworks.py`
- **Detailed roadmap should have proper structure.** (1 connections) — `tests/test_frameworks.py`
- **Simple roadmap should have day30, day60, day90.** (1 connections) — `tests/test_frameworks.py`

## Relationships

- [test_frameworks.py](test_frameworks.py.md) (5 shared connections)
- [Organization](Organization.md) (3 shared connections)
- [get_rubric](get_rubric.md) (1 shared connections)
- [FindingsEngine](FindingsEngine.md) (1 shared connections)

## Source Files

- `app/services/roadmap.py`
- `tests/test_frameworks.py`

## Audit Trail

- EXTRACTED: 42 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*