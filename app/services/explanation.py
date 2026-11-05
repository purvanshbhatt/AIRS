"""
ResilAI Explanation Service — Business Language Layer.

Transforms deterministic backend facts (findings, readiness, evidence)
into executive-friendly narratives using Gemini.

INVARIANTS (enforced by design):
  - Gemini NEVER calculates scores
  - Gemini NEVER creates or removes findings
  - Gemini NEVER changes severity or evidence
  - Gemini NEVER creates framework mappings
  - Every explanation is traceable to deterministic source facts
  - If Gemini is unavailable, a deterministic fallback is used
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger("airs.explanation")


class ExplanationService:
    """Generates business-language explanations from deterministic facts.
    
    Gemini is used strictly as a narrative-only translator.
    All source facts are extracted BEFORE calling the LLM and returned
    alongside the explanation for auditability.
    """

    def __init__(self, db: Session, org_id: str, owner_uid: str):
        if not org_id or not owner_uid:
            raise ValueError("org_id and owner_uid are required")
        self.db = db
        self.org_id = org_id
        self.owner_uid = owner_uid

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_explanation(
        self,
        subject_type: str,
        subject_id: str,
        audience: str = "executive",
    ) -> Dict[str, Any]:
        """Generate a business-language explanation for a deterministic subject.
        
        Steps:
          1. Extract deterministic source facts from the database
          2. Build a grounded prompt containing only those facts
          3. Send to Gemini for narrative generation
          4. Return the explanation alongside source facts for auditability
          
        Returns:
            dict with 'explanation', 'source_facts', 'generated_at', 'model',
            'subject_type', 'subject_id', 'audience'
        """
        # Step 1: Extract deterministic facts
        source_facts = self._extract_source_facts(subject_type, subject_id)
        if not source_facts:
            raise ValueError(
                f"No deterministic facts found for {subject_type}/{subject_id} "
                f"in organization {self.org_id}"
            )

        # Step 2: Try Gemini, fall back to deterministic
        explanation = self._generate_with_gemini(source_facts, audience)
        if explanation is None:
            explanation = self._generate_deterministic_fallback(source_facts, audience)
            model_used = "deterministic-fallback"
        else:
            model_used = self._get_model_name()

        return {
            "explanation": explanation,
            "source_facts": source_facts,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": model_used,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "audience": audience,
        }

    # ------------------------------------------------------------------
    # Source fact extraction (deterministic — no LLM involved)
    # ------------------------------------------------------------------

    def _extract_source_facts(
        self, subject_type: str, subject_id: str
    ) -> List[Dict[str, str]]:
        """Extract deterministic facts from the database for the given subject."""
        if subject_type == "finding":
            return self._extract_finding_facts(subject_id)
        elif subject_type == "readiness":
            return self._extract_readiness_facts(subject_id)
        elif subject_type == "connector":
            return self._extract_connector_facts(subject_id)
        elif subject_type == "recovery":
            return self._extract_recovery_facts()
        elif subject_type == "evidence":
            return self._extract_evidence_facts(subject_id)
        else:
            logger.warning(f"Unknown subject_type: {subject_type}")
            return []

    def _extract_finding_facts(self, finding_id: str) -> List[Dict[str, str]]:
        """Extract facts from a deterministic finding."""
        from app.models.finding import Finding

        finding = (
            self.db.query(Finding)
            .filter(
                Finding.id == finding_id,
                Finding.organization_id == self.org_id,
            )
            .first()
        )
        if not finding:
            return []

        facts = [
            {"fact_type": "finding_title", "key": "title", "value": str(finding.title), "source": "findings_engine"},
            {"fact_type": "finding_severity", "key": "severity", "value": str(finding.severity), "source": "findings_engine"},
        ]
        if finding.evidence:
            facts.append({"fact_type": "finding_evidence", "key": "evidence", "value": str(finding.evidence), "source": "telemetry"})
        if finding.recommendation:
            facts.append({"fact_type": "finding_recommendation", "key": "recommendation", "value": str(finding.recommendation), "source": "findings_engine"})
        if finding.description:
            facts.append({"fact_type": "finding_description", "key": "description", "value": str(finding.description), "source": "findings_engine"})
        return facts

    def _extract_readiness_facts(self, scope: str = "overall") -> List[Dict[str, str]]:
        """Extract facts from the readiness/clinic engine."""
        try:
            from app.services.clinic_engine.v2.readiness_engine import ReadinessEngine
            engine = ReadinessEngine(self.db, self.org_id)
            result = engine.evaluate()
            facts = [
                {"fact_type": "readiness_status", "key": "status", "value": str(result.get("status", "unknown")), "source": "deterministic_scoring"},
                {"fact_type": "readiness_score", "key": "clinic_health_pct", "value": str(result.get("clinic_health_pct", 0)), "source": "deterministic_scoring"},
            ]
            for blocker in result.get("current_blockers", [])[:5]:
                facts.append({
                    "fact_type": "readiness_blocker",
                    "key": blocker.get("capability_id", "unknown"),
                    "value": blocker.get("problem", ""),
                    "source": "deterministic_scoring",
                })
            return facts
        except Exception as e:
            logger.warning(f"Could not extract readiness facts: {e}")
            return []

    def _extract_connector_facts(self, connector_id: str) -> List[Dict[str, str]]:
        """Extract facts about a connector (no secrets)."""
        from app.models.connector import Connector

        connector = (
            self.db.query(Connector)
            .filter(
                Connector.id == connector_id,
                Connector.organization_id == self.org_id,
            )
            .first()
        )
        if not connector:
            return []

        facts = [
            {"fact_type": "connector_type", "key": "connector_type", "value": str(connector.connector_type), "source": "connector_manager"},
            {"fact_type": "connector_status", "key": "status", "value": str(connector.status), "source": "connector_manager"},
            {"fact_type": "connector_name", "key": "name", "value": str(connector.name), "source": "connector_manager"},
        ]
        if connector.last_sync_at:
            facts.append({
                "fact_type": "connector_last_sync",
                "key": "last_sync_at",
                "value": connector.last_sync_at.isoformat(),
                "source": "connector_manager",
            })
        return facts

    def _extract_recovery_facts(self) -> List[Dict[str, str]]:
        """Extract recovery/backup readiness facts."""
        try:
            from app.services.clinic_engine.v2.readiness_engine import ReadinessEngine
            engine = ReadinessEngine(self.db, self.org_id)
            result = engine.evaluate()
            recovery = result.get("recovery_readiness", {})
            facts = [
                {"fact_type": "recovery_status", "key": "backup_status", "value": str(recovery.get("backup_status", "unknown")), "source": "deterministic_scoring"},
                {"fact_type": "recovery_verified", "key": "backup_verified", "value": str(recovery.get("backup_verified", False)), "source": "deterministic_scoring"},
            ]
            return facts
        except Exception as e:
            logger.warning(f"Could not extract recovery facts: {e}")
            return []

    def _extract_evidence_facts(self, evidence_id: str) -> List[Dict[str, str]]:
        """Extract facts about a specific evidence record."""
        from app.models.telemetry_event import TelemetryEvent

        event = (
            self.db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.id == evidence_id,
                TelemetryEvent.organization_id == self.org_id,
            )
            .first()
        )
        if not event:
            return []

        facts = [
            {"fact_type": "evidence_type", "key": "event_type", "value": str(event.event_type), "source": "telemetry"},
            {"fact_type": "evidence_source", "key": "source", "value": str(event.source), "source": "telemetry"},
        ]
        if event.created_at:
            facts.append({"fact_type": "evidence_timestamp", "key": "created_at", "value": event.created_at.isoformat(), "source": "telemetry"})
        return facts

    # ------------------------------------------------------------------
    # Gemini narrative generation (narrative ONLY)
    # ------------------------------------------------------------------

    def _get_model_name(self) -> str:
        from app.core.config import settings
        return getattr(settings, "LLM_MODEL", "gemini-3-flash")

    def _generate_with_gemini(
        self, source_facts: List[Dict[str, str]], audience: str
    ) -> Optional[Dict[str, str]]:
        """Use Gemini to transform source facts into a narrative.
        
        Returns None if Gemini is unavailable or fails.
        """
        from app.core.config import settings

        if not settings.is_llm_enabled:
            return None

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            logger.warning("google-genai not installed, using fallback")
            return None

        # Build client
        client = None
        if settings.GCP_PROJECT_ID:
            try:
                client = genai.Client(
                    vertexai=True,
                    project=settings.GCP_PROJECT_ID,
                    location=getattr(settings, "GCP_REGION", "us-central1"),
                )
            except Exception:
                pass
        if client is None and settings.GEMINI_API_KEY:
            try:
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception:
                return None
        if client is None:
            return None

        # Build grounded prompt
        facts_text = "\n".join(
            f"- {f['key']}: {f['value']} (source: {f['source']})"
            for f in source_facts
        )

        audience_instruction = {
            "executive": "Write for a non-technical healthcare executive. Use plain English. No jargon.",
            "technical": "Write for an IT operations professional. Include technical detail.",
            "board": "Write for a board of directors. Focus on risk, liability, and business continuity.",
        }.get(audience, "Write for a non-technical executive.")

        prompt = f"""You are a security communication specialist for ResilAI.

