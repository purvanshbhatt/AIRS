"""
Tests for Sprint 1.8, Task S1.8-C1 — EvidenceAdapter ABC + Registry.

Covers:
  - ABC enforces the four required attributes/methods.
  - Registry registers by connector_name; duplicate names replace.
  - Lookup returns None for unknown connectors.
  - is_registered / list_connectors / adapters() shape.
  - get_instance returns a singleton.
  - No forbidden LLM imports by AST scan.
"""

import inspect
import ast

import pytest

from app.services.evidence import (
    AdapterHealth,
    EvidenceAdapter,
    EvidenceRecord,
    EvidenceRegistry,
    get_instance,
    reset_instance,
)


class _OkAdapter(EvidenceAdapter):
    """A minimal valid adapter used by the tests."""

    @property
    def connector_name(self) -> str:
        return "test_connector"

    async def fetch_evidence(self, *, since=None):
        return [
            EvidenceRecord(
                connector_name=self.connector_name,
                external_id="abc",
                control_id="ctrl-1",
                finding_kind="telemetry",
            )
        ]

    def normalize(self, vendor_payload):
        return [
            EvidenceRecord(
                connector_name=self.connector_name,
                external_id=str(item.get("id", "")),
                metadata={"raw": item},
            )
            for item in vendor_payload
        ]

    async def health(self):
        return AdapterHealth(
            healthy=True,
            last_success_at=None,
            last_failure_at=None,
            success_count=4,
            failure_count=1,
        )


class _MissingMethodsAdapter:
    """Missing abstract methods — should fail ``register``."""

    @property
    def connector_name(self) -> str:
        return "bad"

    async def fetch_evidence(self, *, since=None):
        return []


class TestABCEnforcement:
    def test_register_rejects_non_abc(self):
        registry = EvidenceRegistry()
        with pytest.raises(TypeError):
            registry.register(object())  # type: ignore[arg-type]

    def test_register_rejects_partial_subclass(self):
        registry = EvidenceRegistry()
        with pytest.raises(TypeError):
            registry.register(_MissingMethodsAdapter())

    def test_register_accepts_valid_subclass(self):
        registry = EvidenceRegistry()
        adapter = _OkAdapter()
        registry.register(adapter)
        assert registry.is_registered("test_connector")


class TestRegistryLookup:
    def test_get_adapter_returns_registered(self):
        registry = EvidenceRegistry()
        adapter = _OkAdapter()
        registry.register(adapter)
        assert registry.get_adapter("test_connector") is adapter

    def test_get_adapter_unknown_returns_none(self):
        registry = EvidenceRegistry()
        assert registry.get_adapter("nope") is None

    def test_list_connectors_returns_sorted(self):
        registry = EvidenceRegistry()
        registry.register(_OkAdapter())
        # add another adapter with a different name
        class _OtherAdapter(EvidenceAdapter):
            @property
            def connector_name(self):
                return "another_connector"
            async def fetch_evidence(self, *, since=None):
                return []
            def normalize(self, _payload):
                return []
            async def health(self):
                return AdapterHealth(healthy=False)
        registry.register(_OtherAdapter())
        assert registry.list_connectors() == ["another_connector", "test_connector"]

    def test_unregister_returns_true_for_known(self):
        registry = EvidenceRegistry()
        registry.register(_OkAdapter())
        assert registry.unregister("test_connector") is True
        assert registry.is_registered("test_connector") is False

    def test_unregister_returns_false_for_unknown(self):
        registry = EvidenceRegistry()
        assert registry.unregister("nope") is False

    def test_replace_existing(self):
        registry = EvidenceRegistry()
        registry.register(_OkAdapter())
        # Register a different adapter with the same name → replaces.
        class _Replacement(EvidenceAdapter):
            @property
            def connector_name(self):
                return "test_connector"

            async def fetch_evidence(self, *, since=None):
                return []

            def normalize(self, _p):
                return []

            async def health(self):
                return AdapterHealth(healthy=False)
        replacement = _Replacement()
        registry.register(replacement)
        assert registry.get_adapter("test_connector") is replacement


class TestSingleton:
    def test_get_instance_singleton(self):
        reset_instance()
        a = get_instance()
        b = get_instance()
        assert a is b

    def test_reset_instance_discardes(self):
        reset_instance()
        a = get_instance()
        reset_instance()
        b = get_instance()
        assert a is not b

    def test_get_instance_singleton_is_empty_by_default(self):
        reset_instance()
        inst = get_instance()
        assert isinstance(inst, EvidenceRegistry)
        assert inst.list_connectors() == []


class TestAdapterHealthHelper:
    def test_success_rate_no_probes_is_zero(self):
        h = AdapterHealth(healthy=False)
        assert h.success_rate == 0.0

    def test_success_rate_computed(self):
        h = AdapterHealth(healthy=True, success_count=4, failure_count=1)
        assert h.success_rate == pytest.approx(0.8)

    def test_to_dict_shape(self):
        h = AdapterHealth(healthy=True, success_count=2, failure_count=0)
        d = h.to_dict()
        assert d["healthy"] is True
        assert d["success_count"] == 2
        assert d["failure_count"] == 0
        assert d["success_rate"] == 1.0


class TestModuleInvariants:
    def test_no_forbidden_llm_imports(self):
        import os
        import app.services.evidence as ev_module

        def _read(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        # Read sources via filesystem to avoid inspect fails on __init__ packages.
        here = os.path.dirname(ev_module.__file__)
        src_base = _read(os.path.join(here, "base_adapter.py"))
        src_reg = _read(os.path.join(here, "registry.py"))
        src_init = _read(os.path.join(here, "__init__.py"))
        src = src_base + "\n" + src_reg + "\n" + src_init

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
        assert not bad, f"evidence package has forbidden imports: {bad}"
