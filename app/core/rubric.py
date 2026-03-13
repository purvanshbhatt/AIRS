"""
AIRS Readiness Scoring Rubric

Defines 5 domains with 6 questions each, scoring formulas, and weights.
Each domain produces a 0-5 score. Weights total 100.

NIST CSF 2.0 functions:
  Govern (GV) - Organizational context, risk strategy, oversight
  Identify (ID) - Asset inventory, risk assessment
  Protect (PR) - Safeguards, identity management, data security
  Detect (DE) - Anomaly and event detection, monitoring
  Respond (RS) - Response planning, communications, analysis
  Recover (RC) - Recovery planning, improvements, communications
"""

from copy import deepcopy

# NIST CSF 2.0 function definitions
NIST_FUNCTIONS = {
    "GV": {"name": "Govern", "description": "Organizational risk management and oversight"},
    "ID": {"name": "Identify", "description": "Asset inventory and risk assessment"},
    "PR": {"name": "Protect", "description": "Safeguards including identity management and data security"},
    "DE": {"name": "Detect", "description": "Anomaly and event detection, continuous monitoring"},
    "RS": {"name": "Respond", "description": "Response planning, communications, analysis, and mitigation"},
    "RC": {"name": "Recover", "description": "Recovery planning, improvements, and communications"},
}


# Plain-language guidance shown in the UI tooltip next to each question.
QUESTION_HELP_TEXT = {
    "tl_01": "Answer Yes if firewall, router, and switch logs are collected centrally and retained for investigations.",
    "tl_02": "Answer Yes if workstation and server logs are collected in your monitoring platform.",
    "tl_03": "Answer Yes if cloud audit/activity logs (AWS/Azure/GCP/SaaS) are enabled and reviewed.",
    "tl_04": "Answer Yes if logs are centralized in one place (SIEM/log platform), not scattered across tools.",
    "tl_05": "Enter the number of days you keep searchable logs for forensic and compliance needs.",
    "tl_06": "Answer Yes if login, logout, privilege changes, and auth failures are logged for critical systems.",
    "dc_01": "Enter what percentage of your assets have active EDR/XDR coverage and telemetry.",
    "dc_02": "Answer Yes if east-west and north-south network traffic is monitored for suspicious behavior.",
    "dc_03": "Answer Yes if detection content/signatures are updated at least weekly or automatically.",
    "dc_04": "Answer Yes if you have detections tailored to your own apps, cloud stack, and business risk.",
    "dc_05": "Answer Yes if phishing, malware, and malicious link protections are enforced for email.",
    "dc_06": "Answer Yes if security alerts are triaged within 24 hours with clear ownership.",
    "iv_01": "Answer Yes if multi-factor authentication is enforced for all user accounts.",
    "iv_02": "Answer Yes if admins/privileged users must always use MFA for access.",
    "iv_03": "Answer Yes if you maintain and review a complete list of privileged accounts.",
    "iv_04": "Answer Yes if service accounts are inventoried, justified, and periodically reviewed.",
    "iv_05": "Answer Yes if privileged sessions are controlled and monitored via PAM or equivalent controls.",
    "iv_06": "Answer Yes if failed logins and anomalous auth patterns are monitored and alerted.",
    "ir_01": "Answer Yes if documented incident response playbooks exist for likely incident scenarios.",
    "ir_02": "Answer Yes if playbooks are tested and updated based on lessons learned.",
    "ir_03": "Answer Yes if incident response roles/on-call responsibilities are clearly assigned.",
    "ir_04": "Answer Yes if pre-approved templates exist for notifying customers, partners, or regulators.",
    "ir_05": "Answer Yes if escalation contacts and decision paths are documented and current.",
    "ir_06": "Answer Yes if tabletop exercises are run at least once per year.",
    "rs_01": "Answer Yes only if your backups follow 3-2-1: 3 copies, 2 media types, and 1 offsite/immutable copy.",
    "rs_02": "Answer Yes if backups are immutable or offline so attackers cannot encrypt/delete them.",
    "rs_03": "Answer Yes if restore tests were completed in the last 6 months with evidence.",
    "rs_04": "Answer Yes if critical systems are inventoried and a disaster recovery plan is documented.",
    "rs_05": "Enter your validated recovery time objective (RTO) in hours for mission-critical services.",
    "rs_06": "Answer Yes if backup admin access uses isolated credentials with MFA/PAM, separate from domain admins.",
}


