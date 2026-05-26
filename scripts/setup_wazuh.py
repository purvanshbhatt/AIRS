#!/usr/bin/env python3
"""
Initialize Wazuh Configuration in the database for the SOC Lab.
Usage:
    py scripts/setup_wazuh.py <org_id> <wazuh_host> <wazuh_api_key>
"""

import sys
import os
from sqlalchemy.orm import Session

# Add the project root to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import SessionLocal
from app.models.wazuh_config import WazuhConfig
from app.models.organization import Organization

def main():
    if len(sys.argv) < 4:
        print("Usage: py scripts/setup_wazuh.py <org_id> <wazuh_host> <wazuh_api_key>")
        sys.exit(1)

    org_id = sys.argv[1]
    wazuh_host = sys.argv[2]
    wazuh_api_key = sys.argv[3]
    
    db: Session = SessionLocal()
    
    try:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            print(f"Error: Organization with ID '{org_id}' not found in the database.")
            sys.exit(1)

        config = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
        if config:
            config.wazuh_host = wazuh_host
            config.wazuh_api_key = wazuh_api_key
            print(f"Updated existing Wazuh config for org {org_id}")
        else:
            config = WazuhConfig(
                org_id=org_id,
                wazuh_host=wazuh_host,
                wazuh_port=55000,
                wazuh_api_key=wazuh_api_key,
                verify_ssl=False
            )
            db.add(config)
            print(f"Created new Wazuh config for org {org_id}")
            
        db.commit()
        print("Done. SOC Lab integration configured in database.")
    except Exception as e:
        print(f"Failed to setup Wazuh config: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
