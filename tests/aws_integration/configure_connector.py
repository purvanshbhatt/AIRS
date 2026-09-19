#!/usr/bin/env python3
"""
Configure and test AWS Security Hub connector for ResilAI.
Reads credentials from environment variables and registers/syncs the connector.

Usage:
    AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_REGION=us-east-1 python tests/aws_integration/configure_connector.py

Product Invariants:
    - NEVER prints or logs AWS credentials, keys, or secrets.
    - Deterministic execution only.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import SessionLocal, Base, engine
import app.models  # Register all models with SQLAlchemy
from app.models.organization import Organization
from app.models.connector import Connector, ConnectorStatus
from app.services.connector_manager import ConnectorManager
from app.connectors.aws_security_hub import AWSSecurityHubConnector


def main() -> int:
    """Configure, validate, and test AWS Security Hub connector."""
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    session_token = os.environ.get("AWS_SESSION_TOKEN")
    region = os.environ.get("AWS_REGION", "us-east-1")
    role_arn = os.environ.get("AWS_ROLE_ARN")
    target_org_id = os.environ.get("ORG_ID")

    if not (access_key and secret_key):
        try:
            import boto3
            boto_session = boto3.Session(region_name=region)
            creds = boto_session.get_credentials()
            if creds:
                frozen = creds.get_frozen_credentials()
                access_key = frozen.access_key
                secret_key = frozen.secret_key
                session_token = frozen.token
        except Exception as e:
            pass

    if not access_key or not secret_key:
        print("ERROR: Missing AWS credentials in environment or AWS profile.")
        print("Required:")
        print("  - Active AWS CLI session or AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY")
        return 1

    print("==================================================")
    print("ResilAI AWS Security Hub Connector Configuration")
    print("==================================================")
    print(f"Target Region : {region}")
    print(f"Role ARN      : {role_arn if role_arn else '(direct credentials)'}")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Resolve or create test organization
        if target_org_id:
            org = db.query(Organization).filter(Organization.id == target_org_id).first()
            if not org:
                print(f"ERROR: Organization '{target_org_id}' not found.")
                return 1
        else:
            org_id_slug = "resilai-aws-validation-org"
            org = db.query(Organization).filter(Organization.id == org_id_slug).first()
            if not org:
                org = Organization(
                    id=org_id_slug,
                    name="ResilAI AWS Validation Organization",
                    owner_uid="system-aws-validation",
                )
                db.add(org)
                db.commit()
                db.refresh(org)
                print(f"Created validation organization: {org.id}")
            else:
                print(f"Using existing organization: {org.id}")

        manager = ConnectorManager(db, org.id)

        # 2. Build credentials dict (NEVER printed)
        credentials = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "aws_region": region,
        }
        if session_token:
            credentials["aws_session_token"] = session_token
        if role_arn:
            credentials["role_arn"] = role_arn

        # 3. Check for existing AWS Security Hub connector
        existing_connector = (
            db.query(Connector)
            .filter(
                Connector.org_id == org.id,
                Connector.connector_type == "aws_security_hub",
            )
            .first()
        )

        if existing_connector:
            print(f"Updating credentials for existing connector: {existing_connector.id}")
            existing_connector.encrypted_credentials = manager._encrypt_credentials(credentials)
            existing_connector.auth_method = "iam_role" if role_arn else "api_key"
            existing_connector.status = ConnectorStatus.pending_auth.value
            db.commit()
            db.refresh(existing_connector)
            connector = existing_connector
        else:
            print("Registering new AWS Security Hub connector...")
            connector = manager.register_connector(
                connector_type="aws_security_hub",
                display_name=f"AWS Security Hub ({region})",
                auth_method="iam_role" if role_arn else "api_key",
                credentials=credentials,
                config={"region": region},
                created_by="system-aws-validation",
            )
            print(f"Registered connector ID: {connector.id}")

        # 4. Instantiate and validate permissions
        print("\nValidating AWS credentials & permissions...")
        conn_impl = AWSSecurityHubConnector(
            connector_id=connector.id,
            org_id=org.id,
            credentials=credentials,
            config={"region": region},
        )

        auth_success = asyncio.run(conn_impl.authenticate())
        if not auth_success:
            print("FAILURE: Authentication to AWS Security Hub failed.")
            connector.status = ConnectorStatus.error.value
            connector.health_status = "unreachable"
            db.commit()
            return 1

        print("SUCCESS: Authenticated to AWS Security Hub.")

        perm_result = asyncio.run(conn_impl.validate_permissions())
        if not perm_result.valid:
            print(f"WARNING: Permission validation incomplete: {perm_result.message}")
            if perm_result.missing_permissions:
                print(f"Missing permissions: {perm_result.missing_permissions}")
        else:
            print("SUCCESS: All required AWS permissions verified.")

        # 5. Run sync
        print("\nTriggering initial connector sync...")
        sync_result = asyncio.run(manager.sync_connector(connector.id))

        print("\n--- Sync Results ---")
        print(f"Success         : {sync_result.success}")
        print(f"Events Ingested : {sync_result.events_ingested}")
        print(f"Duration        : {sync_result.duration_ms:.2f} ms")
        if sync_result.error_details:
            print(f"Error Details   : {sync_result.error_details}")

        if sync_result.success:
            print("\n==================================================")
            print("AWS Security Hub Connector Validation COMPLETE (OK)")
            print("==================================================")
            return 0
        else:
            print("\n==================================================")
            print("AWS Security Hub Connector Sync FAILED")
            print("==================================================")
            return 1

    except Exception as exc:
        print(f"\nERROR: Unexpected failure during configuration: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
