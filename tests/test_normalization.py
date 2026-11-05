import pytest
from app.services.lifecycle.normalization import VersionNormalizationEngine

def test_normalization_accuracy():
    engine = VersionNormalizationEngine()

    cases = [
        # Python
        ("py-3.8.1-win", "Python Software Foundation", "Python", "3.8.1"),
        ("python/3.8.1", "Python Software Foundation", "Python", "3.8.1"),
        # PostgreSQL
        ("postgres11", "PostgreSQL Global Development Group", "PostgreSQL", "11"),
        ("postgresql-11", "PostgreSQL Global Development Group", "PostgreSQL", "11"),
        # NodeJS
        ("node-v18.16.0", "OpenJS Foundation", "Node.js", "18.16.0"),
        ("nodejs 18", "OpenJS Foundation", "Node.js", "18"),
        # Java
        ("java-8-openjdk", "Oracle Corporation", "Java", "8"),
        # Nginx
        ("nginx-1.20", "F5, Inc.", "NGINX", "1.20")
    ]

    successes = 0
    total = len(cases)

    print("\n--- Normalization Coverage Report ---")
    for raw, expected_vendor, expected_product, expected_version in cases:
        normalized = engine.normalize(raw)
        
        is_success = (
            normalized.version == expected_version and 
            normalized.vendor == expected_vendor and 
            normalized.product == expected_product
        )
        
        if is_success:
            successes += 1
            print(f"[PASS] {raw} -> {normalized.vendor} | {normalized.product} | {normalized.version}")
        else:
            print(f"[FAIL] {raw} -> Got: {normalized.vendor} | {normalized.product} | {normalized.version}")
            
    accuracy = successes / total
    print(f"\nTotal Accuracy: {accuracy * 100:.1f}%")
    assert accuracy >= 0.95  # Target is 95%
