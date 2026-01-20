"""
AIRS Readiness Scoring Rubric

Defines 5 domains with 6 questions each, scoring formulas, and weights.
Each domain produces a 0-5 score. Weights total 100.
"""

RUBRIC = {
    "version": "1.0.0",
    "total_weight": 100,
    "max_domain_score": 5,
    "domains": {
        "telemetry_logging": {
            "name": "Telemetry & Logging",
            "description": "Measures log collection coverage, retention, and centralization",
            "weight": 25,
            "questions": [
                {
                    "id": "tl_01",
                    "text": "Are logs collected from network devices (firewalls, switches, routers)?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "tl_02",
                    "text": "Are logs collected from endpoints (workstations, servers)?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "tl_03",
                    "text": "Are logs collected from cloud services (Azure/AWS/GCP)?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "tl_04",
                    "text": "Are logs centralized in a SIEM or log management platform?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "tl_05",
                    "text": "What is your log retention period (days)?",
                    "type": "numeric",
                    "points": 1,
                    "thresholds": {
                        "0": 0,      # < 7 days
                        "7": 0.25,   # 7-29 days
                        "30": 0.5,   # 30-89 days
                        "90": 0.75,  # 90-364 days
                        "365": 1     # 365+ days
                    }
                },
                {
                    "id": "tl_06",
                    "text": "Are authentication/authorization events logged across all critical systems?",
                    "type": "boolean",
                    "points": 1
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        },
        "detection_coverage": {
            "name": "Detection Coverage",
            "description": "Measures endpoint and network detection capabilities",
            "weight": 20,
            "questions": [
                {
                    "id": "dc_01",
                    "text": "What percentage of endpoints have EDR agents installed?",
                    "type": "percentage",
                    "points": 1,
                    "thresholds": {
                        "0": 0,
                        "25": 0.25,
                        "50": 0.5,
                        "75": 0.75,
                        "95": 1
                    }
                },
                {
                    "id": "dc_02",
                    "text": "Is network traffic monitored (NDR/IDS/IPS)?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "dc_03",
                    "text": "Are detection rules/signatures updated at least weekly?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "dc_04",
                    "text": "Do you have custom detection rules for your environment?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "dc_05",
                    "text": "Is email security/anti-phishing protection in place?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "dc_06",
                    "text": "Are alerts triaged within 24 hours?",
                    "type": "boolean",
                    "points": 1
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        },
        "identity_visibility": {
            "name": "Identity Visibility",
            "description": "Measures identity security controls and visibility",
            "weight": 20,
            "questions": [
                {
                    "id": "iv_01",
                    "text": "Is MFA enforced for all users?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "iv_02",
                    "text": "Is MFA enforced for privileged/admin accounts?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "iv_03",
                    "text": "Is there a complete inventory of privileged accounts?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "iv_04",
                    "text": "Are service accounts inventoried and regularly reviewed?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "iv_05",
                    "text": "Is Privileged Access Management (PAM) solution deployed?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "iv_06",
                    "text": "Are failed login attempts and anomalies monitored?",
                    "type": "boolean",
                    "points": 1
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        },
        "ir_process": {
            "name": "IR Playbooks & Process",
            "description": "Measures incident response preparedness and processes",
            "weight": 15,
            "questions": [
                {
                    "id": "ir_01",
                    "text": "Do documented IR playbooks exist?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "ir_02",
                    "text": "Have IR playbooks been tested in the last 12 months?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "ir_03",
                    "text": "Is there a defined IR team with clear roles?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "ir_04",
                    "text": "Are there communication templates for incident notification?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "ir_05",
                    "text": "Is there an escalation matrix with contact information?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "ir_06",
                    "text": "Are tabletop exercises conducted at least annually?",
                    "type": "boolean",
                    "points": 1
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        },
        "resilience": {
            "name": "Backup/Recovery & Resilience",
            "description": "Measures backup integrity and recovery capabilities",
            "weight": 20,
            "questions": [
                {
                    "id": "rs_01",
                    "text": "Are critical systems backed up regularly?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "rs_02",
                    "text": "Are backups stored offline or immutable (air-gapped)?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "rs_03",
                    "text": "Have backup restores been tested in the last 6 months?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "rs_04",
                    "text": "Is there a documented disaster recovery plan?",
                    "type": "boolean",
                    "points": 1
                },
                {
                    "id": "rs_05",
                    "text": "What is your Recovery Time Objective (RTO) in hours?",
                    "type": "numeric",
                    "points": 1,
                    "thresholds": {
                        "0": 1,      # Immediate (undefined = worst)
                        "4": 1,      # <= 4 hours
                        "24": 0.75,  # <= 24 hours
                        "72": 0.5,   # <= 72 hours
                        "168": 0.25, # <= 1 week
                        "999": 0     # > 1 week or undefined
                    },
                    "scoring_direction": "lower_is_better"
                },
                {
                    "id": "rs_06",
                    "text": "Are backup credentials separate from primary domain credentials?",
                    "type": "boolean",
                    "points": 1
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        }
    },
    "maturity_levels": {
        "0-20": {"level": 1, "name": "Initial", "description": "Ad-hoc, reactive security posture"},
        "21-40": {"level": 2, "name": "Developing", "description": "Basic controls in place, gaps exist"},
        "41-60": {"level": 3, "name": "Defined", "description": "Documented processes, consistent execution"},
        "61-80": {"level": 4, "name": "Managed", "description": "Measured and controlled, proactive approach"},
        "81-100": {"level": 5, "name": "Optimized", "description": "Continuous improvement, industry-leading"}
    }
}


def get_rubric() -> dict:
    """Return the complete rubric definition."""
    return RUBRIC


def get_domain(domain_id: str) -> dict:
    """Return a specific domain definition."""
    return RUBRIC["domains"].get(domain_id)


def get_all_question_ids() -> list:
    """Return a flat list of all question IDs."""
    question_ids = []
    for domain in RUBRIC["domains"].values():
        for question in domain["questions"]:
            question_ids.append(question["id"])
    return question_ids


def get_question(question_id: str) -> tuple:
    """Return a question and its parent domain."""
    for domain_id, domain in RUBRIC["domains"].items():
        for question in domain["questions"]:
            if question["id"] == question_id:
                return question, domain_id
    return None, None
