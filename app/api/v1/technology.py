from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import require_auth
from app.schemas.technology import TechInventoryItem, TechLifecycleAnalysis, TechExposureItem
from app.services.technology_intelligence import TechnologyIntelligenceOrchestrator
from app.services.governance.lifecycle_analysis import LifecycleAnalysisService
from app.models.tech_stack import TechStackItem
from app.services.cve.cve_enrichment import CVEEnrichmentService

router = APIRouter(prefix="/technology", tags=["Technology Intelligence"])

@router.get("/inventory/{org_id}", response_model=List[TechInventoryItem])
async def get_technology_inventory(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """
    Returns the enriched technology inventory for a given organization,
    including lifecycle and vulnerability signals.
    """
    # In a real app we would verify the user has access to org_id here
    # 404 handled if no org/empty, but for now we just return orchestrator results
    orchestrator = TechnologyIntelligenceOrchestrator(db, org_id)
    inventory = await orchestrator.get_technology_inventory()
    return inventory

@router.get("/lifecycle/{org_id}", response_model=List[TechLifecycleAnalysis])
async def get_technology_lifecycle(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """
    Returns detailed lifecycle analysis for all tech stack items in the org.
    """
    items = db.query(TechStackItem).filter(TechStackItem.org_id == org_id).all()
    
    lifecycle_service = LifecycleAnalysisService(db)
    
    results = []
    for item in items:
        if not item.version:
            continue
            
        analysis = lifecycle_service.analyze_lifecycle(item.component_name, item.version)
        results.append({
            "component_name": item.component_name,
            "version": item.version,
            "status": analysis.get("status", "Unknown"),
            "latest_supported": analysis.get("latest_supported"),
            "eol_date": analysis.get("eol_date"),
            "message": analysis.get("message", "")
        })
        
    return results

@router.get("/exposure/{org_id}", response_model=List[TechExposureItem])
async def get_technology_exposure(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """
    Returns a flattened list of all exposures (vulnerabilities) linked to the tech stack.
    """
    items = db.query(TechStackItem).filter(TechStackItem.org_id == org_id).all()
    cve_service = CVEEnrichmentService(db, org_id)
    
    inventory_items = []
    for item in items:
        inventory_items.append({
            "vendor": "",
            "product": item.component_name,
            "version": item.version
        })
        
    enriched_results = await cve_service.bulk_enrich(inventory_items)
    
    exposures = []
    for i, item in enumerate(items):
        enrichment = enriched_results[i]
        for vuln in enrichment.vulnerabilities:
            exposures.append({
                "cve_id": vuln.cve_id,
                "component_name": item.component_name,
                "version": item.version,
                "severity": vuln.severity,
                "is_kev": vuln.is_kev
            })
            
    return exposures


# =============================================================================
# Technology stack + vulnerability intelligence
#
#   GET    /technology/stack/{org_id}                         unified stack, CVEs, end of life
#   POST   /technology/stack/{org_id}/refresh                 discovery + intelligence refresh
#   GET    /technology/advisories/{org_id}                    advisories + top actions
#   GET    /technology/web-assets/{org_id}                    registered websites
#   POST   /technology/web-assets/{org_id}                    register a website
#   DELETE /technology/web-assets/{org_id}/{asset_id}
#   POST   /technology/web-assets/{org_id}/{asset_id}/scan    passive scan of a registered website
#   GET    /technology/deployments/{org_id}                   what is deployed in AWS
#
# Demo organizations (``demo-*`` or org_mode demo) are readable without a
# token, like the readiness and network endpoints. Real organizations require
# the signed-in owner. These results are informational: they do not feed the
# deterministic readiness score.
# =============================================================================

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Query, Request, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.core.auth import User, get_optional_user
from app.core.config import settings
from app.core.demo_guard import require_writable
from app.core.entitlements import require_entitlement
from app.models.vuln_intel import WebAsset
from app.services.billing.entitlements import Entitlement
from app.services.discovery.discovery import is_demo_org
from app.services.vuln_intel.service import (
    IntelClients,
    advisories_payload,
    refresh_org,
    run_intel,
    stack_payload,
)
from app.services.vuln_intel.web_scanner import UrlNotAllowed, WebScanner, normalize_url, sync_web_detections

logger = logging.getLogger("airs.api.technology")

MAX_WEB_ASSETS_PER_ORG = 25
SCAN_COOLDOWN_SECONDS = 15
DEPLOYMENTS_CACHE_MINUTES = 10

_readiness_guard = require_entitlement(Entitlement.READINESS_SCORING)


def get_intel_clients() -> IntelClients:
    """Public-feed clients (overridden in tests with a mocked transport)."""
    return IntelClients.default()


def get_web_scanner() -> WebScanner:
    """Website scanner (overridden in tests with a fake resolver / fetcher)."""
    return WebScanner()


def _authorize(db: Session, org_id: str, user: Optional[User], require_org: bool = False) -> bool:
    """Authorize the request for ``org_id``. Returns True when it is a demo organization.

    ``require_org`` (write routes): the organization row must exist even when
    authentication is switched off for local development.
    """
    org_id = (org_id or "").strip()
    if not org_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization ID is required.")
    demo = is_demo_org(db, org_id)
    if demo:
        return True
    if settings.is_auth_required and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if user is not None:
        from app.services.organization import OrganizationService
        try:
            org = OrganizationService(db, owner_uid=user.uid).get(org_id)
        except Exception as exc:
            logger.error("Organization access check failed for user=%s org=%s: %s", user.uid, org_id, exc)
            org = None
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ORGANIZATION_NOT_FOUND",
                    "message": f"Organization '{org_id}' not found or access not authorized.",
                    "organization_id": org_id,
                },
            )
    elif require_org:
        from app.models.organization import Organization
        if db.query(Organization).filter(Organization.id == org_id).first() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ORGANIZATION_NOT_FOUND",
                        "message": f"Organization '{org_id}' not found.", "organization_id": org_id},
            )
    return False


