"""
AIRS LLM Narrative Generator

AI-assisted narrative generation for executive summaries and roadmaps.
The LLM CANNOT modify scores - it only generates human-readable narratives
from deterministic scores and findings.

IMPORTANT - LLM Scope Limitations:
  The LLM is strictly limited to generating narrative text:
    ✓ Executive summary paragraph
    ✓ 30/60/90 day roadmap narrative  
    ✓ Finding rewrites in business tone
  
  The LLM does NOT and CANNOT modify:
    ✗ Numeric scores (overall_score, domain_scores)
    ✗ Maturity tier/level
    ✗ Findings (count, severity, recommendations)
    ✗ Any structured assessment data

Demo Mode:
  When DEMO_MODE=true, LLM can run without strict API key validation.
  Falls back to deterministic text if LLM fails.

Feature flags:
  - AIRS_USE_LLM: Enable/disable LLM (default: False)
  - DEMO_MODE: Allow LLM without strict validation (default: False)
  - GEMINI_API_KEY: Optional in demo mode (uses ADC on Cloud Run)
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)


class NarrativeType(str, Enum):
    """Types of narratives the LLM can generate."""
    EXECUTIVE_SUMMARY = "executive_summary"
    ROADMAP_30_60_90 = "roadmap"
    FINDING_BUSINESS_TONE = "finding_rewrite"


@dataclass
class ScoreContext:
    """Immutable score context passed to LLM (read-only)."""
    overall_score: float
    maturity_level: int
    maturity_name: str
    domain_scores: List[Dict[str, Any]]
    
    def to_prompt_context(self) -> str:
        """Format scores for LLM prompt (read-only display)."""
        lines = [
            f"Overall Score: {self.overall_score:.1f}/100",
            f"Maturity Level: {self.maturity_level} - {self.maturity_name}",
            "",
            "Domain Scores:"
        ]
        for ds in self.domain_scores:
            lines.append(f"  - {ds.get('domain_name', ds.get('domain_id'))}: {ds.get('score', 0):.1f}%")
        return "\n".join(lines)


@dataclass
class FindingContext:
    """Immutable finding context passed to LLM (read-only)."""
    rule_id: str
    title: str
    domain_name: str
    severity: str
    evidence: str
    recommendation: str
    
    def to_prompt_context(self) -> str:
        """Format finding for LLM prompt."""
        return f"""
Finding: {self.title}
Severity: {self.severity.upper()}
Domain: {self.domain_name}
Evidence: {self.evidence}
Technical Recommendation: {self.recommendation}
"""


@dataclass
class NarrativeResult:
    """Result from narrative generation."""
    narrative_type: NarrativeType
    content: str
    llm_generated: bool
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None


class LLMNarrativeGenerator:
    """
    Generates AI-assisted narratives from deterministic assessment data.
    
    IMPORTANT: This class NEVER modifies scores or findings.
    It only generates human-readable narratives from immutable data.
    
    Uses Google Gemini API for generation.
    In demo mode, can use ADC without explicit API key.
    """
    
    def __init__(self):
        # Use the is_llm_enabled property which handles demo mode
        self.enabled = settings.is_llm_enabled
        self.demo_mode = settings.is_demo_mode
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        self._client = None
        
        # Log demo mode warning
        if self.enabled and self.demo_mode:
            logger.warning("LLM running in demo mode - generates narratives only, no score modification")
        
    def _get_client(self):
        """Lazy-load Google Gemini client."""
        if not self._client and self.enabled:
            try:
                import google.generativeai as genai
                # Configure with API key if available, otherwise ADC
                if self.api_key:
                    genai.configure(api_key=self.api_key)
                # ADC is used automatically on Cloud Run if no API key
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                logger.warning("Google GenerativeAI package not installed. Run: pip install google-generativeai")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.enabled = False
        return self._client
    
    def is_available(self) -> bool:
        """Check if LLM features are available."""
        # In demo mode, try without strict API key check
        if self.demo_mode:
            return self.enabled and self._get_client() is not None
        return self.enabled and bool(self.api_key) and self._get_client() is not None
    
    def _generate_content(self, prompt: str, max_tokens: int = None) -> tuple[str, Optional[int]]:
        """Generate content using Gemini."""
        import google.generativeai as genai
        
        generation_config = genai.GenerationConfig(
            temperature=self.temperature,
        )
        
        response = self._get_client().generate_content(
            prompt,
            generation_config=generation_config
        )
        
        content = response.text
        # Gemini doesn't provide token count the same way, estimate from response
        tokens_used = None
        if hasattr(response, 'usage_metadata'):
            tokens_used = getattr(response.usage_metadata, 'total_token_count', None)
        
        return content, tokens_used
    
    def generate_executive_summary(
        self,
        scores: ScoreContext,
        findings: List[FindingContext],
        organization_name: str = "the organization"
    ) -> NarrativeResult:
        """
        Generate an executive summary paragraph.
        
        The LLM receives READ-ONLY score data and generates a narrative.
        Scores are NEVER modified - they are passed as immutable context.
        """
        if not self.is_available():
            return self._fallback_executive_summary(scores, findings, organization_name)
        
        # Build prompt with immutable score context
        critical_high = len([f for f in findings if f.severity.lower() in ("critical", "high")])
        
        prompt = f"""Write a professional executive summary for {organization_name}'s AI Security Assessment.

