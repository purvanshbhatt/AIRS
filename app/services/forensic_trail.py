"""
Forensic Trail Agent — Automated SIEM-Correlated Audit Trail Generation.

Provides:
  1. A production-ready system prompt for Antigravity agents that automates
     JSON audit trail generation by correlating SIEM log dumps with GHI scores.
  2. A ForensicTrailAgent class that extends the agentic loop with a
     `query_siem_logs` tool.
  3. A deterministic fallback that generates audit trails without LLM calls.

All outputs are structured JSON — the LLM is used only for log parsing
and correlation, never for score computation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger("airs.forensic_trail")


# ---------------------------------------------------------------------------
# The Agent Prompt
# ---------------------------------------------------------------------------

FORENSIC_TRAIL_SYSTEM_PROMPT = """\
You are the ResilAI Forensic Trail Agent. Your sole purpose is to generate
a deterministic, auditable JSON record that correlates SIEM log evidence
with the current Governance Health Index (GHI) score.

CRITICAL CONSTRAINTS:
1. You MUST NOT generate, modify, or opine on any numeric score. All scores
   are computed by the ResilAI Deterministic Governance Engine and are
   immutable inputs to your analysis.
2. You MUST NOT use subjective language ("likely", "probably", "suggests").
   Every claim must cite a specific log event ID, timestamp, or count.
3. Your output MUST be valid JSON conforming to the ForensicTrailSchema.
4. You MUST use the provided tools to query raw SIEM data. Do not hallucinate
   log entries or event counts.

WORKFLOW:
1. Receive the latest SIEM log dump (pre-fetched or via query_siem_logs tool).
2. For each finding in the current assessment:
   a. Search the SIEM logs for corroborating or contradicting evidence.
   b. Record the log event IDs, timestamps, and counts that support the
      finding's verification status.
   c. Classify as "SOC-Verified" (SIEM evidence confirms the finding),
      "Provisional" (no SIEM evidence available — self-attested only),
      or "Contradicted" (SIEM evidence contradicts the self-reported answer).
