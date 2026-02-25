"""
Compliance Applicability Engine — deterministic rules.

Maps organization profile attributes to applicable compliance frameworks.
No LLM usage — pure rule-based logic.
"""

import json
import logging
from typing import List, Optional
from app.models.organization import Organization
from app.schemas.compliance import ApplicableFramework

logger = logging.getLogger(__name__)


def get_applicable_frameworks(org: Organization) -> List[ApplicableFramework]:
    """
    Determine which compliance frameworks apply to an organization
    based on its governance profile attributes.
    
    Rules (deterministic, no LLM):
      - processes_phi → HIPAA
      - handles_dod_data → CMMC Level 2 + NIST 800-171
      - processes_cardholder_data → PCI-DSS
      - processes_pii AND "EU" in geo_regions → GDPR
      - processes_pii (any region) → Privacy Framework (recommended)
      - Public SaaS (industry=technology, size>=51) → SOC 2 (recommended)
      - uses_ai_in_production → NIST AI RMF
      - financial_services → NIST CSF 2.0 + FFIEC
      - government_contractor → FedRAMP (recommended)
    """
    frameworks: List[ApplicableFramework] = []

    # Parse geo_regions from JSON text
    geo_regions: List[str] = []
    if org.geo_regions:
        try:
            geo_regions = json.loads(org.geo_regions)
        except (json.JSONDecodeError, TypeError):
            geo_regions = []

    # ── HIPAA ────────────────────────────────────────────────────────────
    if org.processes_phi:
        frameworks.append(ApplicableFramework(
            framework="HIPAA",
            reason="Organization processes Protected Health Information (PHI)",
            mandatory=True,
            reference_url="https://www.hhs.gov/hipaa/index.html",
        ))

    # ── CMMC + NIST 800-171 ─────────────────────────────────────────────
    if org.handles_dod_data:
        frameworks.append(ApplicableFramework(
            framework="CMMC Level 2",
            reason="Organization handles Department of Defense (DoD) data",
            mandatory=True,
            reference_url="https://dodcio.defense.gov/CMMC/",
        ))
        frameworks.append(ApplicableFramework(
            framework="NIST SP 800-171",
            reason="Required for Controlled Unclassified Information (CUI) handling",
            mandatory=True,
            reference_url="https://csrc.nist.gov/publications/detail/sp/800-171/rev-2/final",
        ))

    # ── PCI-DSS ──────────────────────────────────────────────────────────
    if org.processes_cardholder_data:
        frameworks.append(ApplicableFramework(
            framework="PCI-DSS v4.0",
            reason="Organization processes cardholder/payment card data",
            mandatory=True,
            reference_url="https://www.pcisecuritystandards.org/",
        ))

    # ── GDPR ─────────────────────────────────────────────────────────────
    if org.processes_pii and "EU" in geo_regions:
        frameworks.append(ApplicableFramework(
            framework="GDPR",
            reason="Organization processes PII with EU presence/operations",
            mandatory=True,
            reference_url="https://gdpr.eu/",
        ))

    # ── Privacy (general) ────────────────────────────────────────────────
    if org.processes_pii and "EU" not in geo_regions:
        frameworks.append(ApplicableFramework(
            framework="NIST Privacy Framework",
            reason="Organization processes Personally Identifiable Information (PII)",
            mandatory=False,
            reference_url="https://www.nist.gov/privacy-framework",
        ))

    # ── SOC 2 (recommended for SaaS / technology) ───────────────────────
    industry = (org.industry or "").lower()
    if industry in ("technology", "saas", "software"):
        frameworks.append(ApplicableFramework(
            framework="SOC 2 Type II",
            reason="Technology/SaaS organization — SOC 2 expected by customers",
            mandatory=False,
            reference_url="https://www.aicpa.org/soc2",
        ))

    # ── NIST AI RMF ──────────────────────────────────────────────────────
    if org.uses_ai_in_production:
        frameworks.append(ApplicableFramework(
            framework="NIST AI RMF",
            reason="Organization uses AI/ML in production systems",
            mandatory=False,
            reference_url="https://www.nist.gov/artificial-intelligence/ai-risk-management-framework",
        ))

    # ── NIST CSF 2.0 + FFIEC (financial services) ───────────────────────
    if org.financial_services:
        frameworks.append(ApplicableFramework(
            framework="NIST CSF 2.0",
            reason="Financial services organization — NIST CSF adoption expected",
            mandatory=True,
            reference_url="https://www.nist.gov/cyberframework",
        ))
        frameworks.append(ApplicableFramework(
            framework="FFIEC IT Handbook",
            reason="Financial institution subject to FFIEC examination",
            mandatory=True,
            reference_url="https://ithandbook.ffiec.gov/",
        ))

    # ── FedRAMP (government contractor) ──────────────────────────────────
    if org.government_contractor:
        frameworks.append(ApplicableFramework(
            framework="FedRAMP",
            reason="Government contractor — FedRAMP authorization recommended for cloud services",
            mandatory=False,
            reference_url="https://www.fedramp.gov/",
        ))

    logger.info(
        f"Compliance engine: org={org.id} -> {len(frameworks)} applicable frameworks"
    )

    return frameworks