Assessment Results:
{scores.to_prompt_context()}

Key Statistics:
- Total findings identified: {len(findings)}
- Critical/High severity: {critical_high}
- Areas for improvement: {self._get_weak_domains(scores)}

Write 2-3 paragraphs suitable for board presentation that:
1. State the overall security posture based on the score
2. Highlight key strengths or concerns
3. Provide a high-level recommendation"""

        try:
            content, tokens = self._generate_content(prompt)
            
            return NarrativeResult(
                narrative_type=NarrativeType.EXECUTIVE_SUMMARY,
                content=content,
                llm_generated=True,
                model_used=self.model,
                tokens_used=tokens
            )
            
        except Exception as e:
            logger.error(f"LLM executive summary generation failed: {e}")
            return self._fallback_executive_summary(scores, findings, organization_name)
    
    def generate_roadmap_narrative(
        self,
        scores: ScoreContext,
        findings: List[FindingContext],
        organization_name: str = "the organization"
    ) -> NarrativeResult:
        """
        Generate a 30/60/90 day roadmap narrative.
        
        Prioritizes findings by severity and provides actionable timelines.
        """
        if not self.is_available():
            return self._fallback_roadmap(scores, findings)
        
        # Categorize findings by severity for the prompt
        critical = [f for f in findings if f.severity.lower() == "critical"]
        high = [f for f in findings if f.severity.lower() == "high"]
        medium = [f for f in findings if f.severity.lower() == "medium"]
        low = [f for f in findings if f.severity.lower() == "low"]
        
        findings_summary = []
        for f in (critical + high + medium)[:10]:  # Top 10 findings
            findings_summary.append(f.to_prompt_context())
        
        prompt = f"""You are a security program manager creating a remediation roadmap.
Write actionable, time-bound recommendations organized into 30/60/90 day phases.
Be specific about what should be done in each phase.
Focus on business-friendly language that non-technical executives can understand.

Create a 30/60/90 day security improvement roadmap for {organization_name}.

CURRENT STATE:
{scores.to_prompt_context()}

FINDINGS TO ADDRESS:
- Critical: {len(critical)}
- High: {len(high)}  
- Medium: {len(medium)}
- Low: {len(low)}

TOP FINDINGS REQUIRING ATTENTION:
{"".join(findings_summary)}

Create a roadmap with:
- FIRST 30 DAYS: Immediate/critical actions (quick wins and critical fixes)
- DAYS 31-60: Foundation building (process improvements, tool deployments)
- DAYS 61-90: Maturity advancement (policy refinements, training programs)

For each phase, list 3-5 specific, actionable items with expected outcomes."""

        try:
            content, tokens = self._generate_content(prompt)
            
            return NarrativeResult(
                narrative_type=NarrativeType.ROADMAP_30_60_90,
                content=content,
                llm_generated=True,
                model_used=self.model,
                tokens_used=tokens
            )
            
        except Exception as e:
            logger.error(f"LLM roadmap generation failed: {e}")
            return self._fallback_roadmap(scores, findings)
    
    def rewrite_finding_business_tone(
        self,
        finding: FindingContext
    ) -> NarrativeResult:
        """
        Rewrite a technical finding in business-friendly language.
        
        Preserves severity and core recommendation but makes it
        accessible to non-technical stakeholders.
        """
        if not self.is_available():
            return self._fallback_finding_rewrite(finding)
        
        prompt = f"""You are a security consultant translating technical findings for business executives.
Rewrite the finding to be understood by non-technical stakeholders.
Preserve the severity and core message, but explain business impact.
Keep it concise - 2-3 sentences maximum.

Rewrite this technical security finding for a business audience:

{finding.to_prompt_context()}

Provide:
1. A business-friendly title (1 line)
2. Business impact statement (1-2 sentences)
3. Executive recommendation (1 sentence)

