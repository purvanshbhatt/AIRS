"""
Organization profile enrichment service.

Extracts metadata from websites and infers baseline security profiles.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

from app.core.url_fetcher import fetch_url
from app.schemas.organization import EnrichmentResponse

logger = logging.getLogger(__name__)

# Baseline profile keywords for inference
PROFILE_KEYWORDS = {
    "smb": [
        "local", "family owned", "restaurant", "cafe", "shop", "store", "boutique", 
        "plumbing", "hvac", "repair", "cleaning", "landscaping", "salon", "gym",
        "small business", "serving", "community"
    ],
    "saas_startup": [
        "software", "platform", "cloud", "api", "ai", "artificial intelligence", 
        "machine learning", "data", "analytics", "dashboard", "integration", 
        "workflow", "automation", "tech", "startup", "developer"
    ],
    "healthcare": [
        "health", "medical", "care", "patient", "clinic", "hospital", "doctor", 
        "wellness", "therapy", "treatment", "pharmacy", "healthcare", "hipaa"
    ],
    "financial": [
        "bank", "finance", "money", "invest", "investment", "insurance", "capital", 
        "wealth", "financial", "payment", "crypto", "trading", "broker", "fund"
    ],
    "enterprise": [
        "global", "corporation", "international", "leader", "worldwide", "integrated", 
        "enterprise", "solutions", "group", "holding", "conglomerate", "fortune"
    ]
}


class EnrichmentService:
    """Service to enrich organization profiles from URLs."""

    def enrich_from_url(self, url: str) -> EnrichmentResponse:
        """
        Fetch URL and extract profile information.
        
        Args:
            url: The website URL to analyze.
            
        Returns:
            EnrichmentResponse with extracted metadata and suggestions.
        """
        logger.info(f"Enriching profile from URL: {url}")
        
        # 1. Fetch content securely
        try:
            html_content = fetch_url(url)
        except Exception as e:
            logger.warning(f"Failed to fetch URL {url}: {e}")
            # Return empty result with error indication conceptually (or just empty)
            # Schema requires source_url, others optional
            return EnrichmentResponse(source_url=url, description=f"Failed to fetch website: {str(e)}")

        # 2. Parse HTML
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract Metadata
            title = self._get_title(soup)
            description = self._get_meta_content(soup, "description") or self._get_og_content(soup, "description")
            keywords_str = self._get_meta_content(soup, "keywords")
            
            keywords = []
            if keywords_str:
                keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            
            # 3. Infer Baseline
            # Combine text for analysis
            analysis_text = f"{title or ''} {description or ''} {' '.join(keywords)}".lower()
            baseline, confidence = self._infer_baseline(analysis_text)
            
            return EnrichmentResponse(
                title=title,
                description=description,
                keywords=keywords,
                baseline_suggestion=baseline,
                confidence=confidence,
                source_url=url
            )
            
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {e}")
            return EnrichmentResponse(source_url=url, description="Error analyzing website content")

    def _get_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
            
        return None

    def _get_meta_content(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """Extract meta tag content by name."""
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    def _get_og_content(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """Extract open graph tag content."""
        # Check 'property' attribute (standard OG)
        tag = soup.find("meta", property=f"og:{property_name}")
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    def _infer_baseline(self, text: str) -> Tuple[Optional[str], float]:
        """
        Infer baseline profile from text analysis.
        Returns (profile_key, confidence_score).
        """
        scores = {k: 0 for k in PROFILE_KEYWORDS}
        total_hits = 0
        
        # Simple keyword matching
        words = set(re.findall(r'\w+', text))
        
        for profile, keywords in PROFILE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:  # check phrase in text logic
                    scores[profile] += 1
                    total_hits += 1
        
        if total_hits == 0:
            return None, 0.0
        
        # Find best match
        best_profile = max(scores, key=scores.get)
        best_score = scores[best_profile]
        
        # Calculate confidence
        # Heuristic: ratio of hits for this profile vs total hits, dampened by absolute count
        # If we have very few hits total, confidence should be lower even if all are for one profile
        if best_score == 0:
            return None, 0.0
            
        ratio = best_score / total_hits
        
        # Boost confidence if we have multiple indicators
        confidence = ratio
        if best_score > 2:
            confidence = min(1.0, confidence + 0.1)
        elif best_score == 1:
            confidence = min(1.0, confidence - 0.2)
            
        # Ensure non-negative
        confidence = max(0.0, confidence)
            
        return best_profile, round(confidence, 2)
