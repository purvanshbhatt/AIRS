"""Google Antigravity SDK - Autonomous Remediation Agent.

Translates deterministic findings into configuration-level remediation playbooks
by querying vendor documentation using Gemini tool-calling.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("airs.antigravity")

# Mock Vendor Documentation Catalog
MOCK_DOC_CATALOG = {
    "okta": {
        "mfa": "Okta MFA Configuration Guide:\n1. Log in to Okta Admin Console.\n2. Navigate to Security > Authenticators.\n3. Under 'Enrollment', add a new MFA Enrollment Policy or edit the Default Policy.\n4. Set Okta Verify, FIDO2 (WebAuthn), and Google Authenticator to 'Required' or 'Optional'.\n5. Add a Rule to enforce MFA: Set 'Prompt for factor' to 'Every time' or 'Once per session' based on compliance requirements.\n6. Assign the policy to target user groups (e.g., Administrators, AI Engineers).",
        "default": "Okta API Security Guide:\n1. Navigate to Security > API to manage authorization servers.\n2. Go to Directory > People to adjust access groups and roles.\n3. Under Security > General, ensure session lifetime policies are set to strict defaults (max 12 hours)."
    },
    "crowdstrike": {
        "edr": "CrowdStrike Falcon Sensor Deployment Guide:\n1. Log in to CrowdStrike Falcon Console.\n2. Go to Host Setup and Management > Sensor Downloads.\n3. Download the appropriate sensor package (Windows/Linux/macOS).\n4. Install the sensor on target host systems using command:\n   Linux: `sudo dpkg -i falcon-sensor.deb` or `sudo rpm -i falcon-sensor.rpm`\n5. Register the sensor with your CID token:\n   `/opt/CrowdStrike/falconctl -s --cid=<your_customer_id>`\n6. Start the service: `sudo systemctl start falcon-sensor`\n7. Verify EDR telemetry connection in Falcon Console under Host Management or via local check `/opt/CrowdStrike/falconctl -g --aid`.",
        "default": "CrowdStrike Falcon Prevention Policies:\n1. Navigate to Endpoint Security > Prevention Policies.\n2. Enable 'Machine Learning' detection and prevention levels to 'Cautious' or 'Moderate'.\n3. Configure exploit mitigation settings to audit or block unapproved binaries."
    },
    "wazuh": {
        "agent": "Wazuh Agent Registration and Enrollment:\n1. Install Wazuh Agent package on target endpoint.\n2. Run registration command:\n   `/var/ossec/bin/agent-auth -m <wazuh_manager_ip> -p 1515`\n3. Start the service: `sudo systemctl restart wazuh-agent`\n4. Inspect registration logs: `tail -n 100 /var/ossec/logs/ossec.log` to verify successful manager handshake status.",
        "vuln": "Wazuh Vulnerability Detector Configuration:\n1. Edit the wazuh-manager configuration file: `/var/ossec/etc/ossec.conf`.\n2. Search for `<vulnerability-detector>` block and update configurations:\n   ```xml\n   <vulnerability-detector>\n     <enabled>yes</enabled>\n     <interval>5m</interval>\n     <provider name=\"canonical\">\n       <enabled>yes</enabled>\n       <os>trusty</os>\n       <os>xenial</os>\n       <os>bionic</os>\n       <os>focal</os>\n       <os>jammy</os>\n       <update_interval>1h</update_interval>\n     </provider>\n   </vulnerability-detector>\n   ```\n3. Save configuration and restart wazuh-manager: `sudo systemctl restart wazuh-manager`.",
        "default": "Wazuh Security Rules Configuration:\n1. Edit custom rules in `/var/ossec/etc/rules/local_rules.xml`.\n2. Reload configurations by restarting the manager."
    },
    "general": {
        "audit": "Centralized Auditing & Logging Guide:\n1. Enable system-level structured audit logging on server hosts.\n2. Configure syslog forwarder or filebeat/fluentd log shippier to forward `/var/log/audit/audit.log` or Docker container JSON logs to your Centralized SIEM input.\n3. Verify ingest stream parsed correctly and alerts trigger on critical audit events.",
        "default": "General Security Hardening:\n1. Review network firewall rules.\n2. Remove default passwords.\n3. Enforce principle of least privilege on all API keys and system tokens."
    }
}


def search_vendor_documentation(vendor: str, query: str) -> str:
    """Search the official vendor-specific technical guides to find configuration playbooks.

    Args:
        vendor: Name of the vendor (e.g. 'okta', 'crowdstrike', 'wazuh', 'general').
        query: Search keywords or query string.
    """
    v = str(vendor).lower().strip()
    q = str(query).lower().strip()
    
    logger.info("Antigravity SDK Tool Called: search_vendor_documentation(vendor=%s, query=%s)", v, q)
    
    if v not in MOCK_DOC_CATALOG:
        v = "general"
        
    catalog = MOCK_DOC_CATALOG[v]
    
    # Try finding sub-keys
    for key, doc in catalog.items():
        if key != "default" and key in q:
            return doc
            
    # Fallback to default for that vendor
    return catalog.get("default", MOCK_DOC_CATALOG["general"]["default"])


def query_siem_logs_tool(siem_type: str, query_type: str, custom_query: str = "", time_range: str = "-24h") -> str:
    """Query raw SIEM logs for forensic trail generation.

    Args:
        siem_type: Which SIEM to query — 'splunk' or 'wazuh'.
        query_type: Type of query — 'mfa', 'edr', 'logging', 'agents',
                    'vulnerabilities', or 'custom'.
        custom_query: Optional custom SPL query (Splunk only).
        time_range: Time range for the query (e.g., '-24h', '-7d').

    Returns:
        JSON string with SIEM query results.
    """
    import json as _json
    logger.info("Antigravity SDK Tool Called: query_siem_logs(siem=%s, type=%s)", siem_type, query_type)
    return _json.dumps({
        "status": "tool_invoked",
        "siem_type": siem_type,
        "query_type": query_type,
        "custom_query": custom_query,
        "time_range": time_range,
        "message": "SIEM query dispatched. Results injected by the agent loop.",
    })


class AntigravityAgent:
    """Orchestrates the Google Antigravity SDK Remediation Agent.
    
    Integrates Gemini function calling with vendor documentation lookups
    to autonomously generate custom configuration-level playbooks.
    """
    
    def __init__(self):
        self.enabled = settings.is_llm_enabled
        self.demo_mode = settings.is_demo_mode
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.LLM_MODEL
        self.temperature = 0.2
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
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.enabled = False
        return self._client

    def is_available(self) -> bool:
        if self.demo_mode:
            return self.enabled and self._get_client() is not None
        return self.enabled and bool(self.api_key) and self._get_client() is not None

    def execute_remediation_agent(
        self,
        finding_title: str,
        finding_description: str,
        finding_severity: str,
        finding_recommendation: str,
        finding_evidence: str,
        rule_id: str,
    ) -> str:
        """Executes the agentic loop to generate technical remediation steps."""
        
        # 1. Fallback Generation if LLM/Gemini is unavailable or in demo fallback
        if not self.is_available():
            return self._generate_fallback_playbook(
                finding_title, finding_description, finding_severity, finding_recommendation, finding_evidence, rule_id
            )
            
        system_prompt = (
            "You are the ResilAI Remediation Agent. Your goal is to translate identified compliance gaps into specific, actionable remediation steps for technical teams.\n"
            "1. You receive validated findings from the ResilAI Deterministic Governance Engine (do not alter these scores).\n"
            "2. You use the Google Antigravity SDK tools to search for vendor-specific documentation (e.g., CrowdStrike/Okta/Wazuh) relevant to the finding.\n"
            "3. Your goal is to propose specific configuration changes (e.g., 'Enable MFA policy X') that would close the gap.\n"
            "4. You must always maintain separation between your narrative guidance and the immutable scores calculated by the platform.\n"
        )
        
        prompt = f"""Generate a configuration-level remediation playbook for this finding:
        
