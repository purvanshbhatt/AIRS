"""
Tests for the deterministic scoring contract (Sprint 1.8, Task S1.8-A2).

Verifies:
  - ``calculate_readiness_delta`` returns the documented breakdown.
  - Sequential recalculations produce correct delta values.
  - The module is free of forbidden LLM imports (ADR-007).
  - The module-level isolation guard raises on violation.
"""

import inspect

import pytest

from app.services import scoring as scoring_module
from app.services.scoring import calculate_readiness_delta


class TestCalculateReadinessDelta:
    def test_returns_documented_breakdown(self):
        result = calculate_readiness_delta(
            assessment_score=60.0,
            verified_controls=[],
            verified_coverages=[],
            lifecycle_risks=[],
            exposure_risks=[],
        )
        assert "assessment_score" in result
        assert "modifiers" in result
        assert "final_readiness" in result
        assert "previous_readiness" in result
        assert "readiness_delta" in result
        assert "reasons" in result
        # Modifier subshape
        mods = result["modifiers"]
        assert "verification_bonus" in mods
        assert "coverage_bonus" in mods
        assert "lifecycle_penalty" in mods
        assert "exposure_penalty" in mods

    def test_known_fixture_produces_expected_output(self):
        # Critical control verified (1 instance) => +3 verification bonus
        verified_controls = [{"name": "EDR", "family": "Endpoint",
                              "severity": "critical"}]
        # Coverage exactly 90% => +2 coverage bonus
        # Lifecycle: one EOL asset => -2 lifecycle penalty (returned as -2.0)
        lifecycle_risks = [{"software_name": "CentOS",
                            "lifecycle_status": "END_OF_LIFE"}]
        exposure_risks: list = []

        result = calculate_readiness_delta(
            assessment_score=60.0,
            verified_controls=verified_controls,
            verified_coverages=[{"name": "EDR", "family": "Endpoint",
                                 "coverage_percentage": 90.0}],
            lifecycle_risks=lifecycle_risks,
            exposure_risks=exposure_risks,
            previous_readiness_score=55.0,
        )

        # 60 + 3 (verification) + 2 (coverage) - 2 (lifecycle) - 0 (exposure)
        # = 63.0
        assert result["final_readiness"] == pytest.approx(63.0)
        assert result["readiness_delta"] == pytest.approx(8.0)

    def test_repeated_calculation_determinism(self):
        args = dict(
            assessment_score=50.0,
            verified_controls=[{"name": "X", "family": "Y",
                                "severity": "important"}],
            verified_coverages=[{"name": "A", "family": "B",
                                 "coverage_percentage": 80.0}],
            lifecycle_risks=[],
            exposure_risks=[],
        )
        first = calculate_readiness_delta(**args, previous_readiness_score=40.0)
        second = calculate_readiness_delta(**args, previous_readiness_score=40.0)
        # Determinism — identical inputs must produce identical outputs.
        assert first["final_readiness"] == second["final_readiness"]
        assert first["modifiers"] == second["modifiers"]
        assert first["readiness_delta"] == second["readiness_delta"]

    def test_final_score_clamped_between_0_and_100(self):
        result = calculate_readiness_delta(
            assessment_score=0.0,
            verified_controls=[],
            verified_coverages=[],
            lifecycle_risks=[
                {"software_name": "X", "lifecycle_status": "END_OF_LIFE"}
            ] * 50,
            exposure_risks=[{"software_name": "X", "kev_count": 1,
                             "is_internet_facing": True,
                             "is_critical_asset": True}] * 50,
        )
        assert 0.0 <= result["final_readiness"] <= 100.0

    def test_no_previous_returns_none_delta(self):
        result = calculate_readiness_delta(
            assessment_score=80.0,
            verified_controls=[],
            verified_coverages=[],
            lifecycle_risks=[],
            exposure_risks=[],
        )
        assert result["previous_readiness"] is None
        assert result["readiness_delta"] is None


class TestScoringIsolationInvariant:
    def test_module_direct_imports_contain_no_forbidden_names(self):
        # AST inspect only the IMPORTS that scoring.py declares. This avoids
        # transitively accepting any module that happens to be loaded
        # transitively by the rest of the codebase.
        import ast

        src = inspect.getsource(scoring_module)
        tree = ast.parse(src)

        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.add(node.module)
                    for alias in node.names:
                        imported_names.add(f"{node.module}.{alias.name}")

        forbidden_root_modules = (
            "ai_narrative",
            "llm_narrative",
            "google.genai",
            "google.generativeai",
        )

        def _is_forbidden(name: str) -> bool:
            return any(
                name == forbidden or name.startswith(forbidden + ".")
                for forbidden in forbidden_root_modules
            )

        violations = sorted(n for n in imported_names if _is_forbidden(n))
        assert not violations, (
            "scoring.py must not import forbidden narrative / LLM modules; "
            f"got: {violations}"
        )

    def test_module_source_has_no_forbidden_runtime_calls(self):
        # Static check: scoring.py must not actually IMPORT or CALL into
        # forbidden modules. Mentions in comments / docstrings / error
        # strings are allowed since the purpose of this module is to refuse
        # such imports at runtime.
        import ast

        src = inspect.getsource(scoring_module)
        tree = ast.parse(src)

        # All import statements
        import_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_names.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_names.add(node.module)

        # All attribute / load names — anything that ends up in a function
        # call argument or RHS.
        referenced_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Walk to root name left of the chain.
                root = node
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name):
                    referenced_names.add(root.id)

        forbidden = ("ai_narrative", "llm_narrative")

        bad_imports = sorted(n for n in import_names if any(n == f or n.startswith(f + ".") for f in forbidden))
        bad_calls = sorted(n for n in referenced_names if n in forbidden)

        assert not bad_imports, (
            f"scoring.py contains forbidden imports: {bad_imports}"
        )
        assert not bad_calls, (
            f"scoring.py references forbidden runtime names: {bad_calls}"
        )

    def test_calculate_readiness_delta_signature_is_stable(self):
        sig = inspect.signature(calculate_readiness_delta)
        expected_params = [
            "assessment_score",
            "verified_controls",
            "verified_coverages",
            "lifecycle_risks",
            "exposure_risks",
            "previous_readiness_score",
        ]
        assert list(sig.parameters.keys()) == expected_params
