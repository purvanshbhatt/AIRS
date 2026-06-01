"""
Board Intelligence Engine.

Generates executive narratives based purely on deterministic evidence 
and simulation results using Gemini Flash. 

Enforces strict logic firewall boundaries.
"""
import json
import logging
from sqlalchemy.orm import Session
from app.sentinel.twin.models import SentinelSimulation
from google import genai
from app.core.config import settings

logger = logging.getLogger("airs.sentinel.board_intelligence")

# Prompt Template acting as a logic firewall boundary
EXECUTIVE_PROMPT = """
You are the ResilAI Board Intelligence Engine.
Your task is to explain deterministic security metrics to an executive board.

CRITICAL DIRECTIVES:
1. You MUST NOT calculate scores. Use the provided scores.
2. You MUST NOT invent findings. Use the provided findings.
3. You MUST NOT change framework mappings. Use the provided mappings.
4. Your ONLY job is to translate the provided technical evidence into business impact and executive narrative.

INPUT DATA (DETERMINISTIC):
Base Readiness Score: {base_score}
Simulated Post-Incident Score: {simulated_score}
Scenario: {scenario}

Missing Controls & Evidence:
{missing_controls}

OUTPUT FORMAT (JSON ONLY):
{{
    "executive_summary": "High level 3-sentence summary",
    "business_impact": "Financial and operational impact",
    "board_narrative": "How to talk about this at the board meeting",
    "remediation_roadmap": "High level steps based ONLY on missing controls",
    "operational_risk_summary": "Overall risk posture"
}}
"""

def generate_board_report(db: Session, simulation_id: str) -> dict:
    """
    Generates an executive report using Gemini Flash based on a SentinelSimulation.
    """
    simulation = db.query(SentinelSimulation).filter(SentinelSimulation.id == simulation_id).first()
    if not simulation:
        raise ValueError(f"Simulation {simulation_id} not found.")
        
    base_score = simulation.simulation_context.get("base_score", "Unknown")
    simulated_score = simulation.readiness_impact_score
    scenario = simulation.scenario_type
    missing_controls = json.dumps(simulation.missing_controls, indent=2)
    
    prompt = EXECUTIVE_PROMPT.format(
        base_score=base_score,
        simulated_score=simulated_score,
        scenario=scenario,
        missing_controls=missing_controls
    )
    
    try:
        client = genai.Client() # Assuming environment has GOOGLE_API_KEY
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        # Parse JSON response
        raw_text = response.text
        # Strip markdown json blocks if present
        if raw_text.startswith("```json"):
            raw_text = raw_text.strip("`").replace("json\n", "", 1)
            
        report_data = json.loads(raw_text)
        
        logger.info(f"Successfully generated Board Intelligence report for simulation {simulation_id}")
        return report_data
        
    except Exception as e:
        logger.error(f"Failed to generate board report via Gemini: {e}")
        # Fallback to deterministic template on LLM failure
        return {
            "executive_summary": f"A {scenario} incident would drop the readiness score from {base_score} to {simulated_score}.",
            "business_impact": "Automated impact generation failed. Review manual telemetry.",
            "board_narrative": "Please consult the technical team.",
            "remediation_roadmap": "Address missing controls immediately.",
            "operational_risk_summary": "High risk due to critical missing controls."
        }
