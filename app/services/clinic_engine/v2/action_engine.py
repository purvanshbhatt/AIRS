"""
Action Engine

Converts raw ActionIntent (from capabilities) into customer-facing ActionCards using clinic context.
"""
from typing import List

from app.services.clinic_engine.v2.contracts import (
    ActionCard,
    BusinessRiskAssessment,
    ClinicContext,
    StaffSummary,
    DeviceSummary
)
from app.services.clinic_engine.v2.schema import ClinicMoment, ActionIntent


class ActionEngine:
    """Builds customer-facing action cards from capability ActionIntents.
    
    Deterministic templates personalized with clinic context.
    AI never decides. Templates do.
    """
    
    def build_action_cards(
        self,
        moment: ClinicMoment,
        risk: BusinessRiskAssessment,
        context: ClinicContext,
    ) -> List[ActionCard]:
        """Convert moment's ActionIntents to rich ActionCards."""
        cards = []
        for intent in moment.actions:
            card = self._build_card(intent, moment, risk, context)
            cards.append(card)
        return cards
    
    def _build_card(
        self, 
        intent: ActionIntent, 
        moment: ClinicMoment, 
        risk: BusinessRiskAssessment, 
        context: ClinicContext
    ) -> ActionCard:
        """Match on intent.action_id or moment.capability_id to pick template."""
        # Defaults
        staff_name = "Inactive User"
        device_name = "Unknown Device"
        system_name = "Unknown System"
        location = "Unknown Location"
        device_type = "device"
        
        # Resolve from context using automation_params
        target_user = intent.automation_params.get("user_id") or intent.automation_params.get("email")
        target_device = intent.automation_params.get("device_id")
        
        staff = None
        if target_user:
            for s in context.staff:
                if s.id == target_user or s.email == target_user:
                    staff = s
                    staff_name = s.display_name
                    break
        
        device = None
        if target_device:
            for d in context.devices:
                if d.id == target_device or d.external_device_id == target_device:
                    device = d
                    device_name = d.device_name
                    location = d.location or location
                    device_type = d.device_type or device_type
                    break
                    
        email = staff.email if staff and staff.email else "the user"
        systems_list = ", ".join(staff.access_systems) if staff and staff.access_systems else "all clinic systems"
        
        specific_issue = intent.automation_params.get("issue", "security updates")
        action_type = intent.action_id or moment.capability_id
        
        if "unauthorized_access" in action_type or "disable_account" in action_type:
            days = intent.automation_params.get("inactive_days", 30)
            status = staff.employment_status if staff else "unknown"
            
            recommendation = "Disable immediately" if status == "terminated" else "Review before disabling"
            
            safe_because = []
            if status == "terminated":
                safe_because.append("User terminated")
            safe_because.append("No active sessions")
            safe_because.append(f"Account inactive {days} days")
                
            return ActionCard(
                action_id=intent.action_id,
                title=f"Disable {staff_name}'s Account" if staff else "Disable Inactive Account",
                description=f"This will immediately lock {email} and prevent access to {systems_list}.",
                expected_result=f"{staff_name} will no longer be able to sign in or access any clinic systems including patient records.",
                rollback_description="If needed, the account can be re-enabled from the Microsoft 365 admin portal within 30 days.",
                success_message="Account disabled successfully. Access to patient records has been revoked.",
                recommendation=recommendation,
                safe_because=safe_because,
                reversible=True,
                approval_needed=False,
                category="access_control",
                required_permissions=["Microsoft 365 Admin"],
                estimated_minutes=intent.estimated_minutes,
                can_automate=intent.can_automate
            )
            
        elif "device_compromise" in action_type or "remediate_device" in action_type:
            recommendation = "Schedule update tonight" if device_type == "workstation" else "Update immediately"
            
            return ActionCard(
                action_id=intent.action_id,
                title=f"Update {device_name}" if device_name != "Unknown Device" else f"Secure {location} Computer",
                description=f"The {device_type} at {location} needs {specific_issue}.",
                expected_result="Device will be compliant and protected.",
                rollback_description="Updates can be rolled back through Windows Update settings.",
                success_message="Device secured. Compliance restored.",
                recommendation=recommendation,
                safe_because=[],
                reversible=True,
                approval_needed=True,
                category="device_security",
                required_permissions=["Endpoint Admin"],
                estimated_minutes=intent.estimated_minutes,
                can_automate=intent.can_automate
            )
            
        elif "recovery_readiness" in action_type or "verify_backup" in action_type:
            hours = intent.automation_params.get("hours_since_backup", 24)
            system = None
            target_sys = intent.automation_params.get("system_id")
            if target_sys:
                for sys in context.critical_systems:
                    if sys.id == target_sys or sys.system_name == target_sys:
                        system = sys
                        system_name = sys.system_name
                        break
            
            recommendation = "Verify now" if system and system.hipaa_relevant else "Check today"
            
            return ActionCard(
                action_id=intent.action_id,
                title=f"Verify {system_name} Backup",
                description=f"The last successful backup was {hours} hours ago. Verify the backup system.",
                expected_result="Backup status will be confirmed and any issues identified.",
                rollback_description="N/A",
                success_message="Backup verified. Recovery is available.",
                recommendation=recommendation,
                safe_because=[],
                reversible=False,
                approval_needed=False,
                category="backup",
                required_permissions=["Backup Admin"],
                estimated_minutes=intent.estimated_minutes,
                can_automate=intent.can_automate
            )
            
        # Fallback card
        return ActionCard(
            action_id=intent.action_id,
            title=intent.label,
            description="Action required based on security findings.",
            expected_result="Issue will be addressed.",
            rollback_description="Reversibility varies by action.",
            success_message="Action completed.",
            recommendation="Review and execute",
            safe_because=[],
            reversible=False,
            approval_needed=True,
            category="general",
            required_permissions=[],
            estimated_minutes=intent.estimated_minutes,
            can_automate=intent.can_automate
        )
