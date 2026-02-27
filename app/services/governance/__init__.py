"""
Governance Services Package.

Extracts all governance-related business logic into a cohesive package:
  - compliance_engine:  Deterministic framework applicability rules
  - audit_calendar:     Audit scheduling, enrichment, and forecasting
  - tech_stack:         Tech stack lifecycle risk classification
  - lifecycle_engine:   Static version lifecycle intelligence
  - drift_engine:       Compliance drift detection & Shadow AI governance
"""

from app.services.governance.compliance_engine import get_applicable_frameworks
from app.services.governance.audit_calendar import AuditCalendarService
from app.services.governance.tech_stack import TechStackService
from app.services.governance.lifecycle_engine import (
    get_version_status,
    is_eol,
    get_eol_date,
    days_until_eol,
    get_supported_technologies,
    get_technology_versions,
    reload_config,
)
from app.services.governance.drift_engine import (
    create_baseline,
    calculate_drift,
    get_drift_timeline,
    check_shadow_ai_risk,
    calculate_sustainability_index,
    calculate_audit_failure_probability,
)

__all__ = [
    "get_applicable_frameworks",
    "AuditCalendarService",
    "TechStackService",
    "get_version_status",
    "is_eol",
    "get_eol_date",
    "days_until_eol",
    "get_supported_technologies",
    "get_technology_versions",
    "reload_config",
    # Drift engine
    "create_baseline",
    "calculate_drift",
    "get_drift_timeline",
    "check_shadow_ai_risk",
    "calculate_sustainability_index",
    "calculate_audit_failure_probability",
]
