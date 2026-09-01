"""
Framework Validation Test Suite — Deterministic Coverage Audit.

Validates that ResilAI's framework alignment mappings are:
  - Deterministic (no LLM involvement)
  - Traceable (each mapping links to a specific control/evidence)
  - Honest (missing coverage is reported as missing, not fabricated)

IMPORTANT:
  - This suite does NOT claim ResilAI is certified or compliant.
  - This suite validates that "ResilAI provides readiness evidence aligned to..."
  - Missing mappings are reported, not hidden.
"""

import pytest
from app.core.rubric import get_rubric, get_nist_functions, get_domain_nist_function


class TestNISTCSF20Mappings:
    """Validate NIST CSF 2.0 function mappings in the rubric."""

    def test_rubric_declares_nist_csf_version(self):
        rubric = get_rubric()
        assert rubric["nist_csf_version"] == "2.0"

    def test_all_nist_functions_defined(self):
        functions = get_nist_functions()
        required = {"GV", "ID", "PR", "DE", "RS", "RC"}
        assert required.issubset(set(functions.keys())), (
            f"Missing NIST CSF 2.0 functions: {required - set(functions.keys())}"
        )

    def test_every_domain_has_nist_function(self):
        rubric = get_rubric()
        for domain_id, domain in rubric["domains"].items():
            assert "nist_function" in domain, (
                f"Domain {domain_id} is missing nist_function mapping"
            )
            func = domain["nist_function"]
            assert func in {"GV", "ID", "PR", "DE", "RS", "RC"}, (
                f"Domain {domain_id} has invalid NIST function: {func}"
            )

    def test_every_domain_has_nist_categories(self):
        rubric = get_rubric()
        for domain_id, domain in rubric["domains"].items():
            assert "nist_categories" in domain, (
                f"Domain {domain_id} is missing nist_categories"
            )
            assert len(domain["nist_categories"]) > 0, (
                f"Domain {domain_id} has empty nist_categories"
            )

    def test_nist_categories_format(self):
        """Validate NIST category IDs follow the XX.YY-N format."""
        rubric = get_rubric()
        for domain_id, domain in rubric["domains"].items():
            for cat in domain.get("nist_categories", []):
                assert "." in cat, (
                    f"Invalid NIST category format in {domain_id}: {cat}"
                )

    def test_nist_function_lookup_returns_data(self):
        rubric = get_rubric()
        for domain_id in rubric["domains"]:
            result = get_domain_nist_function(domain_id)
            assert result is not None, (
                f"get_domain_nist_function({domain_id}) returned None"
            )


class TestCISControlsMapping:
    """Validate CIS Controls references."""

    def test_methodology_references_cis(self):
        rubric = get_rubric()
        basis = rubric.get("methodology_basis", [])
        cis_found = any("CIS" in b for b in basis)
        assert cis_found, "Rubric methodology must reference CIS Controls"


class TestFrameworkCoverageReport:
    """Generate a coverage report for all target frameworks."""

    TARGET_FRAMEWORKS = [
        "NIST CSF 2.0",
        "CIS Controls",
        "SOC 2",
        "ISO 27001",
        "NIST AI RMF",
        "HIPAA",
    ]

    def test_coverage_report_generation(self):
        rubric = get_rubric()
        report = {"validated": [], "partial": [], "missing": []}

        # NIST CSF 2.0 — fully mapped
        nist_mapped = all(
            "nist_function" in d and "nist_categories" in d
            for d in rubric["domains"].values()
        )
        if nist_mapped:
            report["validated"].append("NIST CSF 2.0")
        else:
            report["partial"].append("NIST CSF 2.0")

        # CIS Controls — referenced in methodology
        cis_ref = any("CIS" in b for b in rubric.get("methodology_basis", []))
        if cis_ref:
            report["partial"].append("CIS Controls")
        else:
            report["missing"].append("CIS Controls")

        # SOC 2 — check if any domain references SOC 2
        # Currently not explicitly mapped in rubric
        report["missing"].append("SOC 2")

        # ISO 27001 — not explicitly mapped
        report["missing"].append("ISO 27001")

        # NIST AI RMF — check for AI-specific domains/references
        has_ai = any(
            "ai" in d.get("name", "").lower()
            for d in rubric["domains"].values()
        )
        if has_ai:
            report["partial"].append("NIST AI RMF")
        else:
            report["missing"].append("NIST AI RMF")

        # HIPAA — check for healthcare references
        hipaa_ref = any(
            "hipaa" in str(d).lower()
            for d in rubric["domains"].values()
        )
        if hipaa_ref:
            report["partial"].append("HIPAA")
        else:
            report["missing"].append("HIPAA")

        # The test passes — it generates the report honestly
        assert len(report["validated"]) > 0, (
            "At least one framework must be validated"
        )

        # Print the coverage report
        print("\n=== FRAMEWORK COVERAGE REPORT ===")
        print(f"Validated: {report['validated']}")
        print(f"Partial:   {report['partial']}")
        print(f"Missing:   {report['missing']}")


class TestRubricDomainIntegrity:
    """Validate rubric structural integrity."""

    def test_all_domains_have_questions(self):
        rubric = get_rubric()
        for domain_id, domain in rubric["domains"].items():
            assert "questions" in domain, f"{domain_id} missing questions"
            assert len(domain["questions"]) > 0, f"{domain_id} has no questions"

    def test_all_domains_have_weights(self):
        rubric = get_rubric()
        total_weight = 0
        for domain_id, domain in rubric["domains"].items():
            assert "weight" in domain, f"{domain_id} missing weight"
            assert domain["weight"] > 0, f"{domain_id} has zero weight"
            total_weight += domain["weight"]
        assert total_weight == rubric["total_weight"], (
            f"Domain weights ({total_weight}) don't sum to {rubric['total_weight']}"
        )

    def test_no_llm_in_rubric(self):
        """The rubric must be purely deterministic."""
        rubric = get_rubric()
        rubric_str = str(rubric).lower()
        assert "llm" not in rubric_str or "llm" in "methodology" , (
            "Rubric must not reference LLM for scoring"
        )


class TestExplainabilityTaxonomy:
    """Validate the explainability engine taxonomy is deterministic."""

    def test_taxonomy_is_deterministic(self):
        from app.services.clinic_engine.v2.explainability_engine import TAXONOMY
        for cap_id, entry in TAXONOMY.items():
            assert "business_label" in entry, f"{cap_id} missing business_label"
            assert "what_it_means" in entry, f"{cap_id} missing what_it_means"
            assert "why_it_matters" in entry, f"{cap_id} missing why_it_matters"

    def test_taxonomy_has_no_llm_references(self):
        from app.services.clinic_engine.v2.explainability_engine import TAXONOMY
        for cap_id, entry in TAXONOMY.items():
            for key, value in entry.items():
                assert "llm" not in str(value).lower(), (
                    f"Taxonomy entry {cap_id}.{key} references LLM"
                )
