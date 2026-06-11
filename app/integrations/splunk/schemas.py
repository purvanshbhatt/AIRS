"""
Schemas for Splunk MCP Integration.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class SplunkEvent(BaseModel):
    id: str
    source: str
    sourcetype: str
    time: datetime
    host: str
    raw: str
    parsed_fields: Dict[str, Any] = Field(default_factory=dict)

class SplunkSearchRequest(BaseModel):
    query: str
    earliest_time: str = "-24h"
    latest_time: str = "now"
    limit: int = 100

class SplunkSearchResponse(BaseModel):
    status: str
    events: List[SplunkEvent]
    total_count: int

class SplunkHealthResponse(BaseModel):
    status: str
    latency_ms: float
    version: str
