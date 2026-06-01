from enum import Enum

class EvidenceType(str, Enum):
    FAILED_BACKUP_VALIDATION = "failed_backup_validation"
    MISSING_MFA = "missing_mfa"
    INACTIVE_EDR = "inactive_edr"
    LOGGING_GAP = "logging_gap"
    OVERDUE_DR_TESTING = "overdue_dr_testing"
    CRITICAL_VULNERABILITY = "critical_vulnerability"
    CLOUD_MISCONFIGURATION = "cloud_misconfiguration"
    RANSOMWARE_INDICATOR = "ransomware_indicator"
    DATA_EXFILTRATION_INDICATOR = "data_exfiltration_indicator"
    AI_AGENT_ABUSE_INDICATOR = "ai_agent_abuse_indicator"