def _demo_read_only() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "DEMO_READ_ONLY", "message": "The demo workspace is read-only. Sign in to add your own."},
    )


def _web_asset_payload(row: WebAsset) -> dict:
    last_scan = None
    if row.last_scan:
        try:
            last_scan = json.loads(row.last_scan)
        except (TypeError, ValueError):
            last_scan = None
    return {"id": row.id, "url": row.url, "label": row.label, "last_scan": last_scan}


@router.get(
    "/stack/{org_id}",
    summary="Technology stack with vulnerabilities and end-of-life status",
    description=(
        "Software and versions found on the organization's servers, devices, websites and manual "
        "entries, matched against OSV, NVD, CISA KEV and endoflife.date (cached 24 h). "
        "Never synthetic for real organizations; `coverage` says what was not checked."
    ),
)
async def get_technology_stack(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    clients: IntelClients = Depends(get_intel_clients),
):
    demo = _authorize(db, org_id, user)
    result, inv_sources = await run_in_threadpool(
        run_intel, db, org_id, demo, clients=clients, budget_seconds=8.0,
    )
    return stack_payload(result, inv_sources, demo)


@router.post(
    "/stack/{org_id}/refresh",
    summary="Re-run discovery and the vulnerability lookup",
    description="Runs the discovery orchestrator (real organizations with a connector) and refreshes "
                "the intelligence for the resulting inventory. Bounded to about ten seconds of lookups; "
                "the rest is queued for the next refresh.",
)
async def refresh_technology_stack(
    request: Request,
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    clients: IntelClients = Depends(get_intel_clients),
):
    demo = _authorize(db, org_id, user)
    if not demo:
        require_writable()
        await _readiness_guard(request, user, db)
    return await run_in_threadpool(refresh_org, db, org_id, demo, clients=clients)


@router.get(
    "/advisories/{org_id}",
    summary="Vulnerability and end-of-life advisories with fix steps",
    description="One advisory per vulnerability or end-of-life release, sorted known-exploited first, "
                "then severity, then newest. `top_actions` lists at most five confirmed things to do now.",
)
async def get_technology_advisories(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    clients: IntelClients = Depends(get_intel_clients),
):
    demo = _authorize(db, org_id, user)
    result, inv_sources = await run_in_threadpool(
        run_intel, db, org_id, demo, clients=clients, budget_seconds=8.0,
    )
    return advisories_payload(result, inv_sources, demo)


class WebAssetCreate(BaseModel):
    url: str = Field(..., min_length=3, max_length=2048, description="http(s) address of the website")
    label: Optional[str] = Field(None, max_length=255)


