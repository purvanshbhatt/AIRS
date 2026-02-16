"""Demo data seeding for deterministic Public Beta experiences."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.assessment import AnswerInput, AssessmentCreate
from app.schemas.organization import OrganizationCreate
from app.services.assessment import AssessmentService
from app.services.integrations import IntegrationService
from app.services.organization import OrganizationService

_DEMO_ANSWERS = [
    ("tl_01", "true"),
    ("tl_02", "true"),
    ("tl_03", "true"),
    ("tl_04", "true"),
    ("tl_05", "90"),
    ("tl_06", "true"),
    ("dc_01", "80"),
    ("dc_02", "true"),
    ("dc_03", "true"),
    ("dc_04", "true"),
    ("dc_05", "true"),
    ("dc_06", "true"),
    ("iv_01", "true"),
    ("iv_02", "true"),
    ("iv_03", "true"),
    ("iv_04", "true"),
    ("iv_05", "true"),
    ("iv_06", "true"),
    ("ir_01", "true"),
    ("ir_02", "true"),
    ("ir_03", "true"),
    ("ir_04", "true"),
    ("ir_05", "true"),
    ("ir_06", "true"),
    ("rs_01", "true"),
    ("rs_02", "true"),
    ("rs_03", "true"),
    ("rs_04", "true"),
    ("rs_05", "4"),
    ("rs_06", "true"),
]


def ensure_demo_seed_data(db: Session, owner_uid: Optional[str]) -> None:
    """
    Ensure every demo user can immediately see a populated organization + assessment.

    This is idempotent and only runs when DEMO_MODE=true.
    """
    if not settings.is_demo_mode:
        return

    org_service = OrganizationService(db, owner_uid=owner_uid)
    orgs = org_service.get_all(skip=0, limit=1)
    if orgs:
        org = orgs[0]
    else:
        org = org_service.create(
            OrganizationCreate(
                name="Acme Health Systems",
                industry="Healthcare",
                size="201-1000",
                contact_name="Security Operations",
                contact_email="security@acmehealth.example",
            )
        )

    integration_service = IntegrationService(db, owner_uid=owner_uid)
    existing_findings = integration_service.list_external_findings(source="splunk", limit=1, org_id=org.id)
    if not existing_findings:
        integration_service.seed_mock_splunk_findings(org_id=org.id)

    assessment_service = AssessmentService(db, owner_uid=owner_uid)
    existing_assessments = assessment_service.get_all(organization_id=org.id, skip=0, limit=1)
    if existing_assessments:
        return

    assessment = assessment_service.create(
        AssessmentCreate(
            organization_id=org.id,
            title="Public Beta Executive Readiness Assessment",
            version="1.0.0",
        )
    )
    assessment_service.submit_answers(
        assessment.id,
        [AnswerInput(question_id=qid, value=value) for qid, value in _DEMO_ANSWERS],
    )
    assessment_service.compute_score(assessment.id)
