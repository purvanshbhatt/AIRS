from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.tech_stack import TechStackItem
from app.services.cve.cve_enrichment import CVEEnrichmentService

class TechnologyIntelligenceOrchestrator:
    """
    Orchestrates technology data by retrieving TechStackItems and enriching them
    with CVE information to determine readiness impacts.
    """
    
    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id
        self.cve_service = CVEEnrichmentService(db, org_id)

    async def get_technology_inventory(self) -> List[Dict[str, Any]]:
        """
        Returns the technology inventory enriched with vulnerability data and
        readiness impact annotations.
        """
        items = self.db.query(TechStackItem).filter(TechStackItem.org_id == self.org_id).all()
        
        # Prepare for bulk enrichment
        inventory_items = []
        for item in items:
            inventory_items.append({
                "vendor": "",  # Vendor typically not stored in standard TechStackItem
                "product": item.component_name,
                "version": item.version
            })
            
        # Enrich CVEs using the service
        enriched_results = await self.cve_service.bulk_enrich(inventory_items)
        
        result = []
        for i, item in enumerate(items):
            enrichment = enriched_results[i]
            
            # Determine readiness impact based on existing state/enrichment
            readiness_impact = "low"
            if item.lts_status.value in ("eol", "deprecated") or enrichment.kev_count > 0 or enrichment.critical_cves > 0:
                readiness_impact = "high"
            elif enrichment.high_cves > 0 or item.major_versions_behind >= 2:
                readiness_impact = "medium"
                
            result.append({
                "id": item.id,
                "component_name": item.component_name,
                "version": item.version,
                "category": item.category,
                "lts_status": item.lts_status.value,
                "major_versions_behind": item.major_versions_behind,
                "notes": item.notes,
                "critical_cves": enrichment.critical_cves,
                "high_cves": enrichment.high_cves,
                "kev_count": enrichment.kev_count,
                "readiness_impact": readiness_impact,
                "vulnerabilities": [
                    {
                        "cve_id": v.cve_id,
                        "severity": v.severity,
                        "cvss_score": v.cvss_score,
                        "is_kev": v.is_kev
                    }
                    for v in enrichment.vulnerabilities
                ]
            })
            
        return result
