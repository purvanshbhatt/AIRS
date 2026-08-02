"""
Tests for Sprint 1.8, Task S1.8-B3 — AI finding rules AI-001..AI-010.

Covers:
  - The 10 AI rules are registered in FINDING_RULES.
  - The standalone evaluate_ai_governance_findings classifies entries
    per the deterministic mapping.
  - Empty inventory → AI-001 only.
  - Cross-classification: an internet-facing MCP emits AI-005.
  - Determinism: identical input ⇒ identical list.
  - No LLM imports (by AST scan).
"""

import inspect
import ast

import pytest

from app.services import findings as findings_module
from app.services.findings import (
    AI_GOVERNANCE_RULES,
    FINDING_RULES,
    evaluate_ai_governance_findings,
)


class TestRuleRegistration:
    def test_ten_rules_registered(self):
        ids = [r.rule_id for r in AI_GOVERNANCE_RULES]
        for expected in (f"AI-{i:03d}" for i in range(1, 11)):
            assert expected in ids, f"Missing rule {expected}"

    def test_rules_attached_to_findings_list(self):
        ids = [r.rule_id for r in FINDING_RULES]
        for expected in (f"AI-{i:03d}" for i in range(1, 11)):
            assert expected in ids


class TestInventoryClassification:
    def test_empty_inventory_emits_only_ai_001(self):
        out = evaluate_ai_governance_findings([])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert rule_ids == ["AI-001"]

    def test_prompt_library_public_exposure(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "prompt_library", "exposure_level": "public",
             "asset_name": "central-prompt-store"}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-001" not in rule_ids
        assert "AI-003" in rule_ids

    def test_prompt_library_internal_exposure_no_match(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "prompt_library", "exposure_level": "internal"}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-003" not in rule_ids

    def test_vector_db_missing_retention_matches_ai_004(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "vector_db", "retention_policy": None}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-004" in rule_ids

    def test_vector_db_with_retention_no_match(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "vector_db", "retention_policy": "180_days"}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-004" not in rule_ids

    def test_mcp_server_internet_facing_matches_ai_005(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "mcp_server", "exposure_level": "public",
             "asset_name": "public-mcp"}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-005" in rule_ids

    def test_agent_framework_production_critical_matches_ai_006(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "agent_framework",
             "lifecycle_stage": "production",
             "business_criticality": "critical"}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-006" in rule_ids

    def test_agent_framework_dev_only_not_match(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "agent_framework",
             "lifecycle_stage": "development"}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-006" not in rule_ids

    def test_unversioned_prompt_matches_ai_007(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "prompt", "current_version": None}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-007" in rule_ids

    def test_eol_model_matches_ai_008(self):
        for stage in ("end_of_life", "deprecated"):
            out = evaluate_ai_governance_findings([
                {"asset_type": "model", "lifecycle_stage": stage}
            ])
            rule_ids = sorted({f["rule_id"] for f in out})
            assert "AI-008" in rule_ids

    def test_air_gapped_disabled_pii_matches_ai_009(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "model",
             "handles_pii": True,
             "network_isolation": False}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-009" in rule_ids

    def test_unowned_asset_matches_ai_010(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "model", "ownership": None}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-010" in rule_ids

    def test_unclassified_type_matches_ai_002(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "unknown"}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-002" in rule_ids

    def test_unclassified_type_and_eol_yield_two_rules(self):
        out = evaluate_ai_governance_findings([
            {"asset_type": "model",   # not flagged as unclassified
             "lifecycle_stage": "end_of_life"}
        ])
        rule_ids = sorted({f["rule_id"] for f in out})
        assert "AI-008" in rule_ids
        assert "AI-002" not in rule_ids

    def test_determinism(self):
        entries = [
            {"asset_type": "mcp_server", "exposure_level": "public"},
            {"asset_type": "vector_db", "retention_policy": None},
            {"asset_type": "model", "lifecycle_stage": "end_of_life"},
            {"asset_type": "prompt_library", "exposure_level": "exposed"},
        ]
        a = evaluate_ai_governance_findings(entries)
        b = evaluate_ai_governance_findings(entries)
        assert [f["rule_id"] for f in a] == [f["rule_id"] for f in b]


class TestModuleInvariants:
    def test_no_forbidden_llm_imports(self):
        src = inspect.getsource(findings_module)
        tree = ast.parse(src)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module)
        forbidden = ("ai_narrative", "llm_narrative",
                     "google.genai", "google.generativeai")
        bad = sorted(
            n for n in imported
            if any(n == f or n.startswith(f + ".") for f in forbidden)
        )
        assert not bad, f"findings gained forbidden imports: {bad}"
