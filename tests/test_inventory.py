from fastapi.testclient import TestClient

def test_create_asset(client: TestClient):
    payload = {
        "name": "Test LLM",
        "asset_type": "model",
        "business_criticality": "critical",
        "exposure_level": "internal",
        "lifecycle_stage": "production"
    }
    response = client.post("/api/v1/inventory/assets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test LLM"
    assert data["asset_type"] == "model"
    assert "id" in data

def test_list_assets(client: TestClient):
    # First create an asset
    payload = {
        "name": "Another Model",
        "asset_type": "model",
        "business_criticality": "high",
        "exposure_level": "internal",
        "lifecycle_stage": "development"
    }
    client.post("/api/v1/inventory/assets", json=payload)
    
    response = client.get("/api/v1/inventory/assets")
    assert response.status_code == 200
    data = response.json()
    assert "assets" in data
    assert len(data["assets"]) >= 1

def test_get_asset(client: TestClient):
    # First create an asset
    payload = {
        "name": "Model to Get",
        "asset_type": "agent",
        "business_criticality": "high",
        "exposure_level": "public",
        "lifecycle_stage": "production"
    }
    create_resp = client.post("/api/v1/inventory/assets", json=payload)
    asset_id = create_resp.json()["id"]
    
    response = client.get(f"/api/v1/inventory/assets/{asset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == asset_id
    assert data["name"] == "Model to Get"

def test_update_asset(client: TestClient):
    # First create an asset
    payload = {
        "name": "Model to Update",
        "asset_type": "rag_pipeline",
        "business_criticality": "medium",
        "exposure_level": "internal",
        "lifecycle_stage": "testing"
    }
    create_resp = client.post("/api/v1/inventory/assets", json=payload)
    asset_id = create_resp.json()["id"]
    
    # Update it
    update_payload = {
        "name": "Updated Model",
        "lifecycle_stage": "production"
    }
    update_resp = client.patch(f"/api/v1/inventory/assets/{asset_id}", json=update_payload)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "Updated Model"
    assert data["lifecycle_stage"] == "production"
    assert data["version"] == 2

def test_get_asset_versions(client: TestClient):
    # First create an asset
    payload = {
        "name": "Versioned Model",
        "asset_type": "rag_pipeline",
        "business_criticality": "medium",
        "exposure_level": "internal",
        "lifecycle_stage": "testing"
    }
    create_resp = client.post("/api/v1/inventory/assets", json=payload)
    asset_id = create_resp.json()["id"]
    
    # Update it
    update_payload = {
        "name": "Versioned Model Updated",
    }
    client.patch(f"/api/v1/inventory/assets/{asset_id}", json=update_payload)
    
    response = client.get(f"/api/v1/inventory/assets/{asset_id}/versions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["version_number"] == 2
    assert data[1]["version_number"] == 1

def test_asset_relationships(client: TestClient):
    # Create source asset
    src_payload = {
        "name": "Source Model",
        "asset_type": "dataset",
        "business_criticality": "medium",
        "exposure_level": "internal",
        "lifecycle_stage": "production"
    }
    src_resp = client.post("/api/v1/inventory/assets", json=src_payload)
    src_id = src_resp.json()["id"]
    
    # Create target asset
    tgt_payload = {
        "name": "Target Model",
        "asset_type": "model",
        "business_criticality": "high",
        "exposure_level": "internal",
        "lifecycle_stage": "development"
    }
    tgt_resp = client.post("/api/v1/inventory/assets", json=tgt_payload)
    tgt_id = tgt_resp.json()["id"]
    
    # Create relationship
    rel_payload = {
        "target_asset_id": tgt_id,
        "relationship_type": "feeds_into"
    }
    rel_resp = client.post(f"/api/v1/inventory/assets/{src_id}/relationships", json=rel_payload)
    assert rel_resp.status_code == 201
    
    # Get graph
    graph_resp = client.get("/api/v1/inventory/graph")
    assert graph_resp.status_code == 200
    graph = graph_resp.json()
    assert len(graph["nodes"]) >= 2
    assert len(graph["edges"]) >= 1
    assert graph["edges"][0]["source_asset_id"] == src_id
    assert graph["edges"][0]["target_asset_id"] == tgt_id
