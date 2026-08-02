"""
Capability Registry — Abstract base and registration for question-driven capabilities.

Each capability answers one customer question using evidence.
"""
from __future__ import annotations

import abc
import logging
from typing import Dict, List, Optional, Type

from app.services.clinic_engine.v2.schema import (
    ActionIntent,
    ClinicMoment,
    Evidence,
    EvaluationResult,
    EvidenceKind,
    MomentTranslation,
    Verdict,
)

logger = logging.getLogger("airs.clinic_engine.v2.capability")


class BaseCapability(abc.ABC):
    """A capability answers one customer question using evidence.

    Every capability must declare:
    - What question it answers
    - What evidence it needs
    - Which connectors can provide that evidence
    - Deterministic evaluation logic
    - Plain-English translation rules
    - Available fix actions
    """

    @classmethod
    @abc.abstractmethod
    def capability_id(cls) -> str:
        """Unique identifier for this capability."""
        ...

    @classmethod
    @abc.abstractmethod
    def question_id(cls) -> str:
        """Which customer question this answers (Q1, Q2, Q3)."""
        ...

    @classmethod
    @abc.abstractmethod
    def question_text(cls) -> str:
        """The actual customer question in plain English."""
        ...

    @classmethod
    @abc.abstractmethod
    def required_evidence(cls) -> List[EvidenceKind]:
        """What evidence kinds this capability needs to evaluate."""
        ...

    @classmethod
    @abc.abstractmethod
    def supported_connectors(cls) -> List[str]:
        """Which connectors can provide the required evidence."""
        ...

    @classmethod
    @abc.abstractmethod
    def evaluate(cls, evidence: List[Evidence]) -> List[EvaluationResult]:
        """Deterministic evaluation: examine evidence, return verdicts.

        Must be pure — no side effects, no network calls.
        Returns one EvaluationResult per detected issue.
        """
        ...

    @classmethod
    @abc.abstractmethod
    def translate(cls, result: EvaluationResult) -> MomentTranslation:
        """Convert an evaluation result into plain English."""
        ...

    @classmethod
    @abc.abstractmethod
    def get_actions(cls, result: EvaluationResult) -> List[ActionIntent]:
        """Return available fix actions for this evaluation result."""
        ...

    @classmethod
    def confidence_threshold(cls) -> float:
        """Minimum confidence to report a moment. Override to customize."""
        return 0.5


class CapabilityRegistry:
    """Central registry of all capabilities. Indexed by question."""

    _capabilities: Dict[str, Type[BaseCapability]] = {}
    _question_index: Dict[str, List[str]] = {}  # question_id -> [capability_ids]

    @classmethod
    def register(cls, cap: Type[BaseCapability]) -> Type[BaseCapability]:
        """Register a capability. Can be used as a decorator."""
        cap_id = cap.capability_id()
        cls._capabilities[cap_id] = cap
        qid = cap.question_id()
        cls._question_index.setdefault(qid, []).append(cap_id)
        logger.debug("Registered capability: %s -> question %s", cap_id, qid)
        return cap

    @classmethod
    def get_capabilities_for_question(cls, question_id: str) -> List[Type[BaseCapability]]:
        cap_ids = cls._question_index.get(question_id, [])
        return [cls._capabilities[cid] for cid in cap_ids]

    @classmethod
    def all_capabilities(cls) -> List[Type[BaseCapability]]:
        return list(cls._capabilities.values())

    @classmethod
    def get_capability(cls, capability_id: str) -> Optional[Type[BaseCapability]]:
        return cls._capabilities.get(capability_id)

    @classmethod
    def reset(cls):
        """Reset registry. Only for testing."""
        cls._capabilities.clear()
        cls._question_index.clear()
