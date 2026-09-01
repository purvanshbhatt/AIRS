from pydantic import BaseModel
from typing import Optional

class ClinicMoment(BaseModel):
    id: str
    type_id: str
    what_happened: str
    why_care: str
    fix_action_text: str
    ignore_impact: str
    can_autofix: bool
    estimated_fix_time_mins: int
    severity: str # "high", "medium", "low"
    finding_ref: str # The internal finding ID this correlates to
