import asyncio
import json
import logging
from sqlalchemy.orm import Session
from datetime import datetime

# Setup basic logging to suppress noisy output if we just want JSON
logging.basicConfig(level=logging.ERROR)

from app.services.discovery.aws_ssm_poller import AWSConfigPoller
from app.services.lifecycle.normalization import VersionNormalizationEngine
from app.services.lifecycle.lifecycle_intelligence import LifecycleIntelligenceService
from app.services.cve.cve_enrichment import CVEEnrichmentService
from app.services.scoring import calculate_readiness_delta
from app.models.tech_stack import TechStackItem, LtsStatus

async def main():
    from app.db.database import SessionLocal
    db = SessionLocal()
    
    # 1. AWS SSM Inventory Poller
    poller = AWSConfigPoller(credentials={})
    raw_records = await poller.poll()
    
    # 2. Normalization Engine
    normalizer = VersionNormalizationEngine()
    
    # 3. Lifecycle Analysis Service
    lifecycle_service = LifecycleIntelligenceService(db=db)
    
    # 4. CVE Enrichment Service
    cve_service = CVEEnrichmentService(db=db, org_id="test_org")
    
    lifecycle_risks = []
    
    for record in raw_records:
        # Step A: Normalize
        norm = normalizer.normalize(record.software_name + " " + record.version)
        
        # Step B: Lifecycle Status
        result = lifecycle_service.check_lifecycle_status(
            vendor=norm.vendor,
            product_name=norm.product,
            version=norm.version
        )
        
        # Step C: CVE / KEV
        cve_result = await cve_service.enrich_software(
            vendor=norm.vendor, 
            product_name=norm.product, 
            version=norm.version
        )
        
        # Step D: Construct Risk Object
        lifecycle_risks.append({
            "software_name": f"{norm.product} {norm.version}",
            "lifecycle_status": result.lifecycle_status.value,
            "is_critical_asset": True, # Assume critical for demonstration
            "is_internet_facing": False,
            "kev_count": cve_result.kev_count
        })

    # 5. Readiness Delta Engine
    # Base assessment score
    base_score = 80.0
    
    # Mock verified controls
    verified_controls = [
        {"name": "Endpoint Protection (CrowdStrike)", "severity": "critical"},
        {"name": "MFA Enforcement (Okta)", "severity": "important"}
    ]
    
    # Calculate
    delta_result = calculate_readiness_delta(
        assessment_score=base_score,
        verified_controls=verified_controls,
        lifecycle_risks=lifecycle_risks,
        previous_readiness_score=85.0
    )
    
    print(json.dumps(delta_result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
