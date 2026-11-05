import ast
import inspect
import pytest


class TestDeterministicScoring:
    """Verify the AWS connector enforces deterministic scoring invariants.

    Product Invariants:
    - LLMs NEVER calculate readiness scores
    - LLMs NEVER modify findings
    - LLMs NEVER determine framework mappings
    - Connectors NEVER modify scores or findings directly
    """

    def test_aws_connector_has_no_llm_imports(self):
        """Verify the AWS connector module does not import any LLM/AI modules."""
        import app.connectors.aws_security_hub as mod
        source = inspect.getsource(mod)
        tree = ast.parse(source)

        forbidden_modules = {
            "google.generativeai", "google.genai", "openai",
            "anthropic", "langchain", "gemini",
            "app.services.ai_narrative", "app.services.intelligence",
            "app.services.explanation",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules, \
                        f"AWS connector imports forbidden module: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert node.module not in forbidden_modules, \
                        f"AWS connector imports from forbidden module: {node.module}"

    def test_connector_never_modifies_scores(self):
        """Verify the connector source has no scoring logic."""
        import app.connectors.aws_security_hub as mod
        source = inspect.getsource(mod)
        scoring_terms = ["readiness_score", "calculate_score", "compute_score",
                        "update_score", "score =", "ReadinessLedger"]
        for term in scoring_terms:
            assert term not in source, \
                f"AWS connector contains scoring logic: '{term}'"

    def test_connector_never_creates_findings(self):
        """Verify the connector never creates Finding model objects."""
        import app.connectors.aws_security_hub as mod
        source = inspect.getsource(mod)
        assert "from app.models.finding import" not in source
        assert "Finding(" not in source

    def test_evidence_ingestion_preserves_payload(self):
        """Verify findings are stored as-is, not modified."""
        from app.connectors.aws_security_hub import AWSSecurityHubConnector

        connector = AWSSecurityHubConnector(
            connector_id="test", org_id="test", credentials={}
        )

        finding = {
            "Id": "preserve-test",
            "Title": "Test Finding Title",
            "Description": "Test Description",
            "Severity": {"Label": "HIGH", "Normalized": 70},
            "Compliance": {"Status": "FAILED"},
            "RecordState": "ACTIVE",
            "Workflow": {"Status": "NEW"},
            "Resources": [{"Id": "arn:aws:s3:::test"}],
            "GeneratorId": "test-generator",
            "CreatedAt": "2026-09-13T10:00:00Z",
            "UpdatedAt": "2026-09-13T10:00:00Z",
        }

        event = connector._normalize_finding(finding)
        # The payload must faithfully represent the source
        assert event.payload["title"] == finding["Title"]
        assert event.payload["description"] == finding["Description"]
        assert event.payload["compliance_status"] == "FAILED"
        assert event.payload["generator_id"] == "test-generator"

    def test_control_mapping_not_implemented(self):
        """Document that AWS findings are NOT yet mapped to control IDs.

        This is an integration gap, not a test failure.
        The connector correctly ingests findings but does not assign control_id.
        """
        from app.connectors.aws_security_hub import AWSSecurityHubConnector

        connector = AWSSecurityHubConnector(
            connector_id="test", org_id="test", credentials={}
        )
        finding = {
            "Id": "mapping-test",
            "Severity": {"Label": "MEDIUM"},
            "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/S3.4",
        }
        event = connector._normalize_finding(finding)
        # control_id is NOT set — this is a known gap
        # The finding IS ingested, but not mapped to a framework control
        assert event.payload.get("control_id") is None
