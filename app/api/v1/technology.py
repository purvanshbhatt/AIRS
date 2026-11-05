from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import require_auth
from app.schemas.technology import TechInventoryItem, TechLifecycleAnalysis, TechExposureItem
from app.services.technology_intelligence import TechnologyIntelligenceOrchestrator
from app.services.governance.lifecycle_analysis import LifecycleAnalysisService
from app.models.tech_stack import TechStackItem
from app.services.cve.cve_enrichment import CVEEnrichmentService

router = APIRouter(prefix="/technology", tags=["Technology Intelligence"])

@router.get("/inventory/{org_id}", response_model=List[TechInventoryItem])
async def get_technology_inventory(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """
    Returns the enriched technology inventory for a given organization,
    including lifecycle and vulnerability signals.
    """
    # In a real app we would verify the user has access to org_id here
    # 404 handled if no org/empty, but for now we just return orchestrator results
    orchestrator = TechnologyIntelligenceOrchestrator(db, org_id)
    inventory = await orchestrator.get_technology_inventory()
    return inventory

@router.get("/lifecycle/{org_id}", response_model=List[TechLifecycleAnalysis])
async def get_technology_lifecycle(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """
    Returns detailed lifecycle analysis for all tech stack items in the org.
    """
    items = db.query(TechStackItem).filter(TechStackItem.org_id == org_id).all()
    
    lifecycle_service = LifecycleAnalysisService(db)
    
    results = []
    for item in items:
        if not item.version:
            continue
            
        analysis = lifecycle_service.analyze_lifecycle(item.component_name, item.version)
        results.append({
            "component_name": item.component_name,
            "version": item.version,
            "status": analysis.get("status", "Unknown"),
            "latest_supported": analysis.get("latest_supported"),
            "eol_date": analysis.get("eol_date"),
            "message": analysis.get("message", "")
        })
        
    return results

@router.get("/exposure/{org_id}", response_model=List[TechExposureItem])
async def get_technology_exposure(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """
    Returns a flattened list of all exposures (vulnerabilities) linked to the tech stack.
    """
    items = db.query(TechStackItem).filter(TechStackItem.org_id == org_id).all()
    cve_service = CVEEnrichmentService(db, org_id)
    
    inventory_items = []
    for item in items:
        inventory_items.append({
            "vendor": "",
            "product": item.component_name,
            "version": item.version
        })
        
    enriched_results = await cve_service.bulk_enrich(inventory_items)
    
    exposures = []
    for i, item in enumerate(items):
        enrichment = enriched_results[i]
        for vuln in enrichment.vulnerabilities:
            exposures.append({
                "cve_id": vuln.cve_id,
                "component_name": item.component_name,
                "version": item.version,
                "severity": vuln.severity,
                "is_kev": vuln.is_kev
            })
            
    return exposures
