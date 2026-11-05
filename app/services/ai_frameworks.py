from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.framework_mapping import FrameworkMappingRegistry, FrameworkType
from app.models.finding import Finding, FindingStatus

# Standard total controls for AI frameworks
AI_FRAMEWORK_TOTALS = {
    FrameworkType.NIST_AI_RMF: 72,
    FrameworkType.MITRE_ATLAS: 14,
}

def calculate_ai_framework_coverage(db: Session, org_id: str) -> List[Dict[str, Any]]:
    """
    Calculate 0-100 coverage score per AI framework for a given organization.
    
    This is a deterministic function that queries FrameworkMappingRegistry for
    findings linked to an organization's assessments. We assume mappings reflect 
    covered/satisfied controls or known tracked controls.
    """
    # Join FrameworkMappingRegistry -> Finding -> Assessment to filter by org_id
    # Since Finding doesn't directly have org_id, we need to join Assessment.
    from app.models.assessment import Assessment
    
    results = (
        db.query(
            FrameworkMappingRegistry.framework_type,
            func.count(func.distinct(FrameworkMappingRegistry.control_id)).label("covered_controls")
        )
        .join(Finding, Finding.id == FrameworkMappingRegistry.finding_id)
        .join(Assessment, Assessment.id == Finding.assessment_id)
        .filter(Assessment.organization_id == org_id)
        .filter(FrameworkMappingRegistry.framework_type.in_([
            FrameworkType.NIST_AI_RMF, 
            FrameworkType.MITRE_ATLAS
        ]))
        # Assuming only resolved or active findings that act as positive evidence count towards coverage
        # Or we just count all mappings for this deterministic stub
        .group_by(FrameworkMappingRegistry.framework_type)
        .all()
    )
    
    # Initialize dictionary with zeros for AI frameworks
    tracked = {fw: 0 for fw in AI_FRAMEWORK_TOTALS.keys()}
    
    for fw_type, count in results:
        tracked[fw_type] = count
        
    coverage_data = []
    
    for fw_type, covered in tracked.items():
        total = AI_FRAMEWORK_TOTALS[fw_type]
        # Cap at 100% 
        pct = min(100.0, round((covered / total) * 100.0, 1))
        
        coverage_data.append({
            "framework": fw_type.value,
            "covered_controls": covered,
            "total_controls": total,
            "coverage_percent": pct,
        })
        
    # Sort for deterministic output
    coverage_data.sort(key=lambda x: x["framework"])
    return coverage_data
