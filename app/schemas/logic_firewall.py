"""Schemas for Logic Firewall simulation and trace endpoints."""

from typing import List

from pydantic import BaseModel, Field


class LogicFirewallSimulationRequest(BaseModel):
    query: str = Field(default="What is our 401k policy?")
    organization_name: str = Field(default="Acme Health Systems")
    enable_logic_firewall: bool = Field(default=True)


class QuarantinedChunkResponse(BaseModel):
    chunk_index: int
    threat_type: str
    mitre_mapping: str
    signals: List[str]
    action: str
    confidence: float
    excerpt: str


class LogicTraceResponse(BaseModel):
    request_id: str
    threat_type: str
    mitre_mapping: str
    signals: List[str]
    action: str
    confidence: float
    created_at: str


class LogicFirewallSimulationResponse(BaseModel):
    request_id: str
    scenario: str
    query: str
    pipeline: str
    raw_response_without_firewall: str
    sanitized_response_with_firewall: str
    chunks_total: int
    chunks_quarantined: int
    quarantined_chunks: List[QuarantinedChunkResponse]
    threat_type: str
    signal: str
    actions_taken: List[str]
    logic_trace: LogicTraceResponse
    frameworks: dict
    business_impact_narrative: str
