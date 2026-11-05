"""
Public Configuration API

Provides lightweight, unauthenticated public product configuration for multi-vertical
positioning (General Platform, Healthcare Vertical, Legal Vertical).

Exposes:
- GET /api/public/product-config
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Header, Request
from pydantic import BaseModel, Field

router = APIRouter()


class ProductConfigResponse(BaseModel):
    vertical_key: str = Field(..., description="Active vertical key: general | healthcare | legal")
    display_name: str = Field(..., description="Product display name for the vertical")
    industry_label: str = Field(..., description="Target industry label")
    headline: str = Field(..., description="Primary landing headline")
    core_question: str = Field(..., description="Core business readiness question")
    focus_areas: List[str] = Field(..., description="Domain focus and risk priority areas")
    demo_org_id: str = Field(..., description="Simulated demo organization ID")
    demo_org_name: str = Field(..., description="Simulated demo organization name")


VERTICAL_CONFIGS = {
    "general": {
        "vertical_key": "general",
        "display_name": "ResilAI",
        "industry_label": "Enterprise & Cloud",
        "headline": "ResilAI — AI Incident Readiness Platform",
        "core_question": "If a security or AI incident happens tomorrow, are you actually ready?",
        "focus_areas": [
            "Universal incident readiness",
            "Deterministic scoring & evidence pipeline",
            "SaaS & cloud reliability",
            "Identity & access control",
            "Executive impact translation",
            "Automated control verification",
        ],
        "demo_org_id": "demo-acme-technologies",
        "demo_org_name": "Acme Technologies",
    },
    "healthcare": {
        "vertical_key": "healthcare",
        "display_name": "ResilAI Healthcare",
        "industry_label": "Healthcare",
        "headline": "Incident readiness for healthcare organizations",
        "core_question": "If ransomware hits your clinic tomorrow morning, can you keep operating and prove you're ready?",
        "focus_areas": [
            "Ransomware resilience",
            "EHR clinical operations continuity",
            "Microsoft 365 & Entra ID protection",
            "Veeam immutable backup integrity",
            "Recovery readiness SLAs",
            "Executive board visibility",
        ],
        "demo_org_id": "demo-northstar-health",
        "demo_org_name": "Northstar Family Health",
    },
    "legal": {
        "vertical_key": "legal",
        "display_name": "ResilAI Legal",
        "industry_label": "Law Firms & Legal",
        "headline": "Incident readiness for law firms",
        "core_question": "If ransomware hits your firm tomorrow morning, can you keep operating and protect client data?",
        "focus_areas": [
            "Client data protection",
            "Privileged access & confidentiality",
            "Document vault & repository security",
            "Endpoint & partner laptop protection",
            "ABA & regulatory compliance",
            "MSP & vendor visibility",
        ],
        "demo_org_id": "demo-northstar-cole",
        "demo_org_name": "Northstar & Cole LLP",
    },
}


def resolve_vertical_key(
    query_param: Optional[str] = None,
    header_val: Optional[str] = None,
    host: Optional[str] = None,
) -> str:
    """Resolve vertical key with precedence: query param -> header -> host subdomain -> default."""
    if query_param:
        norm = query_param.strip().lower()
        if norm in VERTICAL_CONFIGS:
            return norm

    if header_val:
        norm = header_val.strip().lower()
        if norm in VERTICAL_CONFIGS:
            return norm

    if host:
        lower_host = host.split(":")[0].strip().lower()
        first_part = lower_host.split(".")[0]
        if first_part in VERTICAL_CONFIGS:
            return first_part
        if lower_host.startswith("healthcare-"):
            return "healthcare"
        if lower_host.startswith("legal-"):
            return "legal"
        if lower_host.startswith("general-"):
            return "general"

    return "general"


@router.get(
    "/product-config",
    response_model=ProductConfigResponse,
    summary="Get Public Product Configuration",
    description="Returns public multi-vertical configuration metadata based on query param, header, or subdomain.",
)
async def get_product_config(
    request: Request,
    vertical: Optional[str] = Query(None, description="Optional vertical key: general | healthcare | legal"),
    x_resilai_vertical: Optional[str] = Header(None, alias="X-ResilAI-Vertical", description="Optional vertical key header"),
) -> ProductConfigResponse:
    host = request.headers.get("host")
    resolved_key = resolve_vertical_key(
        query_param=vertical,
        header_val=x_resilai_vertical,
        host=host,
    )
    data = VERTICAL_CONFIGS.get(resolved_key, VERTICAL_CONFIGS["general"])
    return ProductConfigResponse(**data)