def _default_help_text(question: dict) -> str:
    q_type = question.get("type")
    if q_type == "boolean":
        return "Answer Yes if this control is consistently implemented and evidenced; otherwise answer No."
    if q_type == "percentage":
        return "Enter your measured percentage (0-100) based on current operational data."
    if q_type == "numeric":
        return "Enter the current measured value from your documented process or monitoring records."
    return "Provide the most accurate current-state answer based on evidence, not assumptions."

RUBRIC = {
    "version": "2.0.0",
    "total_weight": 100,
    "max_domain_score": 5,
    "nist_csf_version": "2.0",
    "methodology_basis": [
        "Common ransomware root causes (CISA #StopRansomware guidance)",
        "MITRE ATT&CK Enterprise technique prevalence",
        "NIST CSF 2.0 impact areas and control effectiveness",
        "CIS Controls v8 Implementation Groups",
        "OWASP Top 10 risk categories",
    ],
    "domains": {
        "telemetry_logging": {
            "name": "Telemetry & Logging",
            "description": "Measures log collection coverage, retention, and centralization",
            "weight": 25,
            "nist_function": "DE",
            "nist_categories": ["DE.CM-3", "DE.CM-9", "DE.AE-3"],
            "questions": [
                {
                    "id": "tl_01",
                    "text": "Are logs collected from network devices (firewalls, switches, routers)?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "DE.CM-3"
                },
                {
                    "id": "tl_02",
                    "text": "Are logs collected from endpoints (workstations, servers)?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "DE.CM-9"
                },
                {
                    "id": "tl_03",
                    "text": "Are logs collected from cloud services (Azure/AWS/GCP)?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "DE.CM-9"
                },
                {
                    "id": "tl_04",
                    "text": "Are logs centralized in a SIEM or log management platform?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "DE.AE-3"
                },
                {
                    "id": "tl_05",
                    "text": "What is your log retention period (days)?",
                    "type": "numeric",
                    "points": 1,
                    "nist_category": "DE.CM-3",
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
                    "points": 1,
                    "nist_category": "DE.CM-3"
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        },
        "detection_coverage": {
            "name": "Detection Coverage",
            "description": "Measures endpoint and network detection capabilities",
            "weight": 20,
            "nist_function": "DE",
            "nist_categories": ["DE.CM-1", "DE.CM-4", "DE.CM-5", "PR.PS-2"],
            "questions": [
                {
                    "id": "dc_01",
                    "text": "What is your endpoint detection (EDR/XDR) coverage relative to your full asset inventory?",
                    "type": "percentage",
                    "points": 1,
                    "nist_category": "DE.CM-1",
                    "tier_options": [
                        {"value": ">95%",        "label": ">95% (Enterprise Standard)",         "score": 1.0},
                        {"value": "80-95%",       "label": "80-95% (Measured Gap)",              "score": 0.75},
                        {"value": "<80%",         "label": "<80% (High Risk)",                   "score": 0.25},
                        {"value": "Unknown / Not Measured", "label": "Unknown / Not Measured",     "score": 0.0},
                    ],
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
                    "points": 1,
                    "nist_category": "DE.CM-1"
                },
                {
                    "id": "dc_03",
                    "text": "Are detection rules/signatures updated at least weekly?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "DE.CM-4"
                },
                {
                    "id": "dc_04",
                    "text": "Do you have custom detection rules for your environment?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "DE.CM-4"
                },
                {
                    "id": "dc_05",
                    "text": "Is email security/anti-phishing protection in place?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "PR.PS-2"
                },
                {
                    "id": "dc_06",
                    "text": "Are alerts triaged within 24 hours?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "DE.CM-5"
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        },
        "identity_visibility": {
            "name": "Identity Visibility",
            "description": "Measures identity security controls and visibility",
            "weight": 20,
            "nist_function": "PR",
            "nist_categories": ["PR.AA-1", "PR.AA-5", "PR.AA-6"],
            "questions": [
                {
                    "id": "iv_01",
                    "text": "Is MFA enforced for all users?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "PR.AA-3"
                },
                {
                    "id": "iv_02",
                    "text": "Is MFA enforced for privileged/admin accounts?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "PR.AA-5"
                },
                {
                    "id": "iv_03",
                    "text": "Is there a complete inventory of privileged accounts?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "ID.AM-1"
                },
                {
                    "id": "iv_04",
                    "text": "Are service accounts inventoried and regularly reviewed?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "ID.AM-1"
                },
                {
                    "id": "iv_05",
                    "text": "Is Privileged Access Management (PAM) solution deployed?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "PR.AA-5"
                },
                {
                    "id": "iv_06",
                    "text": "Are failed login attempts and anomalies monitored?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "DE.CM-3"
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        },
        "ir_process": {
            "name": "IR Playbooks & Process",
            "description": "Measures incident response preparedness and processes",
            "weight": 15,
            "nist_function": "RS",
            "nist_categories": ["RS.MA-1", "RS.CO-2", "RS.AN-3"],
            "questions": [
                {
                    "id": "ir_01",
                    "text": "Do documented IR playbooks exist?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "RS.MA-1"
                },
                {
                    "id": "ir_02",
                    "text": "Have IR playbooks been tested in the last 12 months?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "RS.MA-1"
                },
                {
                    "id": "ir_03",
                    "text": "Is there a defined IR team with clear roles?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "RS.CO-2"
                },
                {
                    "id": "ir_04",
                    "text": "Are there communication templates for incident notification?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "RS.CO-2"
                },
                {
                    "id": "ir_05",
                    "text": "Is there an escalation matrix with contact information?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "RS.CO-2"
                },
                {
                    "id": "ir_06",
                    "text": "Are tabletop exercises conducted at least annually?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "RS.AN-3"
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        },
        "resilience": {
            "name": "Backup/Recovery & Resilience",
            "description": "Measures backup integrity, asset criticality awareness, and recovery capabilities",
            "weight": 20,
            "nist_function": "RC",
            "nist_categories": ["RC.RP-1", "RC.RP-3", "PR.DS-11"],
            "questions": [
                {
                    "id": "rs_01",
                    "text": "Are critical systems backed up according to a 3-2-1 strategy (3 copies, 2 media, 1 offsite/immutable)?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "PR.DS-11"
                },
                {
                    "id": "rs_02",
                    "text": "Are backups stored offline or immutable (air-gapped)?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "PR.DS-11"
                },
                {
                    "id": "rs_03",
                    "text": "Have backup restores been tested in the last 6 months?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "RC.RP-3"
                },
                {
                    "id": "rs_04",
                    "text": "Is there a documented inventory of critical systems and a Disaster Recovery plan?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "ID.AM-2"
                },
                {
                    "id": "rs_05",
                    "text": "What is your validated Recovery Time Objective (RTO) for mission-critical applications?",
                    "type": "numeric",
                    "points": 1,
                    "nist_category": "RC.RP-1",
                    "tier_options": [
                        {"value": "<4hrs",     "label": "<4 Hours (Resilient)",             "score": 1.0},
                        {"value": "4-24hrs",   "label": "4-24 Hours (Moderate)",            "score": 0.75},
                        {"value": "24-72hrs",  "label": "24-72 Hours (Degraded)",           "score": 0.25},
                        {"value": "Undefined / No Target", "label": "Undefined / No Target", "score": 0.0},
                    ],
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
                    "text": "Are backup management interfaces protected by MFA and PAM credentials that are completely separate from primary domain accounts (credential isolation)?",
                    "type": "boolean",
                    "points": 1,
                    "nist_category": "PR.AA-5"
                }
            ],
            "scoring_formula": "Sum points (max 6), scale to 0-5: score = (sum / 6) * 5"
        }
    },
    "maturity_levels": {
        "0-20": {
            "level": 1,
            "name": "Initial",
            "description": "Ad-hoc, reactive security posture",
            "governance_maturity": "No formal governance framework",
            "risk_posture": "Critical",
            "control_effectiveness": "Absent or Ineffective",
        },
        "21-40": {
            "level": 2,
            "name": "Developing",
            "description": "Basic controls in place, gaps exist",
            "governance_maturity": "Informal governance, limited oversight",
            "risk_posture": "High Risk",
            "control_effectiveness": "Partial",
        },
        "41-60": {
            "level": 3,
            "name": "Defined",
            "description": "Documented processes, consistent execution",
            "governance_maturity": "Defined governance policies, inconsistent enforcement",
            "risk_posture": "Moderate Risk",
            "control_effectiveness": "Defined but Not Fully Measured",
        },
        "61-80": {
            "level": 4,
            "name": "Managed",
            "description": "Measured and controlled, proactive approach",
            "governance_maturity": "Managed governance with KPIs and risk oversight",
            "risk_posture": "Low-Moderate Risk",
            "control_effectiveness": "Effective",
        },
        "81-100": {
            "level": 5,
            "name": "Optimized",
            "description": "Continuous improvement, industry-leading",
            "governance_maturity": "Optimized — continuous risk management and board visibility",
            "risk_posture": "Low Risk",
            "control_effectiveness": "Highly Effective — Continuously Improved",
        },
    },
    # Tiered remediation timeline labels (Task 3: Executive Roadmap)
    "remediation_timelines": {
        "30":  {"label": "Immediate",  "range": "0–30 days",   "focus": "Critical risk reduction and quick wins"},
        "60":  {"label": "Near-term",  "range": "30–90 days",  "focus": "Foundation building and process improvement"},
        "90":  {"label": "Strategic",  "range": "90+ days",    "focus": "Governance maturity and operational resilience"},
    },
}


def get_rubric() -> dict:
    """Return the complete rubric definition."""
    rubric = deepcopy(RUBRIC)
    for domain in rubric["domains"].values():
        for question in domain["questions"]:
            qid = question.get("id")
            question["help_text"] = QUESTION_HELP_TEXT.get(qid, _default_help_text(question))
    return rubric


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
                q = deepcopy(question)
                q["help_text"] = QUESTION_HELP_TEXT.get(question_id, _default_help_text(question))
                return q, domain_id
    return None, None


def get_nist_functions() -> dict:
    """Return all NIST CSF 2.0 function definitions."""
    return NIST_FUNCTIONS


def get_domain_nist_function(domain_id: str) -> dict:
    """Return the NIST function for a given domain."""
    domain = RUBRIC["domains"].get(domain_id, {})
    func_id = domain.get("nist_function")
    if func_id:
        return {"id": func_id, **NIST_FUNCTIONS.get(func_id, {})}
    return {}


def get_methodology() -> dict:
    """Return the scoring methodology explanation for the /methodology endpoint."""
    domains_meta = []
    for domain_id, domain in RUBRIC["domains"].items():
        domains_meta.append({
            "domain_id": domain_id,
            "domain_name": domain["name"],
            "weight_pct": domain["weight"],
            "nist_function": domain.get("nist_function"),
            "nist_function_name": NIST_FUNCTIONS.get(domain.get("nist_function", ""), {}).get("name"),
            "nist_categories": domain.get("nist_categories", []),
            "description": domain["description"],
            "question_count": len(domain["questions"]),
            "max_domain_score": RUBRIC["max_domain_score"],
        })
    return {
        "rubric_version": RUBRIC["version"],
        "nist_csf_version": RUBRIC["nist_csf_version"],
        "methodology_basis": RUBRIC["methodology_basis"],
        "total_weight": RUBRIC["total_weight"],
        "max_domain_score": RUBRIC["max_domain_score"],
        "scoring_formula": (
            "For each domain: domain_score (0–5) = (earned_points / max_points) * 5. "
            "Overall score (0–100) = sum of (domain_score / 5) * domain_weight across all domains."
        ),
        "domains": domains_meta,
        "maturity_levels": RUBRIC["maturity_levels"],
        "remediation_timelines": RUBRIC["remediation_timelines"],
    }
