"""
Hackathon Demo Script for ResilAI Sentinel.

Executes the end-to-end workflow:
1. Ingests mock Splunk telemetry.
2. Converts telemetry to deterministic evidence.
3. Executes a Digital Twin Ransomware simulation.
4. Generates a Board Intelligence executive narrative via Gemini.
"""

import asyncio
import json
import logging
import os
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.integrations.splunk.service import ingest_splunk_telemetry
from app.sentinel.evidence.engine import generate_evidence_from_telemetry
from app.sentinel.twin.engine import execute_simulation
from app.sentinel.board_intelligence.generator import generate_board_report

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel.demo")

async def run_demo():
    logger.info("Starting ResilAI Sentinel Hackathon Demo...")
    db: Session = SessionLocal()
    org_id = "00000000-0000-0000-0000-000000000001" # Assuming a demo org exists
    
    try:
        # Step 1: Initialize connector (handled implicitly in service for demo if missing, 
        # or we can mock the connector creation)
        from app.integrations.splunk.connector import initialize_splunk_connector
        initialize_splunk_connector(db, org_id, "https://mock-mcp-splunk.local", "dummy", "demo_user")
        
        # Step 2: Ingest Splunk Telemetry
        logger.info("Ingesting Splunk telemetry...")
        events_ingested = await ingest_splunk_telemetry(db, org_id)
        logger.info(f"Ingested {events_ingested} events.")
        
        # Step 3: Evidence Generation
        logger.info("Generating Telemetry Evidence...")
        evidence_generated = generate_evidence_from_telemetry(db, org_id)
        logger.info(f"Generated {evidence_generated} deterministic evidence records.")
        
        # Step 4: Digital Twin Simulation
        scenario = "Ransomware"
        logger.info(f"Executing '{scenario}' Digital Twin Simulation...")
        simulation = execute_simulation(db, org_id, scenario)
        logger.info(f"Simulation completed. New Score: {simulation.readiness_impact_score}")
        
        # Step 5: Board Intelligence Report
        logger.info("Generating Board Intelligence Executive Report...")
        if os.environ.get("GOOGLE_API_KEY"):
            report = generate_board_report(db, simulation.id)
            logger.info("--- BOARD INTELLIGENCE REPORT ---")
            print(json.dumps(report, indent=2))
            logger.info("---------------------------------")
        else:
            logger.warning("GOOGLE_API_KEY not set. Skipping Gemini generation. Set it to see full narrative.")
            
        logger.info("Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_demo())
