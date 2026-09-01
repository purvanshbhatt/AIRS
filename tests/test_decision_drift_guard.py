import pytest
from app.services.decision_engine import project_readiness
from app.services.scoring import calculate_readiness_delta
import copy

def generate_fixtures():
    fixtures = []
    base_state = {
        "assessment_score": 50.0,
        "verified_controls": [],
        "verified_coverages": [],
        "lifecycle_risks": [],
        "exposure_risks": []
    }
    
    # Generate 20 distinct actions / states to test
    actions = [
        [{"type": "VERIFY_CONTROL", "control": {"name": "C1", "severity": "critical"}}],
        [{"type": "VERIFY_CONTROL", "control": {"name": "C1", "severity": "important"}}],
        [{"type": "VERIFY_CONTROL", "control": {"name": "C1", "severity": "standard"}}],
        [{"type": "IMPROVE_COVERAGE", "coverage": {"name": "App1", "coverage_percentage": 100.0}}],
        [{"type": "IMPROVE_COVERAGE", "coverage": {"name": "App1", "coverage_percentage": 95.0}}],
        [{"type": "IMPROVE_COVERAGE", "coverage": {"name": "App1", "coverage_percentage": 85.0}}],
        [{"type": "IMPROVE_COVERAGE", "coverage": {"name": "App1", "coverage_percentage": 70.0}}],
        [{"type": "IMPROVE_ASSESSMENT", "score_increase": 10.0}],
        [{"type": "IMPROVE_ASSESSMENT", "score_increase": 55.0}], # Caps at 100
        [{"type": "REMEDIATE_LIFECYCLE", "software_name": "OldApp"}],
        [{"type": "REMEDIATE_EXPOSURE", "software_name": "VulnApp"}],
        
        # Multiple actions
        [
            {"type": "VERIFY_CONTROL", "control": {"name": "C1", "severity": "critical"}},
            {"type": "IMPROVE_COVERAGE", "coverage": {"name": "App1", "coverage_percentage": 100.0}}
        ],
        [
            {"type": "REMEDIATE_LIFECYCLE", "software_name": "OldApp"},
            {"type": "REMEDIATE_EXPOSURE", "software_name": "VulnApp"}
        ],
        [
            {"type": "IMPROVE_ASSESSMENT", "score_increase": 10.0},
            {"type": "VERIFY_CONTROL", "control": {"name": "C1", "severity": "important"}}
        ],
        [
            {"type": "VERIFY_CONTROL", "control": {"name": "C1", "severity": "critical"}},
            {"type": "VERIFY_CONTROL", "control": {"name": "C2", "severity": "critical"}},
            {"type": "VERIFY_CONTROL", "control": {"name": "C3", "severity": "critical"}},
            {"type": "VERIFY_CONTROL", "control": {"name": "C4", "severity": "critical"}},
            {"type": "VERIFY_CONTROL", "control": {"name": "C5", "severity": "critical"}},
            {"type": "VERIFY_CONTROL", "control": {"name": "C6", "severity": "critical"}} # Tests capping at +15
        ],
        [
            {"type": "IMPROVE_COVERAGE", "coverage": {"name": "A1", "coverage_percentage": 100.0}},
            {"type": "IMPROVE_COVERAGE", "coverage": {"name": "A2", "coverage_percentage": 100.0}},
            {"type": "IMPROVE_COVERAGE", "coverage": {"name": "A3", "coverage_percentage": 100.0}},
            {"type": "IMPROVE_COVERAGE", "coverage": {"name": "A4", "coverage_percentage": 100.0}} # Tests capping at +10
        ],
        [
            {"type": "REMEDIATE_LIFECYCLE", "software_name": "OldApp1"},
            {"type": "REMEDIATE_LIFECYCLE", "software_name": "OldApp2"}
        ],
        [
            {"type": "REMEDIATE_EXPOSURE", "software_name": "VulnApp1"},
            {"type": "REMEDIATE_EXPOSURE", "software_name": "VulnApp2"}
        ],
        [
            {"type": "VERIFY_CONTROL", "control": {"name": "C1", "severity": "standard"}},
            {"type": "IMPROVE_ASSESSMENT", "score_increase": 2.0}
        ],
        [
            {"type": "REMEDIATE_LIFECYCLE", "software_name": "OldApp"},
            {"type": "IMPROVE_COVERAGE", "coverage": {"name": "App1", "coverage_percentage": 99.0}}
        ]
    ]

    for i, action_list in enumerate(actions):
        # We start with some risks that can be remediated
        state = copy.deepcopy(base_state)
        state["lifecycle_risks"].append({"software_name": "OldApp", "lifecycle_status": "END_OF_LIFE"})
        state["lifecycle_risks"].append({"software_name": "OldApp1", "lifecycle_status": "END_OF_LIFE"})
        state["lifecycle_risks"].append({"software_name": "OldApp2", "lifecycle_status": "DEPRECATED"})
        
        state["exposure_risks"].append({"software_name": "VulnApp", "kev_count": 1, "is_critical_asset": True})
        state["exposure_risks"].append({"software_name": "VulnApp1", "kev_count": 1, "is_critical_asset": True, "is_internet_facing": True})
        state["exposure_risks"].append({"software_name": "VulnApp2", "kev_count": 1, "is_critical_asset": False, "is_internet_facing": True})
        
        fixtures.append((state, action_list))
        
    return fixtures

