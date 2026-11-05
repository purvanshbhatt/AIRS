"""
Deterministic regulatory and configuration engine.
Maps organization profiles (country, industry, size) to regulatory frameworks.
"""
import json
from typing import List

# Extensible configuration for regulatory applicability
_REGULATORY_RULES = [
    {
        "country": "US",
        "industry": "Healthcare",
        "frameworks": ["HIPAA", "HITECH", "NIST CSF 2.0"]
    },
    {
        "country": "India",
        "industry": "Healthcare",
        "frameworks": ["DISHA", "DPDPA", "NIST CSF 2.0"]
    },
    {
        "country": "US",
        "industry": "Finance",
        "frameworks": ["GLBA", "NYDFS", "PCI-DSS", "NIST CSF 2.0"]
    },
    {
        "country": "India",
        "industry": "Finance",
        "frameworks": ["RBI Guidelines", "DPDPA", "PCI-DSS", "NIST CSF 2.0"]
    },
    {
        "country": "US",
        "industry": "SMB",
        "frameworks": ["NIST CSF 2.0 (Baseline)"]
    },
    {
        "country": "India",
        "industry": "SMB",
        "frameworks": ["CERT-In Guidelines (Baseline)"]
    },
    {
        "country": "Any",
        "industry": "Any",
        "frameworks": ["NIST CSF 2.0 (Baseline)"]
    }
]

def determine_regulatory_profile(country: str | None, industry: str | None, size: str | None = None) -> str:
    """
    Deterministically computes the applicable regulatory frameworks.
    Returns a JSON-encoded string of the list of frameworks.
    """
    country_norm = (country or "US").strip().upper()
    industry_norm = (industry or "SMB").strip().title()

    # Special handling for common aliases
    if country_norm in ["USA", "UNITED STATES", "U.S.", "US"]:
        country_norm = "US"
    elif country_norm in ["IN", "INDIA"]:
        country_norm = "India"
    
    if not industry_norm:
        industry_norm = "SMB"

    applicable_frameworks = []
    
    # Check for specific matches first
    for rule in _REGULATORY_RULES:
        if rule["country"] != "Any" and rule["country"].upper() == country_norm:
            if rule["industry"].upper() == industry_norm.upper():
                applicable_frameworks = rule["frameworks"]
                break

    # If no specific match, try country default or generic fallback
    if not applicable_frameworks:
        for rule in _REGULATORY_RULES:
            if rule["country"].upper() == country_norm and rule["industry"] == "SMB":
                applicable_frameworks = rule["frameworks"]
                break
                
    if not applicable_frameworks:
        applicable_frameworks = ["NIST CSF 2.0 (Baseline)"]
        
    return json.dumps(applicable_frameworks)
