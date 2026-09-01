"""
Tests for the Readiness Driver extraction module (Sprint 1.8, Task S1.8-A3).

Covers:
  - Top-5 positive drivers sorted by magnitude (descending).
  - Top-5 negative drivers sorted by magnitude (ascending, most negative first).
  - Zero-impact drivers are excluded.
  - Empty inputs return empty lists (no crash, no LLM call).
  - extract_action_items renders a deterministic 'Executive Actions' list.
  - Module never imports forbidden LLM modules.
"""

import inspect
import ast

import pytest

from app.services import readiness_drivers as drivers_module
from app.services.readiness_drivers import extract_drivers, extract_action_items


def _build_inputs(*, critical_count=0, coverage_pct=0.0, eol=0, kev=0):
    controls = [
        {"name": f"ctrl-{i}", "family": "Endpoint", "severity": "critical"}
        for i in range(critical_count)
    ]
    coverages: list = []
    if coverage_pct > 0:
        coverages.append({
            "name": "EDR",
            "family": "Endpoint",
            "coverage_percentage": coverage_pct,
        })
    lifecycle = [
        {"software_name": f"asset-{i}", "lifecycle_status": "END_OF_LIFE"}
        for i in range(eol)
    ]
    exposure: list = []
    if kev > 0:
        exposure.append({
            "software_name": "exposed-service",
            "kev_count": kev,
            "is_internet_facing": True,
            "is_critical_asset": True,
        })
    return {
        "assessment_score": 60.0,
        "verified_controls": controls,
        "verified_coverages": coverages,
        "lifecycle_risks": lifecycle,
        "exposure_risks": exposure,
    }


class TestExtractDrivers:
    def test_empty_inputs_return_empty_lists(self):
        kwargs = _build_inputs()
        out = extract_drivers(**kwargs)
        assert out["positive_drivers"] == []
        assert out["negative_drivers"] == []

    def test_positive_drivers_sorted_descending(self):
        kwargs = _build_inputs(critical_count=4)  # +12 (cap +15)
        # Add 1 important control for variation
        kwargs["verified_controls"].append({
            "name": "backup",
            "family": "Backup",
            "severity": "important",  # +2
        })
        out = extract_drivers(**kwargs, top_n=10)
        positives = out["positive_drivers"]
        assert len(positives) > 0
        impacts = [d["impact"] for d in positives]
        assert impacts == sorted(impacts, reverse=True)

    def test_negative_drivers_sorted_most_negative_first(self):
        kwargs = _build_inputs(eol=2, kev=1)
        # EOL × 2 = -4 kev in critical internet = -7 → total -11
        out = extract_drivers(**kwargs, top_n=10)
        negatives = out["negative_drivers"]
        impacts = [d["impact"] for d in negatives]
        assert impacts == sorted(impacts)  # ascending (most negative first)

    def test_zero_impact_drivers_excluded(self):
        kwargs = _build_inputs(coverage_pct=10.0)  # 10% coverage ⇒ +0 bonus
        out = extract_drivers(**kwargs)
        # Coverage at 10% contributes 0 (no bonus). No drivers emitted.
        assert out["positive_drivers"] == []

    def test_top_n_truncation(self):
        kwargs = _build_inputs(critical_count=20)  # capped at 15
        out = extract_drivers(**kwargs, top_n=3)
        assert len(out["positive_drivers"]) <= 3

    def test_action_items_renders_rationale(self):
        kwargs = _build_inputs(kev=1)
        actions = extract_action_items(**kwargs)
        assert len(actions) >= 1
        for a in actions:
            assert "driver_type" in a
            assert "item" in a
            assert a["impact"] < 0
            assert "rationale" in a and "readiness points" in a["rationale"]

    def test_invalid_top_n_raises(self):
        kwargs = _build_inputs()
        with pytest.raises(ValueError):
            extract_drivers(**kwargs, top_n=0)

    def test_no_db_writes_no_llm_imports(self):
        # Direct-import scan of readiness_drivers.py
        src = inspect.getsource(drivers_module)
        tree = ast.parse(src)

        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.add(node.module)

        forbidden = ("ai_narrative", "llm_narrative", "google.genai", "google.generativeai")
        bad = sorted(
            n for n in imported_names
            if any(n == f or n.startswith(f + ".") for f in forbidden)
        )
        assert not bad, f"readiness_drivers.py has forbidden imports: {bad}"
