# discovery/orchestrator.py

> 56 nodes · cohesion 0.07

## Key Concepts

- **discovery/orchestrator.py** (27 connections) — `app/services/discovery/orchestrator.py`
- **TechnologyDiscoveryService** (20 connections) — `app/services/discovery/discovery.py`
- **TechnologyDiscoveryOrchestrator** (20 connections) — `app/services/discovery/orchestrator.py`
- **models/discovery.py** (13 connections) — `app/models/discovery.py`
- **HostAsset** (11 connections) — `app/models/discovery.py`
- **InstalledProduct** (11 connections) — `app/models/discovery.py`
- **TechnologyInventory** (11 connections) — `app/models/discovery.py`
- **discovery/discovery.py** (11 connections) — `app/services/discovery/discovery.py`
- **AWSDiscoveryService** (9 connections) — `app/services/discovery/aws_discovery.py`
- **GraphDiscoveryService** (9 connections) — `app/services/discovery/graph_discovery.py`
- **AssetType** (8 connections) — `app/models/discovery.py`
- **.run_discovery_cycle()** (8 connections) — `app/services/discovery/orchestrator.py`
- **EvidenceSource** (7 connections) — `app/models/discovery.py`
- **aws_discovery.py** (7 connections) — `app/services/discovery/aws_discovery.py`
- **graph_discovery.py** (7 connections) — `app/services/discovery/graph_discovery.py`
- **Base** (4 connections)
- **.discover_from_aws()** (3 connections) — `app/services/discovery/aws_discovery.py`
- **._execute_mock_aws_discovery()** (3 connections) — `app/services/discovery/aws_discovery.py`
- **.__init__()** (3 connections) — `app/services/discovery/aws_discovery.py`
- **.create_inventory()** (3 connections) — `app/services/discovery/discovery.py`
- **.get_latest_inventory()** (3 connections) — `app/services/discovery/discovery.py`
- **.discover_from_graph()** (3 connections) — `app/services/discovery/graph_discovery.py`
- **._execute_mock_graph_discovery()** (3 connections) — `app/services/discovery/graph_discovery.py`
- **.__init__()** (3 connections) — `app/services/discovery/graph_discovery.py`
- **._deduplicate_assets()** (3 connections) — `app/services/discovery/orchestrator.py`
- *... and 31 more nodes in this community*

## Relationships

- [Organization](Organization.md) (17 shared connections)
- [WazuhConfig](WazuhConfig.md) (10 shared connections)
- [test_reliability.py](test_reliability.py.md) (9 shared connections)
- [LifecycleIntelligenceService](LifecycleIntelligenceService.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [lifecycle_intelligence.py](lifecycle_intelligence.py.md) (2 shared connections)

## Source Files

- `app/models/discovery.py`
- `app/services/discovery/aws_discovery.py`
- `app/services/discovery/discovery.py`
- `app/services/discovery/graph_discovery.py`
- `app/services/discovery/orchestrator.py`

## Audit Trail

- EXTRACTED: 122 (84%)
- INFERRED: 23 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*