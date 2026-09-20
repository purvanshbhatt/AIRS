# AWS Integration Tests

This directory contains test scaffolding and integration tests for the ResilAI AWS Security Hub connector.

## Structure
- `conftest.py`: Shared fixtures including DB and AWS credentials
- `test_connection.py`: Authentication and permission validation tests
- `test_security_hub_ingestion.py`: Synchronization and data mapping tests
- `test_evidence_pipeline.py`: Ingestion to database and deduplication
- `test_tenant_isolation.py`: Validates multi-tenant data isolation
- `test_negative_cases.py`: Error handling and graceful degradation
- `test_deterministic_scoring.py`: Validates no LLM usage and exact payload storage
- `configure_connector.py`: CLI script for manual verification

## Running Tests
Run unit tests (no live AWS credentials needed):
```bash
pytest tests/aws_integration/ -v -m "not aws_integration"
```

Run integration tests (requires live AWS credentials):
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_REGION="your_region"
pytest tests/aws_integration/ -v -m aws_integration
```

## Security Rules
- NEVER hardcode AWS credentials in test files
- NEVER print or log AWS credentials
- The `test_no_credentials_in_telemetry_payload` validates no credentials leak to DB