@router.get("/web-assets/{org_id}", summary="Websites registered for passive checks")
async def list_web_assets(
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    demo = _authorize(db, org_id, user)
    if demo:
        from app.services.demo.demo_stack import demo_web_assets
        return {"assets": demo_web_assets(org_id), "demo": True}
    rows = db.query(WebAsset).filter(WebAsset.org_id == org_id).order_by(WebAsset.created_at.asc()).all()
    return {"assets": [_web_asset_payload(r) for r in rows], "demo": False}


@router.post("/web-assets/{org_id}", status_code=status.HTTP_201_CREATED, summary="Register a website")
async def create_web_asset(
    body: WebAssetCreate,
    org_id: str = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    if _authorize(db, org_id, user, require_org=True):
        raise _demo_read_only()
    require_writable()
    try:
        url = normalize_url(body.url)
    except UrlNotAllowed as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"code": "URL_NOT_ALLOWED", "message": str(exc)})
    existing = db.query(WebAsset).filter(WebAsset.org_id == org_id).all()
    for row in existing:
        if row.url == url:
            return _web_asset_payload(row)
    if len(existing) >= MAX_WEB_ASSETS_PER_ORG:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"code": "TOO_MANY_WEB_ASSETS",
                                    "message": f"At most {MAX_WEB_ASSETS_PER_ORG} websites per organization."})
    row = WebAsset(org_id=org_id, url=url, label=(body.label or "").strip() or None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _web_asset_payload(row)


@router.delete("/web-assets/{org_id}/{asset_id}", summary="Remove a registered website")
async def delete_web_asset(
    org_id: str = Path(..., description="Organization ID"),
    asset_id: str = Path(..., description="Web asset ID"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    if _authorize(db, org_id, user, require_org=True):
        raise _demo_read_only()
    require_writable()
    row = db.query(WebAsset).filter(WebAsset.id == asset_id, WebAsset.org_id == org_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "WEB_ASSET_NOT_FOUND", "message": "Website not found."})
    db.delete(row)
    db.commit()
    sync_web_detections(db, org_id)
    return {"deleted": True, "id": asset_id}


@router.post(
    "/web-assets/{org_id}/{asset_id}/scan",
    summary="Passive scan of a registered website",
    description="One ordinary page request to a website the organization registered itself: status, TLS "
                "certificate, security headers and software versions the site announces. Private, loopback, "
                "link-local and metadata addresses are refused, also after redirects.",
)
async def scan_web_asset(
    org_id: str = Path(..., description="Organization ID"),
    asset_id: str = Path(..., description="Web asset ID"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    scanner: WebScanner = Depends(get_web_scanner),
):
    if _authorize(db, org_id, user):
        from app.services.demo.demo_stack import demo_web_assets
        sample = next((a for a in demo_web_assets(org_id) if a["id"] == asset_id), None)
        if sample is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail={"code": "WEB_ASSET_NOT_FOUND", "message": "Website not found."})
        return sample["last_scan"]

    require_writable()
    # Only a URL this organization added itself is ever fetched.
    row = db.query(WebAsset).filter(WebAsset.id == asset_id, WebAsset.org_id == org_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={"code": "WEB_ASSET_NOT_FOUND", "message": "Website not found."})

    now = datetime.now(timezone.utc)
    if row.last_scan and row.last_scan_at:
        last = row.last_scan_at if row.last_scan_at.tzinfo else row.last_scan_at.replace(tzinfo=timezone.utc)
        if (now - last).total_seconds() < SCAN_COOLDOWN_SECONDS:
            return json.loads(row.last_scan)

    try:
        result = await run_in_threadpool(scanner.scan, row.url)
    except UrlNotAllowed as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={"code": "URL_NOT_ALLOWED", "message": str(exc)})
    row.last_scan = json.dumps(result)
    row.last_scan_at = now
    db.commit()
    try:
        sync_web_detections(db, org_id)
    except Exception as exc:
        db.rollback()
        logger.warning("Web detection sync failed for org %s: %s", org_id, exc)
    return result


@router.get(
    "/deployments/{org_id}",
    summary="Cloud deployments in the connected AWS account",
    description="Lambda functions, RDS instances, EC2, load balancers, CloudFront, API Gateway, S3 websites, "
                "ECS services, App Runner and Elastic Beanstalk, read through the organization's AWS "
                "connector. Empty with `sources.aws = not_connected` when no connector exists.",
)
async def get_cloud_deployments(
    org_id: str = Path(..., description="Organization ID"),
    refresh: bool = Query(False, description="Bypass the 10-minute cache"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
    clients: IntelClients = Depends(get_intel_clients),
):
    from app.services.vuln_intel.cache import IntelCache
    from app.services.vuln_intel.cloud_deployments import (
        CloudDeploymentCollector,
        demo_deployments,
        lambda_runtime_cycles,
    )

    demo = _authorize(db, org_id, user)

    def _collect() -> dict:
        if demo:
            payload = demo_deployments(org_id, lambda_runtime_cycles(db, clients))
            payload["demo"] = True
            return payload
        cache = IntelCache(db)
        key = f"deployments:{org_id}"
        now = datetime.now(timezone.utc)
        entry = cache.get(key)
        if entry is not None and not refresh and entry.is_fresh(now):
            return entry.payload
        payload = CloudDeploymentCollector(
            db, org_id, lambda_cycles=lambda: lambda_runtime_cycles(db, clients),
        ).collect()
        payload["demo"] = False
        if payload["sources"].get("aws") not in ("not_connected", "error", "auth_failed"):
            cache.set(key, "deployments", payload, now=now, ttl=timedelta(minutes=DEPLOYMENTS_CACHE_MINUTES))
        return payload

    return await run_in_threadpool(_collect)
