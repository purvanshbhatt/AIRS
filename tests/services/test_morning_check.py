import pytest
from app.services.clinic_engine.engine import ClinicEngine
from app.services.clinic_engine.morning_check import MorningCheckGenerator

def test_generate_morning_check_safe():
    engine = ClinicEngine()
    generator = MorningCheckGenerator(engine)
    raw_findings = []
    
    check = generator.generate(raw_findings)
    assert check.status == "SAFE"
    assert len(check.moments) == 0

def test_generate_morning_check_needs_attention():
    engine = ClinicEngine()
    generator = MorningCheckGenerator(engine)
    raw_findings = [
        {"id": "1", "rule_id": "os_update_missing"}
    ]
    
    check = generator.generate(raw_findings)
    assert check.status == "NEEDS_ATTENTION"
    assert len(check.moments) == 1
    assert check.moments[0].type_id == "MISSING_UPDATES"
