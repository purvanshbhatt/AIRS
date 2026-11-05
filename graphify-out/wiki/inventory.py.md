# inventory.py

> 49 nodes · cohesion 0.09

## Key Concepts

- **inventory.py** (33 connections) — `app/api/v1/inventory.py`
- **AIAsset** (27 connections) — `app/models/ai_asset.py`
- **models/ai_asset.py** (15 connections) — `app/models/ai_asset.py`
- **_get_org_id()** (13 connections) — `app/api/v1/inventory.py`
- **create_asset()** (10 connections) — `app/api/v1/inventory.py`
- **update_asset()** (10 connections) — `app/api/v1/inventory.py`
- **schemas/ai_asset.py** (10 connections) — `app/schemas/ai_asset.py`
- **create_relationship()** (9 connections) — `app/api/v1/inventory.py`
- **get_asset_graph()** (9 connections) — `app/api/v1/inventory.py`
- **Session** (9 connections)
- **User** (9 connections)
- **AIAssetVersion** (9 connections) — `app/models/ai_asset.py`
- **get_versions()** (8 connections) — `app/api/v1/inventory.py`
- **list_assets()** (8 connections) — `app/api/v1/inventory.py`
- **AIAssetRelationship** (8 connections) — `app/models/ai_asset.py`
- **deactivate_asset()** (7 connections) — `app/api/v1/inventory.py`
- **get_asset()** (7 connections) — `app/api/v1/inventory.py`
- **_asset_snapshot()** (5 connections) — `app/api/v1/inventory.py`
- **AIAssetCreateRequest** (5 connections) — `app/schemas/ai_asset.py`
- **AIAssetGraphResponse** (5 connections) — `app/schemas/ai_asset.py`
- **AIAssetListResponse** (5 connections) — `app/schemas/ai_asset.py`
- **AIAssetRelationshipRequest** (5 connections) — `app/schemas/ai_asset.py`
- **AIAssetUpdateRequest** (5 connections) — `app/schemas/ai_asset.py`
- **get** (4 connections)
- **AIAssetRelationshipResponse** (4 connections) — `app/schemas/ai_asset.py`
- *... and 24 more nodes in this community*

## Relationships

- [User](User.md) (10 shared connections)
- [simulation/engine.py](simulation-engine.py.md) (10 shared connections)
- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [BaseModel](BaseModel.md) (8 shared connections)
- [Organization](Organization.md) (4 shared connections)
- [mobile.py](mobile.py.md) (3 shared connections)
- [policies/engine.py](policies-engine.py.md) (3 shared connections)
- [simulations.py](simulations.py.md) (3 shared connections)
- [get_user_org_id](get_user_org_id.md) (2 shared connections)
- [policies.py](policies.py.md) (1 shared connections)

## Source Files

- `app/api/v1/inventory.py`
- `app/models/ai_asset.py`
- `app/schemas/ai_asset.py`

## Audit Trail

- EXTRACTED: 136 (84%)
- INFERRED: 26 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*