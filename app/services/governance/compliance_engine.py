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

# ── Regions ──────────────────────────────────────────────────────────
# One code per jurisdiction. "GCC" expands to the six Gulf states.
GULF_STATES = ("AE", "SA", "QA", "BH", "KW", "OM")

_REGION_ALIASES = {
    "UAE": "AE", "UNITED ARAB EMIRATES": "AE", "EMIRATES": "AE",
    "KSA": "SA", "SAUDI ARABIA": "SA", "SAUDI": "SA",
    "QATAR": "QA", "BAHRAIN": "BH", "KUWAIT": "KW", "OMAN": "OM",
    "GB": "UK", "UNITED KINGDOM": "UK", "GREAT BRITAIN": "UK", "ENGLAND": "UK",
    "USA": "US", "UNITED STATES": "US", "U.S.": "US",
    "INDIA": "IN", "CANADA": "CA", "AUSTRALIA": "AU", "SINGAPORE": "SG",
    "EUROPE": "EU", "EUROPEAN UNION": "EU",
}

_EU_MEMBER_STATES = {
    "AUSTRIA", "BELGIUM", "BULGARIA", "CROATIA", "CYPRUS", "CZECHIA", "CZECH REPUBLIC",
    "DENMARK", "ESTONIA", "FINLAND", "FRANCE", "GERMANY", "GREECE", "HUNGARY", "IRELAND",
    "ITALY", "LATVIA", "LITHUANIA", "LUXEMBOURG", "MALTA", "NETHERLANDS", "POLAND",
    "PORTUGAL", "ROMANIA", "SLOVAKIA", "SLOVENIA", "SPAIN", "SWEDEN",
}

# What ResilAI reads can only ever support the security duty of a privacy law.
_PRIVACY_NOTE = (
    "ResilAI's access, device and backup checks can support the duty to keep personal "
    "data secure. Consent, notices and requests from individuals are outside what it reads."
)

# Privacy laws that apply when the organisation handles personal data in a region.
# (region, framework, jurisdiction, reason detail, reference_url)
_REGIONAL_PRIVACY_LAWS = (
    ("UK", "UK GDPR and Data Protection Act 2018", "United Kingdom",
     "Organisation handles personal data in the United Kingdom",
     "https://ico.org.uk/for-organisations/"),
    ("AE", "UAE PDPL (Federal Decree-Law No. 45 of 2021)", "United Arab Emirates",
     "Organisation handles personal data in the UAE. The DIFC and ADGM free zones have their own data protection laws",
     "https://u.ae/en/about-the-uae/digital-uae/data/data-protection-laws"),
    ("SA", "Saudi PDPL (Personal Data Protection Law)", "Saudi Arabia",
     "Organisation handles personal data in Saudi Arabia",
     "https://sdaia.gov.sa/en/"),
    ("QA", "Qatar PDPPL (Law No. 13 of 2016)", "Qatar",
     "Organisation handles personal data in Qatar",
     "https://www.ncsa.gov.qa/"),
    ("BH", "Bahrain PDPL (Law No. 30 of 2018)", "Bahrain",
     "Organisation handles personal data in Bahrain",
     "http://www.pdp.gov.bh/"),
    ("KW", "Kuwait CITRA Data Privacy Protection Regulation", "Kuwait",
     "Organisation handles personal data in Kuwait through telecom or IT services",
     "https://www.citra.gov.kw/"),
    ("OM", "Oman PDPL (Royal Decree 6/2022)", "Oman",
     "Organisation handles personal data in Oman",
     "https://www.mtcit.gov.om/"),
    ("IN", "India DPDP Act 2023", "India",
     "Organisation handles digital personal data in India",
     "https://www.meity.gov.in/"),
    ("CA", "PIPEDA", "Canada",
     "Organisation handles personal information in the course of commercial activity in Canada",
     "https://www.priv.gc.ca/"),
    ("AU", "Australian Privacy Act 1988", "Australia",
     "Organisation handles personal information in Australia. Health service providers are covered whatever their size",
     "https://www.oaic.gov.au/"),
    ("SG", "Singapore PDPA 2012", "Singapore",
     "Organisation handles personal data in Singapore",
     "https://www.pdpc.gov.sg/"),
)


