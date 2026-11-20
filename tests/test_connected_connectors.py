"""
A connector that is delivering data must count as connected.

Two gaps made a report say "not monitored" / score 0 for a working AWS
connector:

* the AWS connector can be registered as type ``aws`` (not only
  ``aws_security_hub``), which the coverage map did not list;
* every sync flips the connector to ``syncing`` until it finishes, and only
  ``active`` connectors were counted, so a report generated during a sync saw
  no connector at all.
"""
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENV", "local")

from app.models.connector import Connector
from app.models.organization import Organization
from app.services.clinic_engine.v2.coverage_engine import CoverageEngine, connected_connectors
from app.services.clinic_engine.v2.readiness_engine import ReadinessEngine
from app.services.clinic_engine.v2.trust_engine import TrustEngine

ORG = "org-connected"
NOW = datetime.now(timezone.utc)


def _connector(db, connector_type="aws", status="active", last_sync_at=NOW, health="healthy"):
    if db.query(Organization).filter(Organization.id == ORG).first() is None:
        db.add(Organization(id=ORG, name="Connected Clinic", owner_uid="owner-1"))
    db.add(Connector(
        org_id=ORG, connector_type=connector_type, display_name=f"{connector_type} connector",
        status=status, health_status=health, last_sync_at=last_sync_at,
        auth_method="api_key", created_by="test",
    ))
    db.commit()


def _cloud_area(db):
    report = CoverageEngine(db).assess_coverage(ORG)
    return next((a for a in report.monitored if a.area == "Cloud Security"), None)


def test_aws_typed_connector_covers_cloud_security(db_session):
    _connector(db_session, connector_type="aws")
    area = _cloud_area(db_session)
    assert area is not None
    assert area.source == "Amazon Web Services"


def test_aws_security_hub_typed_connector_still_covers_cloud_security(db_session):
    _connector(db_session, connector_type="aws_security_hub")
    assert _cloud_area(db_session).source == "AWS Security Hub"


def test_connector_in_the_middle_of_a_sync_is_still_connected(db_session):
    _connector(db_session, status="syncing", last_sync_at=NOW - timedelta(minutes=30))

    assert len(connected_connectors(db_session, ORG)) == 1
    assert _cloud_area(db_session) is not None
    assert TrustEngine(db_session).build_overall_verification(ORG).confidence_pct > 0

    report = ReadinessEngine(db_session).evaluate(ORG, [])
    assert [c.name for c in report.connectors] == ["Amazon Web Services"]
    assert report.clinic_health_pct > 0


def test_connector_on_its_first_sync_has_delivered_nothing_yet(db_session):
    _connector(db_session, status="syncing", last_sync_at=None, health=None)

    assert connected_connectors(db_session, ORG) == []
    assert _cloud_area(db_session) is None
    assert TrustEngine(db_session).build_overall_verification(ORG).confidence_pct == 0


def test_failed_and_switched_off_connectors_are_not_connected(db_session):
    _connector(db_session, status="error", health="unreachable")
    _connector(db_session, connector_type="wazuh", status="inactive")

    assert connected_connectors(db_session, ORG) == []
    assert TrustEngine(db_session).build_overall_verification(ORG).confidence_pct == 0
