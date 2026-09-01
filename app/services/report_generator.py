"""
Executive Report Generator — Framework Alignment.

Wraps the existing ProfessionalPDFGenerator to ensure framework alignments
(e.g., NIST CSF, CIS Controls) are securely appended to executive reports.

INVARIANTS:
  - Gemini is NEVER used to determine framework mappings
  - Mappings are strictly pulled from the deterministic rubric
  - Missing frameworks are reported as missing
"""

import logging
from typing import Dict, Any, List

from app.reports.pdf import ProfessionalPDFGenerator
from app.core.rubric import get_rubric, get_nist_function_for_domain

logger = logging.getLogger("airs.report_generator")


class ExecutiveReportGenerator:
    """Generates executive reports with guaranteed deterministic framework alignment."""

    def __init__(self):
        # We reuse the existing professional layout generator
        self.pdf_generator = ProfessionalPDFGenerator()

    def generate(self, assessment_data: Dict[str, Any]) -> bytes:
        """
        Generate the report bytes.
        
        This interceptor enriches the assessment data with deterministic 
        framework coverage BEFORE passing it to the PDF renderer.
        """
        # Step 1: Ensure deterministic framework mappings are present
        enriched_data = self._enrich_with_framework_coverage(assessment_data)

        # Step 2: Render the PDF using the existing professional generator
        # Note: The PDF generator must be updated or expected to handle
        # the enriched 'framework_coverage' key if we want it visualized.
        return self.pdf_generator.generate(enriched_data)

    def _enrich_with_framework_coverage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inject deterministic framework mappings into the report data."""
        rubric = get_rubric()
        
        # We build a framework coverage section
        coverage = {
            "nist_csf_version": rubric.get("nist_csf_version", "2.0"),
            "domains": []
        }

        # Analyze the assessment results against the rubric
        for domain_id, domain_def in rubric.get("domains", {}).items():
            func_id = domain_def.get("nist_function")
            categories = domain_def.get("nist_categories", [])
            
            # Extract how the organization scored on this domain if data exists
            domain_score = 0.0
            if "analytics" in data and "domain_scores" in data["analytics"]:
                domain_score = data["analytics"]["domain_scores"].get(domain_id, 0.0)

            coverage["domains"].append({
                "domain_id": domain_id,
                "domain_name": domain_def.get("name", domain_id),
                "nist_function": func_id,
                "nist_categories": categories,
                "score": domain_score
            })

        # Append to the assessment data safely
        # We make a shallow copy to avoid mutating the source dict unnecessarily
        enriched = dict(data)
        enriched["framework_coverage"] = coverage
        
        # We also enforce that the report declares what frameworks are NOT mapped
        # to ensure honesty.
        enriched["framework_limitations"] = {
            "unmapped": ["SOC 2", "ISO 27001"],
            "disclaimer": "This report provides technical evidence alignment. It does not constitute formal certification."
        }

        return enriched
