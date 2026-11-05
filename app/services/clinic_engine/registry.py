from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional
from app.services.clinic_engine.models import ClinicMoment

class BaseMoment(ABC):
    @classmethod
    @abstractmethod
    def get_type_id(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def evaluate(cls, finding: Any) -> Optional[ClinicMoment]:
        """Evaluate a raw finding and optionally return a ClinicMoment."""
        pass

class FormerEmployeeMoment(BaseMoment):
    @classmethod
    def get_type_id(cls) -> str:
        return "FORMER_EMPLOYEE_ACCESS"

    @classmethod
    def evaluate(cls, finding: Any) -> Optional[ClinicMoment]:
        rule_id = getattr(finding, "rule_id", finding.get("rule_id", "")) if isinstance(finding, dict) else getattr(finding, "rule_id", "")
        if rule_id == "inactive_user_active_token":
            finding_id = getattr(finding, "id", finding.get("id", "unknown")) if isinstance(finding, dict) else getattr(finding, "id", "unknown")
            return ClinicMoment(
                id=f"moment-{finding_id}",
                type_id=cls.get_type_id(),
                what_happened="Sarah's email account still works.",
                why_care="She can still access patient records.",
                fix_action_text="Suspend Account",
                ignore_impact="HIPAA violation and possible patient data exposure.",
                can_autofix=True,
                estimated_fix_time_mins=8,
                severity="high",
                finding_ref=str(finding_id)
            )
        return None

class BackupFailedMoment(BaseMoment):
    @classmethod
    def get_type_id(cls) -> str:
        return "BACKUP_FAILED"

    @classmethod
    def evaluate(cls, finding: Any) -> Optional[ClinicMoment]:
        rule_id = getattr(finding, "rule_id", finding.get("rule_id", "")) if isinstance(finding, dict) else getattr(finding, "rule_id", "")
        if rule_id in ["backup_job_failed", "no_recent_backup"]:
            finding_id = getattr(finding, "id", finding.get("id", "unknown")) if isinstance(finding, dict) else getattr(finding, "id", "unknown")
            return ClinicMoment(
                id=f"moment-{finding_id}",
                type_id=cls.get_type_id(),
                what_happened="Last night's patient database backup failed to run.",
                why_care="If a computer crashes today, all of yesterday's patient notes and billing are permanently lost.",
                fix_action_text="Email Instructions to IT",
                ignore_impact="Permanent loss of patient data and complete practice shutdown if a computer fails.",
                can_autofix=False,
                estimated_fix_time_mins=30,
                severity="high",
                finding_ref=str(finding_id)
            )
        return None

class MissingUpdatesMoment(BaseMoment):
    @classmethod
    def get_type_id(cls) -> str:
        return "MISSING_UPDATES"

    @classmethod
    def evaluate(cls, finding: Any) -> Optional[ClinicMoment]:
        rule_id = getattr(finding, "rule_id", finding.get("rule_id", "")) if isinstance(finding, dict) else getattr(finding, "rule_id", "")
        if rule_id == "os_update_missing":
            finding_id = getattr(finding, "id", finding.get("id", "unknown")) if isinstance(finding, dict) else getattr(finding, "id", "unknown")
            return ClinicMoment(
                id=f"moment-{finding_id}",
                type_id=cls.get_type_id(),
                what_happened="The billing computer hasn't received security updates in three months.",
                why_care="Hackers specifically look for outdated computers to sneak into networks and install ransomware.",
                fix_action_text="Schedule Update for 2 AM",
                ignore_impact="High risk of a ransomware attack locking all clinic computers.",
                can_autofix=True,
                estimated_fix_time_mins=5,
                severity="medium",
                finding_ref=str(finding_id)
            )
        return None

class ClinicMomentRegistry:
    _registry: Dict[str, Type[BaseMoment]] = {}

    @classmethod
    def register(cls, moment_class: Type[BaseMoment]):
        cls._registry[moment_class.get_type_id()] = moment_class

    @classmethod
    def evaluate_finding(cls, finding: Any) -> Optional[ClinicMoment]:
        """Pass a finding to all registered moments until one matches."""
        for moment_class in cls._registry.values():
            result = moment_class.evaluate(finding)
            if result:
                return result
        return None

# Auto-register v1 moments
ClinicMomentRegistry.register(FormerEmployeeMoment)
ClinicMomentRegistry.register(BackupFailedMoment)
ClinicMomentRegistry.register(MissingUpdatesMoment)
