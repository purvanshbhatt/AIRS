"""
Methodology endpoint — GET /api/v1/methodology

Returns the transparent scoring methodology so that auditors,
customers, and Big-4 consulting partners can validate how the
readiness score is derived.
"""

from fastapi import APIRouter
from app.core.rubric import get_methodology

router = APIRouter()


@router.get(
    "/methodology",
    summary="Scoring Methodology",
    description=(
        "Returns the transparent, human-readable scoring methodology for the ResilAI "
        "Incident Readiness platform.  Exposes domain weights, NIST CSF 2.0 function "
        "mappings, the evidence basis for each weight (MITRE ATT&CK prevalence, CISA "
        "ransomware guidance, NIST impact areas), maturity-level definitions with "
        "Governance Maturity / Risk Posture / Control Effectiveness labels, and "
        "remediation-timeline tier definitions (Immediate / Near-term / Strategic)."
    ),
    responses={
        200: {
            "description": (
                "Scoring methodology including domain weights, NIST CSF 2.0 mappings, "
                "maturity levels with enterprise risk terminology, and timeline tiers."
            )
        }
    },
)
async def get_scoring_methodology():
    """
    /api/v1/methodology

    Explicitly designed for:
    - Security auditors validating assessment rigour
    - Big-4 consulting presentations
    - Customer trust and procurement due-diligence
    - Verifying NIST CSF 2.0 alignment

    The payload includes:
    - ``methodology_basis``: list of industry frameworks and threat-intel sources used
    - ``domains``: per-domain weight, NIST function/category, and question count
    - ``maturity_levels``: scoring ranges with Governance Maturity, Risk Posture, and
      Control Effectiveness labels
    - ``remediation_timelines``: Immediate / Near-term / Strategic tier definitions
    """
    return get_methodology()
