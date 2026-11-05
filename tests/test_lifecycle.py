import pytest
from app.services.lifecycle.lifecycle_intelligence import LifecycleIntelligenceService
from app.models.tech_stack import TechStackItem

from tests.conftest import db_session
from app.models.lifecycle_catalog import GlobalSoftwareCatalog, SoftwareVersion

def test_lifecycle_validation(db_session):
    # Seed the DB with required software catalogs for the test cases
    from datetime import date
    db_session.add_all([
        GlobalSoftwareCatalog(product_name="Python", vendor="Python Software Foundation", product_family="runtime"),
        GlobalSoftwareCatalog(product_name="PostgreSQL", vendor="PostgreSQL Global Development Group", product_family="database"),
        GlobalSoftwareCatalog(product_name="Node.js", vendor="OpenJS Foundation", product_family="runtime"),
        GlobalSoftwareCatalog(product_name="Java", vendor="Oracle Corporation", product_family="runtime")
    ])
    db_session.commit()
    
    # We also need to add the versions that are expected to be END_OF_LIFE and ACTIVE
    # Python 3.8
    db_session.add(SoftwareVersion(
        catalog_id=db_session.query(GlobalSoftwareCatalog).filter_by(product_name="Python").first().id,
        version_name="3.8",
        eol_date=date(2024, 10, 14),
        support_status="end_of_life"
    ))
    # PostgreSQL 11
    db_session.add(SoftwareVersion(
        catalog_id=db_session.query(GlobalSoftwareCatalog).filter_by(product_name="PostgreSQL").first().id,
        version_name="11",
        eol_date=date(2023, 11, 9),
        support_status="end_of_life"
    ))
    # Node.js 16
    db_session.add(SoftwareVersion(
        catalog_id=db_session.query(GlobalSoftwareCatalog).filter_by(product_name="Node.js").first().id,
        version_name="16",
        eol_date=date(2023, 9, 11),
        support_status="end_of_life"
    ))
    # Java 8
    db_session.add(SoftwareVersion(
        catalog_id=db_session.query(GlobalSoftwareCatalog).filter_by(product_name="Java").first().id,
        version_name="8",
        eol_date=date(2030, 12, 31),
        support_status="supported"
    ))
    db_session.commit()

    service = LifecycleIntelligenceService(db=db_session)
    
    test_cases = [
        ("Python Software Foundation", "Python", "3.8", "EOL"),
        ("PostgreSQL Global Development Group", "PostgreSQL", "11", "EOL"),
        ("OpenJS Foundation", "Node.js", "16", "EOL"),
        ("Oracle Corporation", "Java", "8", "SUPPORTED") # Java 8 has long-term support
    ]
    
    print("\n--- Lifecycle Intelligence Coverage Report ---")
    
    # We'll test against the raw determinator directly to avoid needing a DB mock if possible
    # But if the service requires the DB, we will mock the tech_stack item
    for vendor, product, version, expected_status in test_cases:
        result = service.check_lifecycle_status(
            product_name=product,
            version=version,
            vendor=vendor
        )
        
        # We also need to extract Days Since/Until EOL and Recommended Version
        days_until = result.days_until_eol
        recommended = result.upgrade_recommendation
        
        is_success = result.lifecycle_status.value == expected_status.lower()
        
        if is_success:
            print(f"[PASS] {product} {version} -> {result.lifecycle_status.value}")
            print(f"       Days Until: {days_until}, Rec: {recommended}")
        else:
            print(f"[FAIL] {product} {version} -> Expected {expected_status.lower()}, Got {result.lifecycle_status.value}")
            
        assert is_success

