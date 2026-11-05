# Settings

> 17 nodes · cohesion 0.12

## Key Concepts

- **Settings** (29 connections) — `app/core/config.py`
- **.is_auth_required()** (2 connections) — `app/core/config.py`
- **.is_aws()** (2 connections) — `app/core/config.py`
- **.is_demo_mode()** (2 connections) — `app/core/config.py`
- **.is_gcp()** (2 connections) — `app/core/config.py`
- **.is_local()** (2 connections) — `app/core/config.py`
- **.is_prod()** (2 connections) — `app/core/config.py`
- **.is_read_only()** (2 connections) — `app/core/config.py`
- **Application settings with validation. Environment variables take precedence…** (1 connections) — `app/core/config.py`
- **Check if running in local environment.** (1 connections) — `app/core/config.py`
- **Check if running in production-like environment (demo, staging, or prod).** (1 connections) — `app/core/config.py`
- **Check if authentication is required for protected endpoints. Auth is required…** (1 connections) — `app/core/config.py`
- **Check if running in demo mode for presentations/testing.** (1 connections) — `app/core/config.py`
- **Check if the environment is read-only (demo mode). In demo mode, all write…** (1 connections) — `app/core/config.py`
- **Check if running in AWS environment.** (1 connections) — `app/core/config.py`
- **Check if running in GCP environment.** (1 connections) — `app/core/config.py`
- **BaseSettings** (1 connections)

## Relationships

- [TestCloudProviderConfiguration](TestCloudProviderConfiguration.md) (5 shared connections)
- [main.py](main.py.md) (5 shared connections)
- [.normalize_cloud_and_env](normalize_cloud_and_env.md) (2 shared connections)
- [.validate_cors_origins](validate_cors_origins.md) (2 shared connections)
- [get_settings](get_settings.md) (1 shared connections)
- [TestMultiCloudHealthCheck](TestMultiCloudHealthCheck.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [.cors_origins_list](cors_origins_list.md) (1 shared connections)
- [.is_staging](is_staging.md) (1 shared connections)
- [.is_llm_enabled](is_llm_enabled.md) (1 shared connections)

## Source Files

- `app/core/config.py`

## Audit Trail

- EXTRACTED: 36 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*