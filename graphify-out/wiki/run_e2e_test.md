# run_e2e_test

> 7 nodes · cohesion 0.38

## Key Concepts

- **run_e2e_test()** (6 connections) — `tests/aws_integration/test_e2e_healthcare.py`
- **test_e2e_healthcare.py** (4 connections) — `tests/aws_integration/test_e2e_healthcare.py`
- **get_aws_credentials()** (3 connections) — `tests/aws_integration/test_e2e_healthcare.py`
- **main()** (2 connections) — `tests/aws_integration/test_e2e_healthcare.py`
- **Any** (1 connections)
- **Resolve AWS credentials from environment or boto3 session.** (1 connections) — `tests/aws_integration/test_e2e_healthcare.py`
- **Execute full end-to-end test and return results.** (1 connections) — `tests/aws_integration/test_e2e_healthcare.py`

## Relationships

- [AWSSecurityHubConnector](AWSSecurityHubConnector.md) (2 shared connections)

## Source Files

- `tests/aws_integration/test_e2e_healthcare.py`

## Audit Trail

- EXTRACTED: 10 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*