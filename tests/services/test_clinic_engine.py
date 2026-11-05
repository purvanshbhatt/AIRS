import pytest
from app.services.clinic_engine.registry import ClinicMomentRegistry
from app.services.clinic_engine.engine import ClinicEngine
from app.services.clinic_engine.models import ClinicMoment

def test_registry_former_employee():
    finding = {"id": "f123", "rule_id": "inactive_user_active_token"}
    moment = ClinicMomentRegistry.evaluate_finding(finding)
    
    assert moment is not None
    assert moment.type_id == "FORMER_EMPLOYEE_ACCESS"
    assert "Sarah's email account still works" in moment.what_happened
    assert moment.can_autofix is True

def test_registry_unknown_finding():
    finding = {"id": "f999", "rule_id": "some_enterprise_rule_we_dont_care_about"}
    moment = ClinicMomentRegistry.evaluate_finding(finding)
    assert moment is None

def test_engine_sorting():
    findings = [
        {"id": "1", "rule_id": "os_update_missing"},
        {"id": "2", "rule_id": "backup_job_failed"},
    ]
    engine = ClinicEngine()
    moments = engine.process_findings(findings)
    
    assert len(moments) == 2
    # Backup failed is high severity, OS update is medium. Backup should be first.
    assert moments[0].type_id == "BACKUP_FAILED"
    assert moments[1].type_id == "MISSING_UPDATES"
