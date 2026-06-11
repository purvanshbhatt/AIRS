"""
Dedicated Schemas for Sentinel Splunk Native Integration.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SplunkEvent(BaseModel):
    id: str = Field(alias="_bkt", default="")
    source: str = ""
    sourcetype: str = ""
    time: str = ""
    host: str = ""
    raw: str = Field(alias="_raw", default="")
    parsed_fields: Dict[str, Any] = Field(default_factory=dict)

    def model_dump_json(self, *args, **kwargs) -> str:
        return super().model_dump_json(*args, **kwargs)

class SplunkSearchResponse(BaseModel):
    events: List[SplunkEvent]
    total_count: int

class SentinelSplunkConfig(BaseModel):
    host: str
    hec_port: int
    mgmt_port: int
    token: str
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = False