Title: {finding_title}
Description: {finding_description}
Severity: {finding_severity.upper()}
Evidence: {finding_evidence}
Technical Recommendation: {finding_recommendation}
Rule/Control ID: {rule_id}

Use the 'search_vendor_documentation' tool to find precise config steps for any security vendor (e.g., Okta, CrowdStrike, Wazuh) mentioned in the finding or relevant to the recommendation.
Format your final response in clean markdown. Provide step-by-step instructions.
At the very end of your response, you MUST append this EXACT scoring disclaimer block:

---
**NOTICE**: The numeric scoring of these findings has been calculated deterministically by the ResilAI Governance Engine. Narrative guidance provided above represents expert remediation recommendations and does not modify the baseline score or maturity ratings.
"""
        
        try:
            from google.genai import types
            
            client = self._get_client()
            
            # Map tools
            tools_list = [search_vendor_documentation]
            
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=tools_list,
                temperature=self.temperature,
            )
            
            # Start conversational history or manually execute calls
            contents = [prompt]
            
            # Run up to 5 steps of tool execution
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
                    # Final response generated
                    return response.text or "Failed to generate narrative."
                    
                # We have function calls, execute them and feed them back
                # Append the assistant response to history
                contents.append(response.candidates[0].content)
                
                # Create a part list for function responses
                function_responses = []
                for fc in function_calls:
                    name = fc.name
                    args = fc.args
                    call_id = getattr(fc, "id", None)
                    
                    if name == "search_vendor_documentation":
                        vendor = args.get("vendor", "general")
                        query = args.get("query", "")
                        result = search_vendor_documentation(vendor=vendor, query=query)
                    else:
                        result = f"Error: Tool '{name}' not found."
                        
                    # Formulate Response part
                    response_part = types.Part.from_function_response(
                        name=name,
                        response={"result": result},
                        id=call_id
                    )
                    function_responses.append(response_part)
                
                # Add function responses to history
                contents.append(types.Content(role="user", parts=function_responses))
                
            return "Remediation Agent timed out after maximum tool execution rounds."
            
        except Exception as e:
            logger.error("Antigravity SDK execution failed: %s. Falling back to local playbook.", e)
            return self._generate_fallback_playbook(
                finding_title, finding_description, finding_severity, finding_recommendation, finding_evidence, rule_id
            )

    def _generate_fallback_playbook(
        self,
        title: str,
        desc: str,
        severity: str,
        rec: str,
        evidence: str,
        rule_id: str,
    ) -> str:
        """Fallback playbook generator that uses the mock catalog locally."""
        v = "general"
        q = ""
        
        # Analyze finding for vendor tags
        title_lower = title.lower()
        desc_lower = desc.lower()
        rec_lower = rec.lower()
        
        if "okta" in title_lower or "okta" in desc_lower or "mfa" in title_lower:
            v = "okta"
            q = "mfa" if "mfa" in title_lower or "mfa" in desc_lower else "default"
        elif "crowdstrike" in title_lower or "crowdstrike" in desc_lower or "edr" in title_lower:
            v = "crowdstrike"
            q = "edr" if "edr" in title_lower or "edr" in desc_lower or "sensor" in title_lower else "default"
        elif "wazuh" in title_lower or "wazuh" in desc_lower or "agent" in title_lower:
            v = "wazuh"
            q = "vuln" if "vuln" in title_lower or "vuln" in desc_lower else "agent"
        elif "audit" in title_lower or "logging" in title_lower or "log" in title_lower:
            v = "general"
            q = "audit"
            
        doc_guide = search_vendor_documentation(v, q)
        
        playbook = f"""### Autonomous Remediation Playbook: {title}

**Control ID**: {rule_id}
**Severity**: {severity.upper()}

#### 1. Configuration Investigation
Based on live telemetry findings, the system detected:
* *Evidence*: {evidence}
* *Description*: {desc}

#### 2. Technical Remediation Actions
According to verified vendor configuration standards, execute the following:

{doc_guide}

#### 3. Verification Steps
1. Once configuration is applied, re-trigger the verification endpoint or run an ad-hoc query from the SIEM Integrations page.
2. Confirm the finding moves to **Resolved** status in the Remediation Ledger.

---
**NOTICE**: The numeric scoring of these findings has been calculated deterministically by the ResilAI Governance Engine. Narrative guidance provided above represents expert remediation recommendations and does not modify the baseline score or maturity ratings.
"""
        return playbook


# Singleton instance
_remediation_agent = None

def get_remediation_agent() -> AntigravityAgent:
    global _remediation_agent
    if _remediation_agent is None:
        _remediation_agent = AntigravityAgent()
    return _remediation_agent


# Re-export ForensicTrailAgent for convenience
def get_forensic_trail_agent():
    """Convenience re-export from forensic_trail module."""
    from app.services.forensic_trail import get_forensic_trail_agent as _get
    return _get()
