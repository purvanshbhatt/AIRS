import sys
import json
import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models.organization import Organization

def main():
    db = SessionLocal()
    org_id = "demo-org-123"
    org = db.query(Organization).filter_by(id=org_id).first()
    if not org:
        org = Organization(id=org_id, name="Demo Clinic", org_mode="demo")
        db.add(org)
        db.commit()
    db.close()
    
    client = TestClient(app)
    response = client.get(f"/api/clinic/readiness/{org_id}")
    
    if response.status_code != 200:
        print("Failed to get report:", response.status_code, response.text)
        sys.exit(1)
        
    data = response.json()
    with open("C:/Users/purva/.gemini/antigravity/brain/8717b8a2-8fea-4987-863d-77ff5c2f5faf/sample_readiness_report.json", "w") as f:
        json.dump(data, f, indent=2)
        
    print("Exported sample_readiness_report.json")
    
    # OpenAPI extraction for Phase 2
    openapi_schema = app.openapi()
    with open("C:/Users/purva/.gemini/antigravity/brain/8717b8a2-8fea-4987-863d-77ff5c2f5faf/openapi_product.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("Exported openapi_product.json")

if __name__ == "__main__":
    main()
