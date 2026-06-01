import json
from typing import Union, List

class SimulationNarrativePromptBuilder:
    """
    Groundwork for the Deterministic Threat Simulator narrative.
    """

    SIMULATION_PROMPT = (
        "SYSTEM: You are the ResilAI Threat Interpreter. A simulated attack ({attack_category}) was executed. "
        "It resulted in a deterministic blast radius of {blast_radius_score}/100 and degraded readiness by {readiness_degradation_pct}%. "
        "It compromised the following controls: {affected_controls}. "
        "Translate this exact data into a 3-sentence executive impact forecast. "
        "DO NOT alter the math, invent new compromised controls, or suggest mitigations outside the provided scope."
    )

    @staticmethod
    def generate_prompt(
        attack_category: str,
        blast_radius_score: Union[int, float],
        readiness_degradation_pct: Union[int, float],
        affected_controls: List[str],
    ) -> str:
        """
        Forces strict type-bound inputs.
        """
        if not isinstance(attack_category, str):
            raise TypeError("attack_category must be a string.")
        if not isinstance(blast_radius_score, (int, float)):
            raise TypeError("blast_radius_score must be a deterministic numeric value.")
        if not isinstance(readiness_degradation_pct, (int, float)):
            raise TypeError("readiness_degradation_pct must be a deterministic numeric value.")
        if not isinstance(affected_controls, list) or not all(isinstance(c, str) for c in affected_controls):
            raise TypeError("affected_controls must be a list of strings.")

        affected_controls_str = ", ".join(affected_controls) if affected_controls else "None"

        return SimulationNarrativePromptBuilder.SIMULATION_PROMPT.format(
            attack_category=attack_category,
            blast_radius_score=blast_radius_score,
            readiness_degradation_pct=readiness_degradation_pct,
            affected_controls=affected_controls_str
        )
