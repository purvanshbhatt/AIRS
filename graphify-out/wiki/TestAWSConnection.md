# TestAWSConnection

> 26 nodes · cohesion 0.14

## Key Concepts

- **TestAWSConnection** (14 connections) — `tests/aws_integration/test_connection.py`
- **_run()** (12 connections) — `tests/aws_integration/test_connection.py`
- **._make_connector()** (12 connections) — `tests/aws_integration/test_connection.py`
- **test_connection.py** (5 connections) — `tests/aws_integration/test_connection.py`
- **.test_authenticate_invalid_credentials()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_authenticate_no_boto3()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_authenticate_success()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_authenticate_with_role_arn()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_health_check_healthy()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_health_check_not_authenticated()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_health_check_unreachable()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_validate_permissions_all_present()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_validate_permissions_missing_get_findings()** (4 connections) — `tests/aws_integration/test_connection.py`
- **.test_validate_permissions_not_authenticated()** (4 connections) — `tests/aws_integration/test_connection.py`
- **Tests for AWS Security Hub connector authentication, health, and permissions.** (2 connections) — `tests/aws_integration/test_connection.py`
- **When describe_hub succeeds, health status is 'healthy'.** (1 connections) — `tests/aws_integration/test_connection.py`
- **Run an async coroutine in a fresh event loop.** (1 connections) — `tests/aws_integration/test_connection.py`
- **When describe_hub raises, health status is 'unreachable'.** (1 connections) — `tests/aws_integration/test_connection.py`
- **When hub_client is None, health status is 'unreachable'.** (1 connections) — `tests/aws_integration/test_connection.py`
- **When all API calls succeed, permissions are valid.** (1 connections) — `tests/aws_integration/test_connection.py`
- **When GetFindings raises, it's reported as missing permission.** (1 connections) — `tests/aws_integration/test_connection.py`
- **When not authenticated, permissions validation fails cleanly.** (1 connections) — `tests/aws_integration/test_connection.py`
- **Mock boto3 session and securityhub client, verify authenticate() returns True.** (1 connections) — `tests/aws_integration/test_connection.py`
- **When boto3 is not installed, authenticate() returns False gracefully.** (1 connections) — `tests/aws_integration/test_connection.py`
- **Invalid credentials cause describe_hub to fail, authenticate returns False.** (1 connections) — `tests/aws_integration/test_connection.py`
- *... and 1 more nodes in this community*

## Relationships

- [AWSSecurityHubConnector](AWSSecurityHubConnector.md) (3 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (1 shared connections)

## Source Files

- `tests/aws_integration/test_connection.py`

## Audit Trail

- EXTRACTED: 49 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*