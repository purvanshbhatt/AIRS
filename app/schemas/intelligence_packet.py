"""Strict JSON contract for Gemini intelligence packets."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SimulationImpactAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    financial_risk: str
    operational_downtime: str
    data_integrity_score: int = Field(ge=0, le=100)


class SimulationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    scenario_name: str
    threat_vector: str
    mapped_frameworks: list[str]
    attack_flow: list[str]
    impact_analysis: SimulationImpactAnalysis

    @field_validator("mapped_frameworks", "attack_flow")
    @classmethod
    def _non_empty_lists(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("List must contain at least one item")
        return value


class RemediationLedgerItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    task_id: str
    action: str
    priority: Literal["Critical", "High", "Medium", "Low"]
    ghi_impact: float
    automation_potential: bool


class ResilAIIntelligencePacket(BaseModel):
    """
    Unified intelligence contract consumed by the frontend.

    This is intentionally strict so malformed model output fails fast.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    simulation: SimulationPayload
    remediation_ledger: list[RemediationLedgerItem]

    @field_validator("remediation_ledger")
    @classmethod
    def _validate_ledger(cls, value: list[RemediationLedgerItem]) -> list[RemediationLedgerItem]:
        if not value:
            raise ValueError("remediation_ledger must contain at least one task")
        task_ids = [item.task_id for item in value]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task_id values in remediation_ledger must be unique")
        return value


class IntelligencePacketIngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["ok"]
    org_id: str
    workspace_id: str
    audit_id: str
    tasks_upserted: int
    ledger_collection_path: str
