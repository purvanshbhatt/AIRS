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
                problem=f"The account for {staff_name} is inactive but still enabled." if staff else "An inactive account is still enabled.",
                why_it_matters="It could be used to improperly access patient records.",
                recommended_action=f"This will immediately lock {email} and prevent access to {systems_list}. {staff_name} will no longer be able to sign in.",
                can_be_undone=True,
                estimated_time_minutes=intent.estimated_minutes,
                fix_now_available=intent.can_automate,
                category="access_control",
                approval_needed=False,
                required_permissions=["Microsoft 365 Admin"],
                success_message="Account disabled successfully. Access to patient records has been revoked."
            )
            
        elif "device_compromise" in action_type or "remediate_device" in action_type:
            recommendation = "Schedule update tonight" if device_type == "workstation" else "Update immediately"
            
            return ActionCard(
                action_id=intent.action_id,
                problem=f"The {device_type} at {location} needs {specific_issue}.",
                why_it_matters="A compromised or outdated device can be a gateway to the clinic network.",
                recommended_action="The device will be updated to become compliant and protected.",
                can_be_undone=True,
                estimated_time_minutes=intent.estimated_minutes,
                fix_now_available=intent.can_automate,
                category="device_security",
                approval_needed=True,
                required_permissions=["Endpoint Admin"],
                success_message="Device secured. Compliance restored."
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
                problem=f"The last successful backup for {system_name} was {hours} hours ago.",
                why_it_matters="If the system fails, recent clinic data cannot be recovered.",
                recommended_action="The backup system will be verified and any issues identified will be highlighted.",
                can_be_undone=False,
                estimated_time_minutes=intent.estimated_minutes,
                fix_now_available=intent.can_automate,
                category="backup",
                approval_needed=False,
                required_permissions=["Backup Admin"],
                success_message="Backup verified. Recovery is available."
            )
            
        # Fallback card
        return ActionCard(
            action_id=intent.action_id,
            problem=intent.label,
            why_it_matters="Security findings indicate action is required.",
            recommended_action="The issue will be addressed.",
            can_be_undone=False,
            estimated_time_minutes=intent.estimated_minutes,
            fix_now_available=intent.can_automate,
            category="general",
            approval_needed=True,
            required_permissions=[],
            success_message="Action completed."
        )
