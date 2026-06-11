"""
ThreatSimulationEngine — Deterministic AI-Specific Adversarial Simulation.

Runs rule-based threat simulations against an organization's AI asset
inventory to calculate blast radius, readiness degradation, and remediation
hooks. ALL scoring is 100% deterministic — no LLM involvement in any
calculation path.

Simulation Categories (9):
  - prompt_injection
  - data_exfiltration
  - rag_poisoning
  - agent_privilege_escalation
  - model_dos
  - shadow_ai
  - sensitive_data_leakage
  - reliability_outage
  - malicious_payload_bypass

Scoring Formula (deterministic):
  blast_radius = base_weight
      × asset_criticality_multiplier   (critical=1.0, high=0.75, medium=0.5, low=0.25)
      × exposure_multiplier            (public=1.0, internal=0.6, restricted=0.4, confidential=0.3)
      × lifecycle_multiplier           (production=1.0, staging=0.7, testing=0.4, development=0.2)
      + control_gap_penalty            (5 pts per missing control)

  readiness_degradation = blast_radius × 0.12  (capped at 25%)

Staging-only module — not deployed to production/demo.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.ai_asset import AIAsset, AIAssetType, BusinessCriticality, ExposureLevel, LifecycleStage
from app.models.simulation_result import SimulationResult, SimulationCategory

logger = logging.getLogger("airs.simulation_engine")


# ═══════════════════════════════════════════════════════════════════════
# Simulation Rule Definitions (Static, Deterministic)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SimulationRule:
    """Immutable rule defining an adversarial attack simulation."""
    id: str
    category: SimulationCategory
    name: str
    description: str
    preconditions: List[str]  # asset types this rule applies to
    attack_vector: str
    affected_controls: List[str]  # control rule IDs impacted
    base_blast_weight: float  # 0.0 – 1.0
    remediation: str


# ── Static Rule Registry ────────────────────────────────────────────────
# Each rule is deterministic and version-pinned. No dynamic generation.

SIMULATION_RULES: Dict[SimulationCategory, List[SimulationRule]] = {
    SimulationCategory.prompt_injection: [
        SimulationRule(
            id="PI-001",
            category=SimulationCategory.prompt_injection,
            name="System Prompt Override",
            description="User-controlled input reaches system prompt without sanitization, enabling instruction override.",
            preconditions=["agent", "rag_pipeline", "prompt_system"],
            attack_vector="User-controlled input reaches system prompt without sanitization",
            affected_controls=["LF-001", "LF-002", "DC-003"],
            base_blast_weight=0.85,
            remediation="Deploy input validation + Logic Firewall guardrails. Implement prompt-level sandboxing.",
        ),
        SimulationRule(
            id="PI-002",
            category=SimulationCategory.prompt_injection,
            name="Indirect Prompt Injection via RAG",
            description="Poisoned retrieval context injects malicious instructions via document embeddings.",
            preconditions=["rag_pipeline", "vector_db"],
            attack_vector="Malicious content in indexed documents modifies agent behavior via retrieval context",
            affected_controls=["LF-001", "LF-003", "DC-004"],
            base_blast_weight=0.75,
            remediation="Implement content sanitization on ingested documents. Add retrieval-time prompt isolation.",
        ),
    ],
    SimulationCategory.data_exfiltration: [
        SimulationRule(
            id="DE-001",
            category=SimulationCategory.data_exfiltration,
            name="Training Data Extraction",
            description="Adversary extracts memorized training data through targeted prompting.",
            preconditions=["model", "fine_tuned_model"],
            attack_vector="Targeted prompting to extract memorized PII or proprietary data from model weights",
            affected_controls=["DC-001", "DC-002", "IV-003"],
            base_blast_weight=0.80,
            remediation="Apply differential privacy during training. Deploy output filtering for PII/secrets.",
        ),
        SimulationRule(
            id="DE-002",
            category=SimulationCategory.data_exfiltration,
            name="API Response Data Leakage",
            description="Inference endpoint exposes sensitive data in unfiltered API responses.",
            preconditions=["inference_endpoint", "model", "agent"],
            attack_vector="Unfiltered API responses expose internal data structures or sensitive context",
            affected_controls=["DC-001", "DC-005"],
            base_blast_weight=0.65,
            remediation="Implement response filtering. Add output classification and redaction layer.",
        ),
    ],
    SimulationCategory.rag_poisoning: [
        SimulationRule(
            id="RP-001",
            category=SimulationCategory.rag_poisoning,
            name="Knowledge Base Contamination",
            description="Adversary injects misleading documents into the vector store to alter retrieval results.",
            preconditions=["rag_pipeline", "vector_db", "dataset"],
            attack_vector="Injection of adversarial documents into the knowledge base to corrupt retrieval",
            affected_controls=["DC-004", "IV-001", "IV-002"],
            base_blast_weight=0.70,
            remediation="Implement document provenance tracking. Add content integrity verification on ingestion.",
        ),
    ],
    SimulationCategory.agent_privilege_escalation: [
        SimulationRule(
            id="APE-001",
            category=SimulationCategory.agent_privilege_escalation,
            name="Tool Use Privilege Escalation",
            description="AI agent is tricked into using tools beyond its intended authorization scope.",
            preconditions=["agent"],
            attack_vector="Manipulated context causes agent to invoke privileged tools or APIs",
            affected_controls=["LF-001", "LF-004", "DC-006"],
            base_blast_weight=0.90,
            remediation="Enforce least-privilege tool access. Add agent action auditing and confirmation gates.",
        ),
    ],
    SimulationCategory.model_dos: [
        SimulationRule(
            id="MDOS-001",
            category=SimulationCategory.model_dos,
            name="Inference Resource Exhaustion",
            description="Adversary submits crafted inputs that consume excessive compute during inference.",
            preconditions=["model", "inference_endpoint", "fine_tuned_model", "agent"],
            attack_vector="Adversarial inputs designed to maximize token generation or processing time",
            affected_controls=["RL-001", "RL-002"],
            base_blast_weight=0.55,
            remediation="Implement request rate limiting and token budget caps. Add timeout enforcement.",
        ),
    ],
    SimulationCategory.shadow_ai: [
        SimulationRule(
            id="SAI-001",
            category=SimulationCategory.shadow_ai,
            name="Unregistered AI Service Usage",
            description="Employees use unregistered third-party AI services that bypass governance controls.",
            preconditions=["external_vendor", "model", "agent"],
            attack_vector="Unauthorized AI tool adoption outside the governance perimeter",
            affected_controls=["GV-001", "GV-002", "DC-007"],
            base_blast_weight=0.60,
            remediation="Deploy AI usage discovery tooling. Enforce vendor approval workflows.",
        ),
    ],
    SimulationCategory.sensitive_data_leakage: [
        SimulationRule(
            id="SDL-001",
            category=SimulationCategory.sensitive_data_leakage,
            name="PII Exposure in Model Output",
            description="Model generates outputs containing personally identifiable information.",
            preconditions=["model", "fine_tuned_model", "agent", "rag_pipeline"],
            attack_vector="Model generates PII or sensitive business data in outputs",
            affected_controls=["DC-001", "DC-002", "DC-008"],
            base_blast_weight=0.75,
            remediation="Add output scanning for PII patterns. Implement data masking in training pipelines.",
        ),
    ],
    SimulationCategory.reliability_outage: [
        SimulationRule(
            id="RO-001",
            category=SimulationCategory.reliability_outage,
            name="Single Point of Failure in Inference Chain",
            description="Critical AI service has no redundancy, creating a single point of failure.",
            preconditions=["inference_endpoint", "model", "agent", "rag_pipeline"],
            attack_vector="Single endpoint failure cascades to downstream dependents",
            affected_controls=["RL-001", "RL-003"],
            base_blast_weight=0.50,
            remediation="Deploy redundant inference endpoints. Implement circuit breaker patterns.",
        ),
    ],
    SimulationCategory.malicious_payload_bypass: [
        SimulationRule(
            id="MPB-001",
            category=SimulationCategory.malicious_payload_bypass,
            name="Content Filter Evasion",
            description="Adversary crafts inputs that bypass content safety filters and guardrails.",
            preconditions=["model", "agent", "prompt_system", "fine_tuned_model"],
            attack_vector="Encoded or obfuscated payloads that evade content safety classifiers",
            affected_controls=["LF-001", "LF-005", "DC-009"],
            base_blast_weight=0.80,
            remediation="Deploy multi-layer content filtering. Add adversarial robustness testing to CI/CD.",
        ),
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# Scoring Multipliers (Deterministic Lookup Tables)
# ═══════════════════════════════════════════════════════════════════════

CRITICALITY_MULTIPLIER = {
    BusinessCriticality.critical: 1.0,
    BusinessCriticality.high: 0.75,
    BusinessCriticality.medium: 0.5,
    BusinessCriticality.low: 0.25,
    # String fallbacks for enum coercion edge cases
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
}

EXPOSURE_MULTIPLIER = {
    ExposureLevel.public: 1.0,
    ExposureLevel.internal: 0.6,
    ExposureLevel.restricted: 0.4,
    ExposureLevel.confidential: 0.3,
    "public": 1.0,
    "internal": 0.6,
    "restricted": 0.4,
    "confidential": 0.3,
}

LIFECYCLE_MULTIPLIER = {
    LifecycleStage.production: 1.0,
    LifecycleStage.staging: 0.7,
    LifecycleStage.testing: 0.4,
    LifecycleStage.development: 0.2,
    LifecycleStage.deprecated: 0.8,
    LifecycleStage.retired: 0.1,
    "production": 1.0,
    "staging": 0.7,
    "testing": 0.4,
    "development": 0.2,
    "deprecated": 0.8,
    "retired": 0.1,
}

# Points deducted per missing/unverified control
CONTROL_GAP_PENALTY = 5.0

# Maximum readiness degradation percentage
MAX_DEGRADATION_PCT = 25.0

# Degradation coefficient: blast_radius * this = degradation %
DEGRADATION_COEFFICIENT = 0.12


# ═══════════════════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════════════════

class ThreatSimulationEngine:
    """Deterministic rules-based AI threat simulation engine.

    All calculations are pure functions of the static rule set and the
    organization's AI asset inventory. No LLM involvement at any stage.
    """

    def __init__(self, db: Session):
        self.db = db

    # ── Public API ──────────────────────────────────────────────────────

    def run_simulation(
        self,
        org_id: str,
        category: SimulationCategory,
        target_asset_id: Optional[str] = None,
        executed_by: Optional[str] = None,
    ) -> SimulationResult:
        """Run a single-category threat simulation.

        If target_asset_id is provided, simulation targets that specific asset.
        Otherwise, it evaluates all applicable assets in the organization.
        """
        rules = SIMULATION_RULES.get(category, [])
        if not rules:
            logger.warning(f"No rules defined for category: {category}")
            return self._create_empty_result(org_id, category, executed_by)

        # Load target assets
        if target_asset_id:
            assets = self.db.query(AIAsset).filter(
                AIAsset.id == target_asset_id,
                AIAsset.org_id == org_id,
                AIAsset.is_active == True,
            ).all()
        else:
            assets = self.db.query(AIAsset).filter(
                AIAsset.org_id == org_id,
                AIAsset.is_active == True,
            ).all()

        if not assets:
            logger.info(f"No applicable AI assets found for org {org_id}")
            return self._create_empty_result(org_id, category, executed_by)

        # Run all rules in this category against matching assets
        attack_chain = []
        all_affected_controls = set()
        total_blast_raw = 0.0
        total_applicable = 0

        for rule in rules:
            matching_assets = [
                a for a in assets
                if self._asset_matches_preconditions(a, rule.preconditions)
            ]
            if not matching_assets:
                continue

            for asset in matching_assets:
                blast = self._calculate_blast_radius(rule, asset)
                total_blast_raw += blast
                total_applicable += 1
                all_affected_controls.update(rule.affected_controls)

                attack_chain.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "target_asset": asset.name,
                    "target_asset_id": asset.id,
                    "asset_type": asset.asset_type.value if hasattr(asset.asset_type, 'value') else str(asset.asset_type),
                    "attack_vector": rule.attack_vector,
                    "blast_radius": round(blast, 2),
                    "remediation": rule.remediation,
                })

        # Aggregate scores
        blast_radius_score = min(
            round(total_blast_raw / max(total_applicable, 1), 2),
            100.0,
        )
        readiness_degradation = min(
            round(blast_radius_score * DEGRADATION_COEFFICIENT, 2),
            MAX_DEGRADATION_PCT,
        )

        # Build remediation hooks
        remediation_hooks = self._build_remediation_hooks(attack_chain)

        # Score impact forecast
        score_impact = {
            "current_blast_radius": blast_radius_score,
            "projected_score_drop": readiness_degradation,
            "affected_control_count": len(all_affected_controls),
            "applicable_asset_count": total_applicable,
        }

        # Persist result
        result = SimulationResult(
            org_id=org_id,
            category=category,
            target_asset_id=target_asset_id,
            attack_chain=attack_chain,
            affected_controls=sorted(all_affected_controls),
            blast_radius_score=blast_radius_score,
            readiness_degradation_pct=readiness_degradation,
            business_impact_narrative=self._generate_impact_narrative(
                category, blast_radius_score, len(all_affected_controls), total_applicable
            ),
            remediation_hooks=remediation_hooks,
            score_impact_forecast=score_impact,
            executed_by=executed_by,
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)

        logger.info(
            f"Simulation {category.value} completed for org {org_id}: "
            f"blast_radius={blast_radius_score}, degradation={readiness_degradation}%"
        )
        return result

    def run_full_assessment(
        self,
        org_id: str,
        executed_by: Optional[str] = None,
    ) -> List[SimulationResult]:
        """Run all simulation categories against the organization's assets."""
        results = []
        for category in SimulationCategory:
            result = self.run_simulation(org_id, category, executed_by=executed_by)
            results.append(result)
        return results

    def get_simulation_history(
        self,
        org_id: str,
        category: Optional[SimulationCategory] = None,
        limit: int = 50,
    ) -> List[SimulationResult]:
        """Retrieve historical simulation results."""
        query = self.db.query(SimulationResult).filter(
            SimulationResult.org_id == org_id,
        )
        if category:
            query = query.filter(SimulationResult.category == category)
        return query.order_by(SimulationResult.executed_at.desc()).limit(limit).all()

    # ── Internal Calculation Methods ────────────────────────────────────

    def _asset_matches_preconditions(
        self, asset: AIAsset, preconditions: List[str]
    ) -> bool:
        """Check if an asset's type matches the rule's preconditions."""
        asset_type_val = (
            asset.asset_type.value
            if hasattr(asset.asset_type, "value")
            else str(asset.asset_type)
        )
        return asset_type_val in preconditions

    def _calculate_blast_radius(self, rule: SimulationRule, asset: AIAsset) -> float:
        """Deterministic blast radius calculation.

        Formula:
            blast = base_weight × 100
                × criticality_multiplier
                × exposure_multiplier
                × lifecycle_multiplier
                + control_gap_penalty × num_affected_controls
        """
        base = rule.base_blast_weight * 100.0

        crit_key = asset.business_criticality
        crit_mult = CRITICALITY_MULTIPLIER.get(crit_key, 0.5)

        exp_key = asset.exposure_level
        exp_mult = EXPOSURE_MULTIPLIER.get(exp_key, 0.6)

        life_key = asset.lifecycle_stage
        life_mult = LIFECYCLE_MULTIPLIER.get(life_key, 0.5)

        # Check which controls the asset already has mapped
        asset_controls = set(asset.associated_controls or [])
        missing_controls = [
            c for c in rule.affected_controls if c not in asset_controls
        ]
        gap_penalty = len(missing_controls) * CONTROL_GAP_PENALTY

        blast = (base * crit_mult * exp_mult * life_mult) + gap_penalty
        return min(blast, 100.0)

    def _create_empty_result(
        self,
        org_id: str,
        category: SimulationCategory,
        executed_by: Optional[str],
    ) -> SimulationResult:
        """Create a zero-impact result when no rules or assets apply."""
        result = SimulationResult(
            org_id=org_id,
            category=category,
            attack_chain=[],
            affected_controls=[],
            blast_radius_score=0.0,
            readiness_degradation_pct=0.0,
            business_impact_narrative="No applicable assets or rules found for this simulation category.",
            remediation_hooks=[],
            score_impact_forecast={"current_blast_radius": 0, "projected_score_drop": 0},
            executed_by=executed_by,
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def _build_remediation_hooks(self, attack_chain: List[Dict]) -> List[Dict]:
        """Extract unique remediation actions from the attack chain."""
        seen = set()
        hooks = []
        for step in attack_chain:
            rem = step.get("remediation", "")
            rule_id = step.get("rule_id", "")
            key = f"{rule_id}:{rem}"
            if key not in seen and rem:
                seen.add(key)
                hooks.append({
                    "rule_id": rule_id,
                    "action": rem,
                    "priority": "high" if step.get("blast_radius", 0) > 60 else "medium",
                    "target_asset": step.get("target_asset"),
                })
        return hooks

    def _generate_impact_narrative(
        self,
        category: SimulationCategory,
        blast_radius: float,
        control_count: int,
        asset_count: int,
    ) -> str:
        """Generate a deterministic impact narrative (no LLM)."""
        severity = "critical" if blast_radius > 75 else (
            "high" if blast_radius > 50 else (
                "moderate" if blast_radius > 25 else "low"
            )
        )
        category_label = category.value.replace("_", " ").title()
        return (
            f"{category_label} simulation assessed {asset_count} applicable asset(s) "
            f"across {control_count} control(s). "
            f"Blast radius: {blast_radius}/100 ({severity} severity). "
            f"Readiness degradation forecast: {min(blast_radius * DEGRADATION_COEFFICIENT, MAX_DEGRADATION_PCT):.1f}%."
        )
