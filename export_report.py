import json
from fastapi.testclient import TestClient
from app.main import app

def export():
    client = TestClient(app)
    # Seed the pilot org if needed
    client.post("/internal/pilot/seed")
    
    # Generate report
    resp = client.get("/api/clinic/readiness/demo-org-123")
    assert resp.status_code == 200
    
    with open("sample_readiness_report.json", "w") as f:
        json.dump(resp.json(), f, indent=2)
        
    print("Exported sample_readiness_report.json")

if __name__ == "__main__":
    export()
