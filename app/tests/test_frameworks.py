from app.core.frameworks import get_all_framework_refs, FINDING_FRAMEWORK_MAPPINGS

def test_get_framework_refs_keys_exist():
    """Ensure get_all_framework_refs returns all keys even if empty."""
    refs = get_all_framework_refs("non_existent_id")
    assert "mitre" in refs
    assert "cis" in refs
    assert "owasp" in refs
    assert refs["mitre"] == []
    assert refs["cis"] == []
    assert refs["owasp"] == []

def test_mapping_tl_01():
    """Test specific mapping for Network Logs."""
    refs = get_all_framework_refs("tl_01")
    assert len(refs["mitre"]) > 0
    # specific check
    ids = [m["id"] for m in refs["mitre"]]
    assert "T1059" in ids or "T1071" in ids

def test_mapping_iv_01():
    """Test specific mapping for MFA."""
    refs = get_all_framework_refs("iv_01")
    ids = [m["id"] for m in refs["mitre"]]
    assert "T1078" in ids

def test_all_mappings_valid():
    """Ensure all mappings in dictionary result in valid refs (no crashes)."""
    for rule_id in FINDING_FRAMEWORK_MAPPINGS:
        refs = get_all_framework_refs(rule_id)
        assert isinstance(refs["mitre"], list)
