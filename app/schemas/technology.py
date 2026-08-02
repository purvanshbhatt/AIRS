from typing import List, Optional
from pydantic import BaseModel

class VulnerabilitySchema(BaseModel):
    cve_id: str
    severity: str
    cvss_score: float
    is_kev: bool

class TechInventoryItem(BaseModel):
    id: str
    component_name: str
    version: Optional[str]
    category: Optional[str]
    lts_status: str
    major_versions_behind: int
    notes: Optional[str]
    critical_cves: int
    high_cves: int
    kev_count: int
    readiness_impact: str
    vulnerabilities: List[VulnerabilitySchema] = []

class TechLifecycleAnalysis(BaseModel):
    component_name: str
    version: str
    status: str
    latest_supported: Optional[str]
    eol_date: Optional[str]
    message: str

class TechExposureItem(BaseModel):
    cve_id: str
    component_name: str
    version: str
    severity: str
    is_kev: bool