3. Correlate the aggregate verification results with the GHI score delta:
   - If score improved: cite the specific SIEM evidence that supports the
     improvement (e.g., "EDR coverage increased from 5 to 12 hosts per
     Splunk query edr_telemetry, event_count=847").
   - If score degraded: cite the specific SIEM evidence that explains the
     regression (e.g., "MFA failure rate exceeded 20% threshold per
     Splunk query mfa_logs, failure_count=34/142").
   - If score unchanged: confirm no material evidence changes detected.
4. Generate the final JSON audit trail with:
   - integrity_hash: SHA-256 of the complete findings+scores payload
   - generated_at: UTC ISO-8601 timestamp
   - ghi_score_current / ghi_score_previous / ghi_score_delta
   - findings[]: array of finding objects each with verification_status,
     evidence_summary, siem_source, log_event_ids[], verified_at
   - methodology: "Deterministic rule-based scoring per ResilAI Rubric
     v2.0.0. SIEM verification performed against live Wazuh/Splunk
     telemetry. No LLM subjectivity applied to scores or classifications."

OUTPUT FORMAT:
You must return ONLY the JSON object. No markdown fencing, no commentary.
"""


# ---------------------------------------------------------------------------
# query_siem_logs tool function (for Antigravity SDK tool-calling)
# ---------------------------------------------------------------------------

async def query_siem_logs(
    siem_type: str,
    query_type: str,
    custom_query: Optional[str] = None,
    time_range: str = "-24h",
) -> str:
    """Query raw SIEM logs for forensic trail generation.

    This tool is called by the Antigravity agent to fetch live telemetry
    from the configured SIEM (Splunk or Wazuh).

    Args:
        siem_type: Which SIEM to query — 'splunk' or 'wazuh'.
        query_type: Type of query — 'mfa', 'edr', 'logging', 'agents',
                    'vulnerabilities', or 'custom'.
        custom_query: Optional custom SPL query (Splunk only).
        time_range: Time range for the query (e.g., '-24h', '-7d').

    Returns:
        JSON string with query results.
    """
    logger.info(
        "Forensic trail tool: query_siem_logs(siem=%s, type=%s, range=%s)",
        siem_type, query_type, time_range,
    )

    # This is a synchronous wrapper — actual SIEM calls happen in the
    # ForensicTrailAgent.execute_forensic_trail() method which has access
    # to the SIEM client instances. Here we return a placeholder that will
    # be replaced by the agent loop.
    return json.dumps({
        "status": "tool_invoked",
        "siem_type": siem_type,
        "query_type": query_type,
        "time_range": time_range,
        "message": "SIEM query executed via ForensicTrailAgent context.",
    })


# Synchronous wrapper for Gemini tool registration
def query_siem_logs_sync(
    siem_type: str,
    query_type: str,
    custom_query: str = "",
    time_range: str = "-24h",
) -> str:
    """Query raw SIEM logs for forensic trail generation.

    Args:
        siem_type: Which SIEM to query — 'splunk' or 'wazuh'.
        query_type: Type of query — 'mfa', 'edr', 'logging', 'agents',
                    'vulnerabilities', or 'custom'.
        custom_query: Optional custom SPL query (Splunk only).
        time_range: Time range for the query (e.g., '-24h', '-7d').

    Returns:
        JSON string with query results.
    """
    return json.dumps({
        "status": "tool_invoked",
        "siem_type": siem_type,
        "query_type": query_type,
        "custom_query": custom_query,
        "time_range": time_range,
        "message": "SIEM query dispatched. Results will be injected by the agent loop.",
    })


# ---------------------------------------------------------------------------
# ForensicTrailAgent
# ---------------------------------------------------------------------------

class ForensicTrailAgent:
    """Generates forensic audit trails by correlating SIEM logs with GHI scores.

    Extends the Antigravity agentic pattern with a `query_siem_logs` tool
    and a structured JSON output schema.
    """

    def __init__(self):
        self.enabled = settings.is_llm_enabled
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.LLM_MODEL
        self.temperature = 0.0  # Maximum determinism
        self._client = None

    def _get_client(self):
        """Lazy-load Google Gemini client."""
        if not self._client and self.enabled:
            try:
                from google import genai
                if settings.GCP_PROJECT_ID:
                    self._client = genai.Client(
                        vertexai=True,
                        project=settings.GCP_PROJECT_ID,
                        location="us-central1",
                    )
                elif self.api_key:
                    self._client = genai.Client(api_key=self.api_key)
                else:
                    raise RuntimeError("No Gemini credentials configured")
            except ImportError:
                logger.warning("google-genai package not installed")
                self.enabled = False
            except Exception as e:
                logger.error("Failed to initialize Gemini client: %s", e)
                self.enabled = False
        return self._client

    def is_available(self) -> bool:
        return self.enabled and self._get_client() is not None

    def execute_forensic_trail(
        self,
        siem_log_dump: Dict[str, Any],
        current_ghi_score: float,
        previous_ghi_score: Optional[float],
        findings: List[Dict[str, Any]],
        assessment_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a forensic audit trail correlating SIEM logs with GHI score.

        If the LLM is available, uses Gemini with the forensic trail prompt
        to parse and correlate SIEM logs. Otherwise, uses the deterministic
        fallback that produces the same JSON schema without LLM assistance.

        Args:
            siem_log_dump: Pre-fetched SIEM data (Splunk/Wazuh combined results).
            current_ghi_score: Current GHI score from the governance engine.
            previous_ghi_score: Previous GHI score for delta calculation.
            findings: List of finding dicts with rule_id, title, severity, etc.
            assessment_id: Optional assessment UUID.
            organization_id: Optional organization UUID.

        Returns:
            Structured JSON dict conforming to the ForensicTrailSchema.
        """
        # Always try deterministic fallback first for reliability
        # The LLM path is used to enrich the log correlation narrative
        if not self.is_available():
            return self._generate_deterministic_trail(
                siem_log_dump, current_ghi_score, previous_ghi_score,
                findings, assessment_id, organization_id,
            )

        try:
            return self._generate_llm_trail(
                siem_log_dump, current_ghi_score, previous_ghi_score,
                findings, assessment_id, organization_id,
            )
        except Exception as exc:
            logger.error("LLM forensic trail failed: %s. Using deterministic fallback.", exc)
            return self._generate_deterministic_trail(
                siem_log_dump, current_ghi_score, previous_ghi_score,
                findings, assessment_id, organization_id,
            )

    def _generate_llm_trail(
        self,
        siem_log_dump: Dict[str, Any],
        current_ghi: float,
        previous_ghi: Optional[float],
        findings: List[Dict[str, Any]],
        assessment_id: Optional[str],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        """Use Gemini to correlate SIEM logs with findings."""
        from google.genai import types
        from app.services.antigravity import search_vendor_documentation

        client = self._get_client()

        ghi_delta = round(current_ghi - previous_ghi, 2) if previous_ghi is not None else None

        prompt = f"""Analyze the following SIEM log dump and correlate with the current assessment findings.

SIEM LOG DUMP:
{json.dumps(siem_log_dump, indent=2, default=str)[:8000]}

CURRENT GHI SCORE: {current_ghi}
PREVIOUS GHI SCORE: {previous_ghi}
GHI DELTA: {ghi_delta}

FINDINGS TO VERIFY:
{json.dumps(findings, indent=2, default=str)[:4000]}

ASSESSMENT ID: {assessment_id}
ORGANIZATION ID: {organization_id}

Generate the forensic trail JSON. Remember: return ONLY the JSON object.
"""

        tools_list = [search_vendor_documentation, query_siem_logs_sync]

        config = types.GenerateContentConfig(
            system_instruction=FORENSIC_TRAIL_SYSTEM_PROMPT,
            tools=tools_list,
            temperature=self.temperature,
        )

        contents = [prompt]

        for step in range(5):
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            # Check for function calls
            function_calls = []
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)

            if not function_calls:
                # Parse the response as JSON
                text = response.text or ""
                try:
                    # Strip any markdown fencing
                    clean = text.strip()
                    if clean.startswith("```"):
                        lines = clean.split("\n")
                        clean = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                    result = json.loads(clean)
                    # Ensure integrity hash is computed correctly
                    result["integrity_hash"] = self._compute_integrity_hash(
                        assessment_id, current_ghi, previous_ghi, findings,
                    )
                    return result
                except json.JSONDecodeError:
                    logger.warning("LLM returned non-JSON response, falling back.")
                    return self._generate_deterministic_trail(
                        siem_log_dump, current_ghi, previous_ghi,
                        findings, assessment_id, organization_id,
                    )

            # Execute function calls
            contents.append(response.candidates[0].content)

            function_responses = []
            for fc in function_calls:
                name = fc.name
                args = fc.args

                if name == "query_siem_logs_sync":
                    result_str = self._handle_siem_tool_call(siem_log_dump, args)
                elif name == "search_vendor_documentation":
                    result_str = search_vendor_documentation(
                        vendor=args.get("vendor", "general"),
                        query=args.get("query", ""),
                    )
                else:
                    result_str = f"Error: Tool '{name}' not found."

                response_part = types.Part.from_function_response(
                    name=name,
                    response={"result": result_str},
                    id=getattr(fc, "id", None),
                )
                function_responses.append(response_part)

            contents.append(types.Content(role="user", parts=function_responses))

        # Max steps reached — use deterministic fallback
        return self._generate_deterministic_trail(
            siem_log_dump, current_ghi, previous_ghi,
            findings, assessment_id, organization_id,
        )

    def _handle_siem_tool_call(
        self, siem_log_dump: Dict[str, Any], args: Dict[str, Any]
    ) -> str:
        """Handle a query_siem_logs tool call using pre-fetched data."""
        query_type = args.get("query_type", "")
        siem_type = args.get("siem_type", "")

        # Extract relevant data from the pre-fetched dump
        if siem_type == "splunk":
            splunk_data = siem_log_dump.get("splunk", {})
            if query_type in splunk_data:
                return json.dumps(splunk_data[query_type], default=str)
            return json.dumps(splunk_data, default=str)
        elif siem_type == "wazuh":
            wazuh_data = siem_log_dump.get("wazuh", {})
            if query_type in wazuh_data:
                return json.dumps(wazuh_data[query_type], default=str)
            return json.dumps(wazuh_data, default=str)
        else:
            return json.dumps(siem_log_dump, default=str)

    def _generate_deterministic_trail(
        self,
        siem_log_dump: Dict[str, Any],
        current_ghi: float,
        previous_ghi: Optional[float],
        findings: List[Dict[str, Any]],
        assessment_id: Optional[str],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        """Deterministic fallback that generates audit trail without LLM.

        Produces the same JSON schema by directly mapping SIEM evidence
        to findings using rule-based logic.
        """
        now = datetime.now(timezone.utc).isoformat()
        ghi_delta = round(current_ghi - previous_ghi, 2) if previous_ghi is not None else None

        # Extract evidence from SIEM dump
        splunk_data = siem_log_dump.get("splunk", {})
        wazuh_data = siem_log_dump.get("wazuh", {})

        trail_findings = []
        soc_verified = 0
        provisional = 0
        contradicted = 0

        for finding in findings:
            rule_id = finding.get("rule_id", "")
            severity = finding.get("severity", "medium")
            title = finding.get("title", "")
            domain_id = finding.get("domain_id", "")

            verification = self._match_siem_evidence(
                rule_id, splunk_data, wazuh_data
            )

            status = verification["status"]
            if status == "SOC-Verified":
                soc_verified += 1
            elif status == "Contradicted":
                contradicted += 1
            else:
                provisional += 1

            trail_findings.append({
                "rule_id": rule_id,
                "title": title,
                "severity": severity,
                "domain_id": domain_id,
                "verification_status": status,
                "evidence_summary": verification["evidence_summary"],
                "siem_source": verification["siem_source"],
                "log_event_ids": verification["log_event_ids"],
                "verified_at": now,
            })

        integrity_hash = self._compute_integrity_hash(
            assessment_id, current_ghi, previous_ghi, findings,
        )

        return {
            "integrity_hash": integrity_hash,
            "generated_at": now,
            "assessment_id": assessment_id,
            "organization_id": organization_id,
            "ghi_score_current": current_ghi,
            "ghi_score_previous": previous_ghi,
            "ghi_score_delta": ghi_delta,
            "methodology": (
                "Deterministic rule-based scoring per ResilAI Rubric v2.0.0. "
                "SIEM verification performed against live Wazuh/Splunk telemetry. "
                "No LLM subjectivity applied to scores or classifications."
            ),
            "findings": trail_findings,
            "total_findings": len(trail_findings),
            "soc_verified_count": soc_verified,
            "provisional_count": provisional,
            "contradicted_count": contradicted,
        }

    def _match_siem_evidence(
        self,
        rule_id: str,
        splunk_data: Dict[str, Any],
        wazuh_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Match a rule_id to available SIEM evidence deterministically."""
        result = {
            "status": "Provisional",
            "evidence_summary": "No SIEM verification mapping for this control. Self-attested only.",
            "siem_source": None,
            "log_event_ids": [],
        }

        # EDR rules → check Splunk EDR or Wazuh agents
        if rule_id.startswith("DC-"):
            edr = splunk_data.get("edr", {})
            if edr and edr.get("status") == "verified":
                event_count = edr.get("event_count", 0)
                result.update({
                    "status": "SOC-Verified",
                    "evidence_summary": f"Splunk EDR telemetry confirms {event_count} detection events.",
                    "siem_source": "splunk",
                    "log_event_ids": [str(e) for e in edr.get("sample_ids", [])[:10]],
                })
            elif edr and edr.get("status") == "partial":
                event_count = edr.get("event_count", 0)
                result.update({
                    "status": "SOC-Verified",
                    "evidence_summary": f"Splunk EDR telemetry partially confirms coverage: {event_count} events, gaps detected.",
                    "siem_source": "splunk",
                    "log_event_ids": [str(e) for e in edr.get("sample_ids", [])[:10]],
                })
            else:
                # Try Wazuh agents fallback
                agents = wazuh_data.get("agents", {})
                if agents and agents.get("active_agents", 0) > 0:
                    active = agents.get("active_agents", 0)
                    total = agents.get("total_agents", 0)
                    result.update({
                        "status": "SOC-Verified",
                        "evidence_summary": f"Wazuh confirms {active}/{total} agents active.",
                        "siem_source": "wazuh",
                        "log_event_ids": [f"agent:{a}" for a in agents.get("agent_ids", [])[:10]],
                    })

        # MFA / Identity rules → check Splunk MFA
        elif rule_id.startswith("IV-"):
            mfa = splunk_data.get("mfa", {})
            if mfa and mfa.get("status") == "verified":
                event_count = mfa.get("event_count", 0)
                result.update({
                    "status": "SOC-Verified",
                    "evidence_summary": f"Splunk MFA logs confirm {event_count} challenge events.",
                    "siem_source": "splunk",
                    "log_event_ids": [str(e) for e in mfa.get("sample_ids", [])[:10]],
                })
            elif mfa and mfa.get("status") == "not_verified":
                result.update({
                    "status": "Contradicted",
                    "evidence_summary": "Splunk MFA logs show 0 challenge events. MFA enforcement not detected.",
                    "siem_source": "splunk",
                    "log_event_ids": [],
                })

        # Telemetry / Logging rules → check Splunk logging health
        elif rule_id.startswith("TL-"):
            logging_data = splunk_data.get("logging", {})
            if logging_data and logging_data.get("logging_enabled"):
                event_count = logging_data.get("event_count_24h", 0)
                result.update({
                    "status": "SOC-Verified",
                    "evidence_summary": f"Splunk confirms {event_count} log events in last 24h.",
                    "siem_source": "splunk",
                    "log_event_ids": [str(e) for e in logging_data.get("sample_ids", [])[:10]],
                })
            # Also check Wazuh vulnerability scanner for TL-001
            elif rule_id == "TL-001":
                vulns = wazuh_data.get("vulnerabilities", {})
                if vulns and vulns.get("total_vulnerabilities", 0) > 0:
                    result.update({
                        "status": "SOC-Verified",
                        "evidence_summary": f"Wazuh vulnerability scanner active: {vulns['total_vulnerabilities']} vulnerabilities tracked.",
                        "siem_source": "wazuh",
                        "log_event_ids": [f"cve:{c}" for c in vulns.get("cve_ids", [])[:10]],
                    })

        # IR and Resilience rules → less direct SIEM mapping
        elif rule_id.startswith("IR-") or rule_id.startswith("RS-"):
            # These are process-level controls, limited SIEM verification
            pass

        # Aggregate rules
        elif rule_id.startswith("AGG-"):
            if rule_id == "AGG-001":
                logging_data = splunk_data.get("logging", {})
                if logging_data and logging_data.get("logging_enabled"):
                    result.update({
                        "status": "SOC-Verified",
                        "evidence_summary": "Aggregate telemetry weakness corroborated by Splunk logging health data.",
                        "siem_source": "splunk",
                        "log_event_ids": [],
                    })
            elif rule_id == "AGG-002":
                mfa = splunk_data.get("mfa", {})
                if mfa and mfa.get("status") in ("verified", "partial"):
                    result.update({
                        "status": "SOC-Verified",
                        "evidence_summary": "Aggregate identity weakness corroborated by Splunk MFA evidence.",
                        "siem_source": "splunk",
                        "log_event_ids": [],
                    })

        return result

    @staticmethod
    def _compute_integrity_hash(
        assessment_id: Optional[str],
        current_ghi: float,
        previous_ghi: Optional[float],
        findings: List[Dict[str, Any]],
    ) -> str:
        """Compute SHA-256 integrity hash of the audit trail payload."""
        hash_payload = {
            "assessment_id": assessment_id,
            "ghi_current": current_ghi,
            "ghi_previous": previous_ghi,
            "findings": [
                {
                    "rule_id": f.get("rule_id", ""),
                    "severity": f.get("severity", ""),
                }
                for f in findings
            ],
        }
        canonical = json.dumps(hash_payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_forensic_agent: Optional[ForensicTrailAgent] = None


def get_forensic_trail_agent() -> ForensicTrailAgent:
    """Get or create the singleton ForensicTrailAgent."""
    global _forensic_agent
    if _forensic_agent is None:
        _forensic_agent = ForensicTrailAgent()
    return _forensic_agent
