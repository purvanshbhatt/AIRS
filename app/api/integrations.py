"""Integration endpoints (API keys + webhooks)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.db.database import get_db
from app.schemas.integrations import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyMetadataResponse,
    WebhookCreateRequest,
    WebhookResponse,
    WebhookTestResponse,
    SplunkSeedRequest,
    SplunkSeedResponse,
    ExternalFindingResponse,
    WebhookUrlTestRequest,
    WebhookUrlTestResponse,
)
from app.services.integrations import (
    EVENT_ASSESSMENT_SCORED,
    IntegrationService,
    deliver_webhook,
    deliver_webhook_url_test,
)
from app.services.audit import record_audit_event

router = APIRouter()


@router.post("/orgs/{org_id}/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    org_id: str,
    data: ApiKeyCreateRequest = ApiKeyCreateRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        result = service.create_api_key(org_id, scopes=data.scopes)
        record_audit_event(
            db=db,
            org_id=org_id,
            action="api_key.created",
            actor=user.uid,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/orgs/{org_id}/api-keys", response_model=list[ApiKeyMetadataResponse])
async def list_api_keys(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        return service.list_api_keys(org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    if not service.deactivate_api_key(key_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")


@router.post("/orgs/{org_id}/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    org_id: str,
    data: WebhookCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        return service.create_webhook(
            org_id=org_id,
            url=str(data.url),
            event_types=data.event_types,
            secret=data.secret,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/orgs/{org_id}/webhooks", response_model=list[WebhookResponse])
async def list_webhooks(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        return service.list_webhooks(org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    if not service.delete_webhook(webhook_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    webhook = service.get_webhook_for_owner(webhook_id)
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    payload = {
        "event_type": EVENT_ASSESSMENT_SCORED,
        "org_id": webhook.org_id,
        "assessment_id": "test-assessment",
        "score": 75.0,
        "critical_findings": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test": True,
    }
    delivered, status_code, error = deliver_webhook(webhook, EVENT_ASSESSMENT_SCORED, payload)
    record_audit_event(
        db=db,
        org_id=webhook.org_id,
        action="webhook.triggered.manual_test",
        actor=user.uid,
    )
    return {
        "webhook_id": webhook_id,
        "delivered": delivered,
        "status_code": status_code,
        "error": error,
    }


@router.post("/integrations/mock/splunk-seed", response_model=SplunkSeedResponse)
async def seed_mock_splunk_findings(
    data: SplunkSeedRequest = SplunkSeedRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        return service.seed_mock_splunk_findings(org_id=data.org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/integrations/external-findings", response_model=list[ExternalFindingResponse])
async def list_external_findings(
    source: str = Query(default="splunk"),
    limit: int = Query(default=50, ge=1, le=200),
    org_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        findings = service.list_external_findings(source=source, limit=limit, org_id=org_id)
        return findings
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/integrations/webhooks/test", response_model=WebhookUrlTestResponse)
async def test_webhook_url(
    data: WebhookUrlTestRequest,
    user: User = Depends(require_auth),
):
    payload = {
        "event_type": data.event_type,
        "org_id": f"user:{user.uid}",
        "assessment_id": "test-assessment",
        "score": 78.0,
        "critical_findings": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test": True,
    }
    delivered, status_code, error = deliver_webhook_url_test(
        url=str(data.url),
        event_type=data.event_type,
        payload=payload,
        secret=data.secret,
    )
    return {
        "delivered": delivered,
        "status_code": status_code,
        "error": error,
        "event_type": data.event_type,
        "payload": payload,
    }