def normalise_regions(geo_regions: Optional[List[str]], country: Optional[str] = None) -> set:
    """Turn the stored region list (and the organisation's country) into region codes."""
    codes: set = set()
    for raw in [*(geo_regions or []), country]:
        if not isinstance(raw, str) or not raw.strip():
            continue
        name = raw.strip().upper()
        if name == "GCC":
            codes.update(GULF_STATES)
        elif name in _EU_MEMBER_STATES:
            codes.add("EU")
        else:
            codes.add(_REGION_ALIASES.get(name, name))
    return codes


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
    regions = normalise_regions(geo_regions, getattr(org, "country", None))
    if "EU" in regions and "EU" not in geo_regions:
        geo_regions = [*geo_regions, "EU"]
    # US-only laws are not listed for an organisation that says it operates elsewhere.
    us_scope = not regions or "US" in regions

    # ── HIPAA ────────────────────────────────────────────────────────────
    if org.processes_phi and us_scope:
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
            reference_url="https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services",
        ))

    # ── NIST AI RMF ──────────────────────────────────────────────────────
    if org.uses_ai_in_production:
        frameworks.append(ApplicableFramework(
            framework="NIST AI RMF",
            reason="Organization uses AI/ML in production systems",
            mandatory=False,
            reference_url="https://www.nist.gov/itl/ai-risk-management-framework",
        ))

    # ── NIST CSF 2.0 + FFIEC (financial services) ───────────────────────
    if org.financial_services:
        frameworks.append(ApplicableFramework(
            framework="NIST CSF 2.0",
            reason="Financial services organization — NIST CSF adoption expected",
            mandatory=True,
            reference_url="https://www.nist.gov/cyberframework",
        ))
    if org.financial_services and us_scope:
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

    # ── European Union ───────────────────────────────────────────────────
    if "EU" in regions:
        if org.uses_ai_in_production:
            # Regulation (EU) 2024/1689. Dates as amended by the 2026 Digital
            # Omnibus on AI; check the Official Journal before quoting them.
            frameworks.append(ApplicableFramework(
                framework="EU AI Act (Regulation (EU) 2024/1689)",
                reason=(
                    "Organisation uses AI and operates in the EU. Duties depend on the risk "
                    "class of each AI system and on your role (provider or deployer). AI literacy "
                    "(Article 4) and the banned practices (Article 5) already apply; high-risk "
                    "duties for stand-alone systems apply from 2 December 2027"
                ),
                mandatory=True,
                reference_url="https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
                jurisdiction="European Union",
                evidence_note=(
                    "ResilAI's access, device, backup and cloud checks can support the "
                    "cybersecurity part of Article 15 for the infrastructure an AI system runs on. "
                    "The AI systems page records your systems and gives a first risk class from "
                    "your own answers. ResilAI does not verify those answers or assess risk "
                    "management, data governance, logging, transparency or human oversight."
                ),
            ))
        frameworks.append(ApplicableFramework(
            framework="NIS2 Directive (EU) 2022/2555",
            reason=(
                "Applies to medium and large organisations in listed sectors, including "
                "healthcare and managed IT services. Check the national law of each member state"
            ),
            mandatory=False,
            reference_url="https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
            jurisdiction="European Union",
            evidence_note=(
                "ResilAI checks can support Article 21(2): (c) backup and recovery, "
                "(i) access control, (j) multi-factor authentication."
            ),
        ))
        if org.financial_services:
            frameworks.append(ApplicableFramework(
                framework="DORA (Regulation (EU) 2022/2554)",
                reason="Financial entity operating in the EU",
                mandatory=True,
                reference_url="https://eur-lex.europa.eu/eli/reg/2022/2554/oj",
                jurisdiction="European Union",
                evidence_note=(
                    "ResilAI checks can support Article 9 (protection and prevention) and "
                    "Article 12 (backup and restoration)."
                ),
            ))

    # ── Privacy laws by region ───────────────────────────────────────────
    if org.processes_pii:
        for code, name, jurisdiction, detail, url in _REGIONAL_PRIVACY_LAWS:
            if code in regions:
                frameworks.append(ApplicableFramework(
                    framework=name,
                    reason=detail,
                    mandatory=True,
                    reference_url=url,
                    jurisdiction=jurisdiction,
                    evidence_note=_PRIVACY_NOTE,
                ))

    # ── United Kingdom ───────────────────────────────────────────────────
    if "UK" in regions:
        frameworks.append(ApplicableFramework(
            framework="Cyber Essentials",
            reason="UK government-backed baseline, often asked for by UK customers and insurers",
            mandatory=False,
            reference_url="https://www.ncsc.gov.uk/cyberessentials/overview",
            jurisdiction="United Kingdom",
            evidence_note="ResilAI checks can support the user access control requirement.",
        ))

    # ── Gulf states ──────────────────────────────────────────────────────
    if "AE" in regions and org.processes_phi:
        frameworks.append(ApplicableFramework(
            framework="UAE ICT Health Law (Federal Law No. 2 of 2019)",
            reason="Organisation handles health information in the UAE",
            mandatory=True,
            reference_url="https://mohap.gov.ae/",
            jurisdiction="United Arab Emirates",
            evidence_note=_PRIVACY_NOTE,
        ))
    if "SA" in regions:
        frameworks.append(ApplicableFramework(
            framework="Saudi NCA Essential Cybersecurity Controls (ECC-2:2024)",
            reason=(
                "Mandatory for government bodies and operators of critical national "
                "infrastructure in Saudi Arabia; a common baseline for their suppliers"
            ),
            mandatory=False,
            reference_url="https://nca.gov.sa/",
            jurisdiction="Saudi Arabia",
            evidence_note=(
                "ResilAI checks can support ECC 2-2 (identity and access management) "
                "and 2-9 (backup and recovery)."
            ),
        ))
        if org.uses_ai_in_production:
            frameworks.append(ApplicableFramework(
                framework="SDAIA AI Ethics Principles",
                reason="Organisation uses AI in Saudi Arabia. Guidance, not a binding law",
                mandatory=False,
                reference_url="https://sdaia.gov.sa/en/",
                jurisdiction="Saudi Arabia",
                evidence_note="ResilAI does not assess AI ethics principles.",
            ))

    # ── Australia ────────────────────────────────────────────────────────
    if "AU" in regions:
        frameworks.append(ApplicableFramework(
            framework="ASD Essential Eight",
            reason="Australian government baseline, widely used as a maturity benchmark",
            mandatory=False,
            reference_url="https://www.cyber.gov.au/resources-business-and-government/essential-cyber-security/essential-eight",
            jurisdiction="Australia",
            evidence_note="ResilAI checks can support multi-factor authentication and regular backups.",
        ))

    # ── International standards (outside the US) ─────────────────────────
    if regions - {"US"}:
        frameworks.append(ApplicableFramework(
            framework="ISO/IEC 27001",
            reason="International security management standard, commonly requested by customers outside the US",
            mandatory=False,
            reference_url="https://www.iso.org/standard/27001",
            jurisdiction="International",
        ))
        if org.uses_ai_in_production:
            frameworks.append(ApplicableFramework(
                framework="ISO/IEC 42001",
                reason="International AI management system standard; supports EU AI Act and Gulf AI governance work",
                mandatory=False,
                reference_url="https://www.iso.org/standard/81230.html",
                jurisdiction="International",
                evidence_note="ResilAI does not assess an AI management system.",
            ))

    logger.info(
        f"Compliance engine: org={org.id} -> {len(frameworks)} applicable frameworks"
    )

    return frameworks
