import asyncio
import json
from app.db.database import SessionLocal
from app.api.assessments import get_assessment_service
from app.core.auth import User
from app.api.assessments import download_executive_summary
import logging

logging.basicConfig(level=logging.DEBUG)

async def test():
    db = SessionLocal()
    # Find an assessment that has been scored
    from app.models.assessment import Assessment
    ass = db.query(Assessment).filter(Assessment.overall_score != None).first()
    if not ass:
        print("No scored assessment found.")
        return

    print(f"Testing with assessment {ass.id}")
    user = User(uid=ass.owner_uid, email="test@test.com")
    
    try:
        response = await download_executive_summary(ass.id, db, user)
        print("Success! Got response.")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
