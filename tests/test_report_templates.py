"""
Template report tests: every template in the Reports page must produce a
real, server-generated, downloadable document with numbers taken from the
readiness snapshot (never fabricated client-side).
"""
import io
import json
import os
from unittest.mock import patch

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENV", "local")

from app.models.organization import Organization
from app.models.report import Report
from app.reports.templates import TEMPLATE_IDS

ORG_ID = "test-org-123"  # provisioned by the client_with_org fixture
GENERATE = "/api/v1/reports/generate"

TEMPLATES = [
    "board_story",
    "monthly_ops",
    "hipaa_audit",
    "technical_telemetry",
    "executive_pdf",
    "boss_report",
    "cyber_insurance",
    "msp_summary",
]


def _pdf_page_count(data: bytes) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(io.BytesIO(data)).pages)
    except ImportError:  # pragma: no cover
        return data.count(b"/Type /Page") - data.count(b"/Type /Pages")


@pytest.fixture
def entitled():
    """test-org-123 has no subscription; grant EXECUTIVE_REPORTS for the test."""
    with patch("app.core.entitlements.EntitlementService.has", return_value=True):
        yield


def _generate(client, report_type, fmt="pdf", title=None, org_id=ORG_ID):
    payload = {"organization_id": org_id, "org_id": org_id, "report_type": report_type, "format": fmt}
    if title:
        payload["title"] = title
    return client.post(GENERATE, json=payload)


def test_template_registry_matches_frontend_cards():
    assert set(TEMPLATES) == set(TEMPLATE_IDS)


@pytest.mark.parametrize("report_type", TEMPLATES)
def test_generate_each_template_persists_report_and_downloads_pdf(db_session, client_with_org, entitled, report_type):
    resp = _generate(client_with_org, report_type)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["report_type"] == report_type
    assert body["format"] == "pdf"
    assert body["status"] == "completed"
    assert body["organization_id"] == ORG_ID
    assert body["persisted"] is True
    # Numbers come from the server snapshot: a fresh org with no telemetry is honest about it.
    assert body["overall_score"] == 0
    assert body["findings_count"] == 0

    row = db_session.query(Report).filter(Report.id == body["id"]).first()
    assert row is not None
    assert row.assessment_id is None
    assert row.report_type == report_type
    assert row.format == "pdf"
    snapshot = json.loads(row.snapshot)
    assert snapshot["template"] == report_type
    assert snapshot["readiness"]["status"] == "unknown"
    assert snapshot["data_source"] == "persisted_telemetry"
    assert len(snapshot["evidence_hash"]) == 64

    dl = client_with_org.get(f"/api/reports/{body['id']}/download")
    assert dl.status_code == 200, dl.text
    assert dl.headers["content-type"].startswith("application/pdf")
    assert dl.content.startswith(b"%PDF")
    assert _pdf_page_count(dl.content) >= 1


def test_boss_report_is_exactly_one_page(db_session, client_with_org, entitled):
    resp = _generate(client_with_org, "boss_report", title="Monday Boss Report")
    assert resp.status_code == 201, resp.text
    dl = client_with_org.get(f"/api/reports/{resp.json()['id']}/download")
    assert dl.status_code == 200
    assert dl.content.startswith(b"%PDF")
    assert _pdf_page_count(dl.content) == 1


def test_boss_report_one_page_with_demo_telemetry(db_session, client_with_org, entitled):
    """Demo telemetry produces many findings; the boss report must still fit one page."""
    db_session.add(Organization(id="demo-boss-clinic", name="Demo Boss Clinic", owner_uid="someone-else", org_mode="demo"))
    db_session.commit()
    resp = _generate(client_with_org, "boss_report", org_id="demo-boss-clinic")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["findings_count"] > 0
    dl = client_with_org.get(f"/api/reports/{body['id']}/download")
    assert dl.status_code == 200
    assert _pdf_page_count(dl.content) == 1


def test_unknown_template_is_422(db_session, client_with_org, entitled):
    resp = _generate(client_with_org, "quarterly_vibes")
    assert resp.status_code == 422


def test_missing_org_is_422(db_session, client_with_org, entitled):
    resp = client_with_org.post(GENERATE, json={"report_type": "board_story"})
    assert resp.status_code == 422


def test_generate_requires_entitlement(db_session, client_with_org):
    resp = _generate(client_with_org, "board_story")
    assert resp.status_code == 402


def test_other_users_org_is_404(db_session, client_with_org, entitled):
    db_session.add(Organization(id="someone-elses-org", name="Other", owner_uid="user-b"))
    db_session.commit()
    resp = _generate(client_with_org, "board_story", org_id="someone-elses-org")
    assert resp.status_code == 404


def test_json_and_csv_formats(db_session, client_with_org, entitled):
    r_json = _generate(client_with_org, "technical_telemetry", fmt="json")
    assert r_json.status_code == 201, r_json.text
    dl = client_with_org.get(f"/api/reports/{r_json.json()['id']}/download")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("application/json")
    data = dl.json()
    assert data["template"] == "technical_telemetry"
    assert "readiness" in data and "connectors" in data

    r_csv = _generate(client_with_org, "monthly_ops", fmt="csv")
    assert r_csv.status_code == 201, r_csv.text
    dl = client_with_org.get(f"/api/reports/{r_csv.json()['id']}/download")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("text/csv")
    text = dl.content.decode("utf-8")
    assert "severity,label,detail,category,owner" in text
    assert "# overall_score" in text


def test_report_list_includes_template_reports(db_session, client_with_org, entitled):
    resp = _generate(client_with_org, "msp_summary", title="MSP hand-off")
    assert resp.status_code == 201
    lst = client_with_org.get(f"/api/reports?organization_id={ORG_ID}")
    assert lst.status_code == 200
    items = lst.json()["reports"]
    assert any(r["id"] == resp.json()["id"] and r["report_type"] == "msp_summary" and r["format"] == "pdf" for r in items)
    assert all(r["assessment_id"] is None for r in items if r["report_type"] == "msp_summary")


def test_unseeded_demo_org_returns_stateless_download(db_session, client_with_org):
    """Demo ids are readable without a subscription; without a DB row nothing is persisted."""
    resp = _generate(client_with_org, "board_story", org_id="demo-northstar-health")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["persisted"] is False
    assert body["findings_count"] > 0  # demo telemetry
    assert body["download_url"].startswith("/api/v1/reports/render?")
    dl = client_with_org.get(body["download_url"])
    assert dl.status_code == 200
    assert dl.content.startswith(b"%PDF")
    assert db_session.query(Report).count() == 0


def test_render_endpoint_requires_ownership_for_real_orgs(db_session, client_with_org):
    db_session.add(Organization(id="someone-elses-org", name="Other", owner_uid="user-b"))
    db_session.commit()
    resp = client_with_org.get("/api/v1/reports/render?org_id=someone-elses-org&report_type=boss_report")
    assert resp.status_code in (401, 404)