@pytest.mark.parametrize("state, actions", generate_fixtures())
def test_project_readiness_matches_actual_scoring(state, actions):
    # 1. Project using decision engine
    projected = project_readiness(
        current_assessment_score=state["assessment_score"],
        current_verified_controls=state["verified_controls"],
        current_verified_coverages=state["verified_coverages"],
        current_lifecycle_risks=state["lifecycle_risks"],
        current_exposure_risks=state["exposure_risks"],
        proposed_actions=actions,
        previous_readiness_score=50.0
    )
    
    # 2. Emulate the actual DB changes that would happen
    new_state = copy.deepcopy(state)
    for action in actions:
        action_type = action.get("type")
        if action_type == "VERIFY_CONTROL":
            new_state["verified_controls"].append(action.get("control", {}))
        elif action_type == "IMPROVE_COVERAGE":
            new_state["verified_coverages"].append(action.get("coverage", {}))
        elif action_type == "REMEDIATE_LIFECYCLE":
            software_name = action.get("software_name")
            new_state["lifecycle_risks"] = [risk for risk in new_state["lifecycle_risks"] if risk.get("software_name") != software_name]
        elif action_type == "REMEDIATE_EXPOSURE":
            software_name = action.get("software_name")
            new_state["exposure_risks"] = [risk for risk in new_state["exposure_risks"] if risk.get("software_name") != software_name]
        elif action_type == "IMPROVE_ASSESSMENT":
            new_state["assessment_score"] = min(100.0, new_state["assessment_score"] + action.get("score_increase", 0.0))
            
    # 3. Call scoring module directly with the "post-state" values
    actual = calculate_readiness_delta(
        assessment_score=new_state["assessment_score"],
        verified_controls=new_state["verified_controls"],
        verified_coverages=new_state["verified_coverages"],
        lifecycle_risks=new_state["lifecycle_risks"],
        exposure_risks=new_state["exposure_risks"],
        previous_readiness_score=50.0
    )
    
    # 4. Anti-Drift AC: Ensure projection equals actual
    assert projected["final_readiness"] == actual["final_readiness"], "Anti-drift violation: projected score differs from actual."
    assert projected["modifiers"] == actual["modifiers"], "Anti-drift violation: modifiers differ."
    assert projected["reasons"] == actual["reasons"], "Anti-drift violation: reasons differ."
