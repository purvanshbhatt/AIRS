import pytest
from app.services.lifecycle.lifecycle_intelligence import LifecycleIntelligenceService
from app.models.tech_stack import TechStackItem

def test_lifecycle_validation():
    from app.db.database import SessionLocal
    db = SessionLocal()
    
    service = LifecycleIntelligenceService(db=db)
    
    test_cases = [
        ("Python Software Foundation", "Python", "3.8", "END_OF_LIFE"),
        ("PostgreSQL Global Development Group", "PostgreSQL", "11", "END_OF_LIFE"),
        ("OpenJS Foundation", "Node.js", "16", "END_OF_LIFE"),
        ("Oracle Corporation", "Java", "8", "ACTIVE") # Java 8 has long-term support
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

