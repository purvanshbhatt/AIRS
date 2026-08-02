import sys
import json
import uuid
import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, Base, engine
from app.models.organization import Organization
from app.api.clinic.router import get_clinic_readiness
import asyncio

async def test_readiness():
    db = SessionLocal()
    try:
        org_id = str(uuid.uuid4())
        org = Organization(id=org_id, name="Test Org", owner_uid="test_user", org_mode="demo")
        db.add(org)
        db.commit()

        print(f"Testing readiness endpoint for org {org_id}")
        
        report = await get_clinic_readiness(org_id, db)
        print(report.model_dump_json(indent=2))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_readiness())
