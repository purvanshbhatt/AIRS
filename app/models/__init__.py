# SQLAlchemy models
# Import all models to register them with SQLAlchemy
from app.models.evidence import EvidenceLedger, NormalizedEvidenceRecord
from app.models.organization import Organization
from app.models.assessment import Assessment, AssessmentStatus
from app.models.answer import Answer
from app.models.score import Score
from app.models.finding import Finding, Severity, FindingStatus
from app.models.report import Report
from app.models.api_key import ApiKey
from app.models.webhook import Webhook
from app.models.roadmap_item import RoadmapItem
from app.models.external_finding import ExternalFinding
from app.models.audit_event import AuditEvent
from app.models.pilot_request import PilotRequest
from app.models.question_metadata import (
    QuestionMetadata,
    MaturityLevel,
    EffortLevel,
    ImpactLevel,
    ControlFunction,
)
from app.models.audit_calendar import AuditCalendarEntry, AuditType
from app.models.tech_stack import TechStackItem, LtsStatus
from app.models.framework_registry import FrameworkRegistry, FrameworkCategory
from app.models.framework_mapping import FrameworkMappingRegistry
from app.models.wazuh_config import WazuhConfig
from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
from app.models.control_rule_registry import ControlRuleRegistry
from app.models.score_audit_log import ScoreAuditLog
from app.models.finding_provenance import (
    FindingProvenance,
    VerificationSource,
    ProvenanceStatus,
)
from app.models.connector import (
    Connector, ConnectorSyncLog,
    ConnectorType, ConnectorAuthMethod, ConnectorStatus,
)
from app.models.ai_asset import (
    AIAsset, AIAssetVersion, AIAssetRelationship,
    AIAssetType, BusinessCriticality, ExposureLevel, LifecycleStage,
)
from app.models.telemetry_event import TelemetryEvent
from app.models.score_snapshot import ScoreSnapshot, SnapshotTrigger
from app.models.readiness_ledger import ReadinessLedgerEntry
from app.models.simulation_result import SimulationResult, SimulationCategory
from app.models.governance_policy import (
    GovernancePolicy, PolicyEvaluationLog,
    PolicyType, EnforcementMode,
)
from app.models.drift_event import DriftEvent
from app.models.software_catalog import SoftwareCatalog
from app.models.discovered_asset import DiscoveredAsset
from app.models.verification import (
    VerificationResult,
    ControlEvidence,
    VerificationAuditLog,
    VerificationState,
    VerificationConfidence,
)
from app.sentinel.evidence.models import TelemetryEvidence
from app.sentinel.twin.models import SentinelSimulation
from app.models.discovery import TechnologyInventory, InstalledProduct, EvidenceSource, HostAsset
from app.models.clinic_moment import ClinicMomentRecord, MomentStatus

# Clinic Product Layer Models
from app.models.clinic.staff import ClinicStaff
from app.models.clinic.device import ClinicDevice
from app.models.clinic.critical_system import CriticalSystem
from app.models.clinic.msp import MSPRelationship
from app.models.clinic.value_metric import ClinicValueMetric
from app.models.clinic.readiness_snapshot import ReadinessSnapshot

# Lifecycle Intelligence Models
from app.models.lifecycle_catalog import (
    GlobalSoftwareCatalog,
    SoftwareVersion,
    LifecycleReference,
)

__all__ = [
    "ClinicMomentRecord",
    "MomentStatus",
    "DiscoveredAsset",
    "Organization",
    "Assessment",
    "AssessmentStatus",
    "Answer",
    "Score",
    "Finding",
    "Severity",
    "FindingStatus",
    "Report",
    "ApiKey",
    "Webhook",
    "RoadmapItem",
    "ExternalFinding",
    "AuditEvent",
    "PilotRequest",
    "QuestionMetadata",
    "MaturityLevel",
    "EffortLevel",
    "ImpactLevel",
    "ControlFunction",
    "AuditCalendarEntry",
    "AuditType",
    "TechStackItem",
    "LtsStatus",
    "FrameworkRegistry",
    "FrameworkCategory",
    "FrameworkMappingRegistry",
    "FindingProvenance",
    "VerificationSource",
    "ProvenanceStatus",
    "ControlRuleRegistry",
    "WazuhTelemetryCache",
    "Connector",
    "ConnectorSyncLog",
    "ConnectorType",
    "ConnectorAuthMethod",
    "ConnectorStatus",
    "AIAsset",
    "AIAssetVersion",
    "AIAssetRelationship",
    "AIAssetType",
    "BusinessCriticality",
    "ExposureLevel",
    "LifecycleStage",
    "TelemetryEvent",
    "ScoreSnapshot",
    "SnapshotTrigger",
    "ReadinessLedgerEntry",
    "SimulationResult",
    "SimulationCategory",
    "GovernancePolicy",
    "PolicyEvaluationLog",
    "PolicyType",
    "EnforcementMode",
    "DriftEvent",
    "SoftwareCatalog",
    "VerificationResult",
    "ControlEvidence",
    "VerificationAuditLog",
    "VerificationState",
    "VerificationConfidence",
    "TelemetryEvidence",
    "SentinelSimulation",
    "ClinicStaff",
    "ClinicDevice",
    "CriticalSystem",
    "MSPRelationship",
    "ClinicValueMetric",
    "ReadinessSnapshot",
    "GlobalSoftwareCatalog",
    "SoftwareVersion",
    "LifecycleReference",
]
