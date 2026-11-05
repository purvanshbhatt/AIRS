from typing import List, Any
from datetime import datetime, timezone
from pydantic import BaseModel
from app.services.clinic_engine.engine import ClinicEngine
from app.services.clinic_engine.models import ClinicMoment

class MorningCheck(BaseModel):
    id: str
    date: str
    status: str # "SAFE" or "NEEDS_ATTENTION"
    moments: List[ClinicMoment]
    generated_at: str

class MorningCheckGenerator:
    def __init__(self, engine: ClinicEngine):
        self.engine = engine

    def generate(self, raw_findings: List[Any]) -> MorningCheck:
        moments = self.engine.process_findings(raw_findings)
        status = "SAFE" if not moments else "NEEDS_ATTENTION"
        
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        
        return MorningCheck(
            id=f"mc-{date_str}",
            date=date_str,
            status=status,
            moments=moments,
            generated_at=now.isoformat()
        )
