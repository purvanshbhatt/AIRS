"""
Test script for Technology Stack Discovery Automation
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.organization import Organization
from app.services.discovery.orchestrator import TechnologyDiscoveryOrchestrator
from app.models.discovery import TechnologyInventory, HostAsset, InstalledProduct

def test_discovery():
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        if not org:
            print("No organization found. Create an org first.")
            return

        print(f"Running discovery for org: {org.name} ({org.id})")
        
        # Clean up any previous inventory to force a fresh run for testing
        db.query(TechnologyInventory).filter(TechnologyInventory.org_id == org.id).delete()
        db.commit()

        orchestrator = TechnologyDiscoveryOrchestrator(db, org.id)
        inventory = orchestrator.run_discovery_cycle()
        
        print(f"\n--- Discovery Complete ---")
        print(f"Inventory ID: {inventory.id}")
        
        assets = db.query(HostAsset).filter(HostAsset.inventory_id == inventory.id).all()
        print(f"\nDiscovered Assets: {len(assets)}")
        for a in assets:
            print(f"  - {a.hostname} [{a.asset_type.value}] IP: {a.ip_address} OS: {a.operating_system}")
            
            products = db.query(InstalledProduct).filter(InstalledProduct.asset_id == a.id).all()
            for p in products:
                print(f"    * {p.product_name} v{p.version} (Source: {p.installation_source})")
                
    finally:
        db.close()

if __name__ == "__main__":
    test_discovery()
