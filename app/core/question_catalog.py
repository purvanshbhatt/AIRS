"""
Question Suggestion Catalog

Static, config-driven metadata for every rubric question.
Used by the suggestion engine to recommend questions based on
maturity, control function, effort, and impact.

This file is the SINGLE SOURCE OF TRUTH for enrichment metadata.
It does NOT affect scoring — scoring uses rubric.py only.

Framework tag conventions:
  - NIST-CSF-<category>     → NIST CSF 2.0 category (e.g. "NIST-CSF-DE.CM-3")
  - NIST-AI-<id>            → NIST AI RMF (e.g. "NIST-AI-MAP-1.1")
  - CIS-<control>           → CIS Controls v8 (e.g. "CIS-8.2")
  - OWASP-AI-<id>           → OWASP AI Security (e.g. "OWASP-AI-01")
"""

from typing import Dict, List, Any


# Valid enums (mirrored in SQLAlchemy model for persistence)
MATURITY_LEVELS = ("basic", "managed", "advanced")
EFFORT_LEVELS = ("low", "medium", "high")
IMPACT_LEVELS = ("low", "medium", "high")
CONTROL_FUNCTIONS = ("govern", "identify", "protect", "detect", "respond", "recover")


# ---------------------------------------------------------------------------
# Catalog: question_id → enrichment metadata
# ---------------------------------------------------------------------------
QUESTION_CATALOG: Dict[str, Dict[str, Any]] = {
    # ── Telemetry & Logging (detect) ──
    "tl_01": {
        "framework_tags": ["NIST-CSF-DE.CM-3", "CIS-8.2", "NIST-AI-MG-2.4"],
        "maturity_level": "basic",
        "effort_level": "low",
        "impact_level": "high",
        "control_function": "detect",
    },
    "tl_02": {
        "framework_tags": ["NIST-CSF-DE.CM-9", "CIS-8.5", "NIST-AI-MG-2.4"],
        "maturity_level": "basic",
        "effort_level": "low",
        "impact_level": "high",
        "control_function": "detect",
    },
    "tl_03": {
        "framework_tags": ["NIST-CSF-DE.CM-9", "CIS-8.11", "OWASP-AI-09"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "high",
        "control_function": "detect",
    },
    "tl_04": {
        "framework_tags": ["NIST-CSF-DE.AE-3", "CIS-8.9", "NIST-AI-MG-3.2"],
        "maturity_level": "managed",
        "effort_level": "high",
        "impact_level": "high",
        "control_function": "detect",
    },
    "tl_05": {
        "framework_tags": ["NIST-CSF-DE.CM-3", "CIS-8.1"],
        "maturity_level": "advanced",
        "effort_level": "medium",
        "impact_level": "medium",
        "control_function": "detect",
    },
    "tl_06": {
        "framework_tags": ["NIST-CSF-DE.CM-3", "CIS-8.5", "OWASP-AI-06"],
        "maturity_level": "basic",
        "effort_level": "low",
        "impact_level": "high",
        "control_function": "detect",
    },

    # ── Detection Coverage (detect) ──
    "dc_01": {
        "framework_tags": ["NIST-CSF-DE.CM-1", "CIS-13.1", "NIST-AI-MG-2.4"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "high",
        "control_function": "detect",
    },
    "dc_02": {
        "framework_tags": ["NIST-CSF-DE.CM-1", "CIS-13.3"],
        "maturity_level": "managed",
        "effort_level": "high",
        "impact_level": "high",
        "control_function": "detect",
    },
    "dc_03": {
        "framework_tags": ["NIST-CSF-DE.CM-4", "CIS-13.7"],
        "maturity_level": "managed",
        "effort_level": "low",
        "impact_level": "medium",
        "control_function": "detect",
    },
    "dc_04": {
        "framework_tags": ["NIST-CSF-DE.CM-4", "CIS-13.8", "NIST-AI-MG-3.2"],
        "maturity_level": "advanced",
        "effort_level": "high",
        "impact_level": "high",
        "control_function": "detect",
    },
    "dc_05": {
        "framework_tags": ["NIST-CSF-PR.PS-2", "CIS-9.6", "OWASP-AI-02"],
        "maturity_level": "basic",
        "effort_level": "low",
        "impact_level": "high",
        "control_function": "protect",
    },
    "dc_06": {
        "framework_tags": ["NIST-CSF-DE.CM-5", "CIS-13.1"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "medium",
        "control_function": "detect",
    },

    # ── Identity Visibility (protect / identify) ──
    "iv_01": {
        "framework_tags": ["NIST-CSF-PR.AA-3", "CIS-6.3", "OWASP-AI-06"],
        "maturity_level": "basic",
        "effort_level": "low",
        "impact_level": "high",
        "control_function": "protect",
    },
    "iv_02": {
        "framework_tags": ["NIST-CSF-PR.AA-5", "CIS-6.5"],
        "maturity_level": "basic",
        "effort_level": "low",
        "impact_level": "high",
        "control_function": "protect",
    },
    "iv_03": {
        "framework_tags": ["NIST-CSF-ID.AM-1", "CIS-5.1", "NIST-AI-MAP-1.1"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "medium",
        "control_function": "identify",
    },
    "iv_04": {
        "framework_tags": ["NIST-CSF-ID.AM-1", "CIS-5.4"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "medium",
        "control_function": "identify",
    },
    "iv_05": {
        "framework_tags": ["NIST-CSF-PR.AA-5", "CIS-6.8", "NIST-AI-GV-1.3"],
        "maturity_level": "advanced",
        "effort_level": "high",
        "impact_level": "high",
        "control_function": "protect",
    },
    "iv_06": {
        "framework_tags": ["NIST-CSF-DE.CM-3", "CIS-8.11", "OWASP-AI-06"],
        "maturity_level": "basic",
        "effort_level": "low",
        "impact_level": "medium",
        "control_function": "detect",
    },

    # ── IR Playbooks & Process (respond) ──
    "ir_01": {
        "framework_tags": ["NIST-CSF-RS.MA-1", "CIS-17.4", "NIST-AI-GV-4.1"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "high",
        "control_function": "respond",
    },
    "ir_02": {
        "framework_tags": ["NIST-CSF-RS.MA-1", "CIS-17.6"],
        "maturity_level": "advanced",
        "effort_level": "high",
        "impact_level": "high",
        "control_function": "respond",
    },
    "ir_03": {
        "framework_tags": ["NIST-CSF-RS.CO-2", "CIS-17.1"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "high",
        "control_function": "respond",
    },
    "ir_04": {
        "framework_tags": ["NIST-CSF-RS.CO-2", "CIS-17.2"],
        "maturity_level": "managed",
        "effort_level": "low",
        "impact_level": "medium",
        "control_function": "respond",
    },
    "ir_05": {
        "framework_tags": ["NIST-CSF-RS.CO-2", "CIS-17.3"],
        "maturity_level": "basic",
        "effort_level": "low",
        "impact_level": "medium",
        "control_function": "respond",
    },
    "ir_06": {
        "framework_tags": ["NIST-CSF-RS.AN-3", "CIS-17.8", "NIST-AI-GV-4.3"],
        "maturity_level": "advanced",
        "effort_level": "high",
        "impact_level": "high",
        "control_function": "respond",
    },

    # ── Resilience (recover) ──
    "rs_01": {
        "framework_tags": ["NIST-CSF-PR.DS-11", "CIS-11.2", "OWASP-AI-07"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "high",
        "control_function": "recover",
    },
    "rs_02": {
        "framework_tags": ["NIST-CSF-PR.DS-11", "CIS-11.3"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "high",
        "control_function": "recover",
    },
    "rs_03": {
        "framework_tags": ["NIST-CSF-RC.RP-3", "CIS-11.5"],
        "maturity_level": "advanced",
        "effort_level": "high",
        "impact_level": "high",
        "control_function": "recover",
    },
    "rs_04": {
        "framework_tags": ["NIST-CSF-ID.AM-2", "CIS-11.1", "NIST-AI-MAP-3.4"],
        "maturity_level": "managed",
        "effort_level": "medium",
        "impact_level": "high",
        "control_function": "identify",
    },
    "rs_05": {
        "framework_tags": ["NIST-CSF-RC.RP-1", "CIS-11.4", "NIST-AI-MG-4.1"],
        "maturity_level": "advanced",
        "effort_level": "high",
        "impact_level": "high",
        "control_function": "recover",
    },
    "rs_06": {
        "framework_tags": ["NIST-CSF-PR.AA-5", "CIS-6.8"],
        "maturity_level": "advanced",
        "effort_level": "medium",
        "impact_level": "high",
        "control_function": "protect",
    },
}


def get_question_metadata(question_id: str) -> Dict[str, Any] | None:
    """Return enrichment metadata for a single question, or None."""
    return QUESTION_CATALOG.get(question_id)


def get_all_question_metadata() -> Dict[str, Dict[str, Any]]:
    """Return the full catalog."""
    return QUESTION_CATALOG


def get_questions_by_control_function(function: str) -> List[str]:
    """Return question IDs that map to a given NIST CSF control function."""
    function = function.lower()
    return [
        qid for qid, meta in QUESTION_CATALOG.items()
        if meta["control_function"] == function
    ]


def get_questions_by_maturity(level: str) -> List[str]:
    """Return question IDs at a given maturity tier."""
    level = level.lower()
    return [
        qid for qid, meta in QUESTION_CATALOG.items()
        if meta["maturity_level"] == level
    ]