Keep the same severity level ({finding.severity.upper()}) and core message."""

        try:
            content, tokens = self._generate_content(prompt, max_tokens=300)
            
            return NarrativeResult(
                narrative_type=NarrativeType.FINDING_BUSINESS_TONE,
                content=content,
                llm_generated=True,
                model_used=self.model,
                tokens_used=tokens
            )
            
        except Exception as e:
            logger.error(f"LLM finding rewrite failed: {e}")
            return self._fallback_finding_rewrite(finding)
    
    def _get_weak_domains(self, scores: ScoreContext) -> str:
        """Get domains with lowest scores."""
        sorted_domains = sorted(scores.domain_scores, key=lambda x: x.get('score', 0))
        weak = sorted_domains[:2]
        return ", ".join([d.get('domain_name', d.get('domain_id', 'Unknown')) for d in weak])
    
    def _fallback_executive_summary(
        self,
        scores: ScoreContext,
        findings: List[FindingContext],
        org_name: str
    ) -> NarrativeResult:
        """Deterministic fallback when LLM is unavailable."""
        critical_high = len([f for f in findings if f.severity.lower() in ("critical", "high")])
        
        # Determine posture based on score
        if scores.overall_score >= 80:
            posture = "strong"
            outlook = "well-positioned"
        elif scores.overall_score >= 60:
            posture = "moderate"
            outlook = "has foundational controls but needs improvement"
        elif scores.overall_score >= 40:
            posture = "developing"
            outlook = "requires significant attention to key security areas"
        else:
            posture = "critical"
            outlook = "faces substantial security gaps requiring immediate action"
        
        content = f"""{org_name} achieved an overall AI Security Readiness Score of {scores.overall_score:.1f}/100, indicating a {posture} security posture. The organization {outlook}.

The assessment identified {len(findings)} findings across {len(scores.domain_scores)} security domains, with {critical_high} rated as critical or high severity. Key areas requiring attention include {self._get_weak_domains(scores)}.

Immediate focus should be placed on addressing critical findings while developing a systematic approach to security maturity improvement."""
        
        return NarrativeResult(
            narrative_type=NarrativeType.EXECUTIVE_SUMMARY,
            content=content,
            llm_generated=False
        )
    
    def _fallback_roadmap(
        self,
        scores: ScoreContext,
        findings: List[FindingContext]
    ) -> NarrativeResult:
        """Deterministic fallback roadmap."""
        critical = [f for f in findings if f.severity.lower() == "critical"]
        high = [f for f in findings if f.severity.lower() == "high"]
        medium = [f for f in findings if f.severity.lower() == "medium"]
        
        lines = ["## 30/60/90 Day Security Improvement Roadmap\n"]
        
        # 30 days
        lines.append("### First 30 Days: Critical Remediation")
        if critical:
            for f in critical[:3]:
                lines.append(f"- **{f.title}**: {f.recommendation}")
        else:
            lines.append("- Review and validate security baseline configurations")
            lines.append("- Conduct security awareness session with key stakeholders")
        lines.append("")
        
        # 60 days  
        lines.append("### Days 31-60: Foundation Building")
        if high:
            for f in high[:3]:
                lines.append(f"- **{f.title}**: {f.recommendation}")
        else:
            lines.append("- Implement enhanced monitoring and logging")
            lines.append("- Develop incident response procedures")
        lines.append("")
        
        # 90 days
        lines.append("### Days 61-90: Maturity Advancement")
        if medium:
            for f in medium[:3]:
                lines.append(f"- **{f.title}**: {f.recommendation}")
        else:
            lines.append("- Establish regular security review cadence")
            lines.append("- Implement continuous improvement metrics")
        
        return NarrativeResult(
            narrative_type=NarrativeType.ROADMAP_30_60_90,
            content="\n".join(lines),
            llm_generated=False
        )
    
    def _fallback_finding_rewrite(self, finding: FindingContext) -> NarrativeResult:
        """Deterministic fallback for finding rewrite."""
        # Simple business-friendly transformation
        severity_impact = {
            "critical": "poses an immediate and severe risk to business operations",
            "high": "represents a significant risk that should be addressed promptly",
            "medium": "presents a moderate risk that should be planned for remediation",
            "low": "is a minor issue that should be addressed as resources allow"
        }
        
        impact = severity_impact.get(finding.severity.lower(), "requires attention")
        
        content = f"""**{finding.title}**

This issue {impact}. {finding.evidence}

**Business Recommendation**: {finding.recommendation}"""
        
        return NarrativeResult(
            narrative_type=NarrativeType.FINDING_BUSINESS_TONE,
            content=content,
            llm_generated=False
        )


# Singleton instance
_generator = None

def get_narrative_generator() -> LLMNarrativeGenerator:
    """Get or create the narrative generator singleton."""
    global _generator
    if _generator is None:
        _generator = LLMNarrativeGenerator()
    return _generator

