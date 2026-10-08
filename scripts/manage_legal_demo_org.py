#!/usr/bin/env python3
"""
Legal Demo Organization Management Utility.

Creates or completely deletes a curated fake legal organization with realistic
AWS Security Hub findings, IAM credential hygiene, and Backup telemetry.

Usage:
    python scripts/manage_legal_demo_org.py --create
    python scripts/manage_legal_demo_org.py --status
    python scripts/manage_legal_demo_org.py --delete
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import SessionLocal, Base, engine
import app.models  # Register models
from app.models.organization import Organization
from app.models.connector import Connector, ConnectorStatus
from app.models.telemetry_event import TelemetryEvent
from app.services.connector_manager import ConnectorManager
from app.services.demo.aws_demo_telemetry import get_aws_demo_telemetry

LEGAL_ORG_ID = "demo-northstar-cole"
LEGAL_ORG_NAME = "Northstar & Cole LLP"


def create_legal_demo_org() -> int:
    """Create the legal demo organization and populate curated AWS telemetry."""
    print("=" * 60)
    print("CREATING LEGAL DEMO ORGANIZATION")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Check or create Organization
        org = db.query(Organization).filter(Organization.id == LEGAL_ORG_ID).first()
        if not org:
            org = Organization(
                id=LEGAL_ORG_ID,
                name=LEGAL_ORG_NAME,
                industry="Law Firms & Legal",
                size="1-50",
                org_mode="demo",
                deployment_mode="sandbox",
                contact_name="Marcus Cole",
                contact_email="marcus.cole@northstarcole.com",
                owner_uid="demo-legal-partner",
                timezone="America/New_York",
                regulatory_profile="ABA Formal Opinion 477R, Rule 1.6(c)",
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"[+] Created Organization: {org.name} ({org.id})")
        else:
            print(f"[*] Organization already exists: {org.name} ({org.id})")

        # 2. Register AWS Security Hub Connector
        mgr = ConnectorManager(db, org.id)
        existing_conn = (
            db.query(Connector)
            .filter(Connector.org_id == org.id, Connector.connector_type == "aws_security_hub")
            .first()
        )
        if not existing_conn:
            conn = mgr.register_connector(
                connector_type="aws_security_hub",
                display_name="AWS Security Hub — Legal Cloud Infrastructure",
                auth_method="iam_role",
                credentials={"role_arn": "arn:aws:iam::505467908065:role/Legal-Audit-Admin", "aws_region": "us-east-1"},
                config={"region": "us-east-1", "vault": "northstar-cole-litigation-hold"},
                created_by="system-legal-demo",
            )
            conn.status = ConnectorStatus.active.value
            conn.health_status = "healthy"
            db.commit()
            print(f"[+] Registered AWS Connector: {conn.id}")
        else:
            print(f"[*] AWS Connector already registered: {existing_conn.id}")

        # 3. Ingest Curated Legal AWS Telemetry Events
        events = get_aws_demo_telemetry(org.id)
        ingested_count = 0
        for ev in events:
            # Check for duplicate event
            exists = (
                db.query(TelemetryEvent)
                .filter(
                    TelemetryEvent.org_id == org.id,
                    TelemetryEvent.source_event_id == ev.source_event_id,
                )
                .first()
            )
            if not exists:
                import hashlib
                payload_str = json.dumps(ev.payload, sort_keys=True)
                p_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
                rec = TelemetryEvent(
                    org_id=org.id,
                    connector_id=conn.id if 'conn' in locals() else None,
                    event_type=ev.event_type,
                    source_system=ev.source_system,
                    source_event_id=ev.source_event_id,
                    payload_hash=p_hash,
                    payload=ev.payload,
                    severity=ev.payload.get("severity", "medium"),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(rec)
                ingested_count += 1

        db.commit()
        print(f"[+] Ingested {ingested_count} curated legal AWS telemetry events:")
        print("    - AWS S3 Client Matter Bucket Block Public Access Disabled")
        print("    - AWS IAM Stale Credentials for External Litigation Counsel")
        print("    - AWS Backup PostgreSQL RDS Litigation Vault Snapshot")
        print("    - AWS Config Litigation Hold Resource Recording Verification")

        print("=" * 60)
        print("LEGAL DEMO READY: Accessible in frontend via ?vertical=legal")
        print("=" * 60)
        return 0

    except Exception as exc:
        print(f"[-] Error creating legal demo org: {exc}")
        db.rollback()
        return 1
    finally:
        db.close()


def status_legal_demo_org() -> int:
    """Check current status of the legal demo organization."""
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.id == LEGAL_ORG_ID).first()
        if not org:
            print(f"[x] Legal demo organization '{LEGAL_ORG_ID}' DOES NOT EXIST.")
            return 1

        conn_count = db.query(Connector).filter(Connector.org_id == org.id).count()
        telemetry_count = db.query(TelemetryEvent).filter(TelemetryEvent.org_id == org.id).count()

        print(f"[✓] Legal demo organization '{org.name}' ({org.id}) is ACTIVE:")
        print(f"    - Connectors: {conn_count}")
        print(f"    - Ingested Telemetry Events: {telemetry_count}")
        return 0
    finally:
        db.close()


def delete_legal_demo_org() -> int:
    """Delete the legal demo organization and all related telemetry without leaving traces."""
    print("=" * 60)
    print("DELETING LEGAL DEMO ORGANIZATION & ALL CURATED DATA")
    print("=" * 60)

    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.id == LEGAL_ORG_ID).first()
        if not org:
            print(f"[*] Organization '{LEGAL_ORG_ID}' already does not exist. Nothing to delete.")
            return 0

        # Delete Telemetry Events
        del_events = db.query(TelemetryEvent).filter(TelemetryEvent.org_id == org.id).delete()
        print(f"[x] Deleted {del_events} telemetry events.")

        # Delete Connectors
        del_conns = db.query(Connector).filter(Connector.org_id == org.id).delete()
        print(f"[x] Deleted {del_conns} connectors.")

        # Delete Organization
        db.delete(org)
        db.commit()
        print(f"[x] Deleted organization '{LEGAL_ORG_NAME}' ({LEGAL_ORG_ID}).")

        print("=" * 60)
        print("CLEANUP COMPLETE: All legal demo data has been purged.")
        print("=" * 60)
        return 0

    except Exception as exc:
        print(f"[-] Error deleting legal demo org: {exc}")
        db.rollback()
        return 1
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Manage Legal Demo Organization & AWS Telemetry")
    parser.add_argument("--create", action="store_true", help="Create and populate legal demo org")
    parser.add_argument("--status", action="store_true", help="Check status of legal demo org")
    parser.add_argument("--delete", action="store_true", help="Completely delete legal demo org and all data")

    args = parser.parse_args()

    if args.create:
        return create_legal_demo_org()
    elif args.delete:
        return delete_legal_demo_org()
    elif args.status:
        return status_legal_demo_org()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
