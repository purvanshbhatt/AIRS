"""
Frameworks API — Serves the compliance mappings for the Frontend FrameworkTab.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.framework_mapping import FrameworkMappingRegistry

router = APIRouter(prefix="/frameworks", tags=["Frameworks"])

@router.get("/mapping")
async def get_framework_mappings(db: Session = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns all findings mapped by framework.
    Used by the React FrameworkTab to display compliance status.
    """
    mappings = db.query(FrameworkMappingRegistry).all()
    
    result = {}
    for mapping in mappings:
        fw_type = mapping.framework_type.value
        if fw_type not in result:
            result[fw_type] = []
        
        result[fw_type].append({
            "finding_id": mapping.finding_id,
            "control_id": mapping.control_id,
            "mapping_version": mapping.mapping_version,
            "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
        })
        
    return result

@router.get("/coverage/{org_id}")
async def get_framework_coverage_data(
    org_id: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns the AI framework coverage for a specific organization.
    """
    from app.services.ai_frameworks import calculate_ai_framework_coverage
    return calculate_ai_framework_coverage(db, org_id)