IMPORTANT RULES:
- You MUST ONLY use the facts provided below. Do NOT invent any data.
- You MUST NOT calculate any scores or percentages.
- You MUST NOT create, remove, or modify any findings.
- You MUST NOT suggest framework mappings or compliance status.
- Your role is ONLY to explain the facts in clear business language.

{audience_instruction}

FACTS:
{facts_text}

Return ONLY valid JSON with this exact schema:
{{
  "plain_language": "A clear 1-2 sentence summary of what this means.",
  "business_impact": "How this affects the organization's operations, risk, or compliance.",
  "recommended_action": "The single most important next step."
}}

Do NOT output anything except the JSON."""

        try:
            config = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=500,
                response_mime_type="application/json",
            )
            response = client.models.generate_content(
                model=self._get_model_name(),
                contents=prompt,
                config=config,
            )
            if response.text:
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:-3]
                data = json.loads(text)
                # Validate schema
                required = {"plain_language", "business_impact", "recommended_action"}
                if required.issubset(data.keys()):
                    return data
        except Exception as e:
            logger.error(f"Gemini explanation generation failed: {e}")

        return None

    # ------------------------------------------------------------------
    # Deterministic fallback
    # ------------------------------------------------------------------

    def _generate_deterministic_fallback(
        self, source_facts: List[Dict[str, str]], audience: str
    ) -> Dict[str, str]:
        """Generate a structured explanation without LLM assistance."""
        # Find key facts
        title = next((f["value"] for f in source_facts if f["key"] == "title"), None)
        severity = next((f["value"] for f in source_facts if f["key"] == "severity"), None)
        status = next((f["value"] for f in source_facts if f["key"] == "status"), None)
        score = next((f["value"] for f in source_facts if f["key"] == "clinic_health_pct"), None)
        recommendation = next((f["value"] for f in source_facts if f["key"] == "recommendation"), None)

        if title and severity:
            plain = f"A {severity}-severity finding was identified: {title}."
            impact = f"This {severity}-severity issue may affect your organization's security posture and regulatory compliance."
            action = recommendation or "Review this finding and address the security gap."
        elif status and score:
            plain = f"Your organization's current readiness status is '{status}' with a health score of {score}%."
            impact = "This represents your overall operational security readiness based on verified evidence."
            action = "Review any open blockers and connect additional evidence sources."
        else:
            plain = "ResilAI has evaluated your organization's security posture based on available evidence."
            impact = "Your readiness is determined by the evidence collected from connected security tools."
            action = "Ensure all security tools are connected and sending data to ResilAI."

        return {
            "plain_language": plain,
            "business_impact": impact,
            "recommended_action": action,
        }
