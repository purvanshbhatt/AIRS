"""
Tests for the in-app API reference:

  GET /api/v1/reference/openapi  — customer-safe OpenAPI document
  GET /api/v1/reference/status   — live status for the explorer
"""

import json
from unittest.mock import PropertyMock, patch

import pytest

from app.api.v1 import api_reference
from app.api.v1.api_reference import (
    DENIED_PATH_PREFIXES,
    PUBLIC_PROBE_PATHS,
    filter_openapi_document,
    is_customer_safe_path,
)

OPENAPI_URL = "/api/v1/reference/openapi"
STATUS_URL = "/api/v1/reference/status"

HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}


@pytest.fixture(autouse=True)
def _fresh_reference_cache():
    api_reference.reset_reference_cache()
    yield
    api_reference.reset_reference_cache()


def _auth_required():
    return patch(
        "app.core.config.Settings.is_auth_required",
        new_callable=PropertyMock,
        return_value=True,
    )


# ── Auth ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("url", [OPENAPI_URL, STATUS_URL])
def test_reference_requires_sign_in(client, url):
    with _auth_required():
        response = client.get(url)
    assert response.status_code == 401


@pytest.mark.parametrize("url", [OPENAPI_URL, STATUS_URL])
def test_reference_available_to_signed_in_user(client_no_org, url):
    with _auth_required():
        response = client_no_org.get(url)
    assert response.status_code == 200


def test_operator_docs_keep_basic_auth_guard(client):
    """The in-app reference must not open up the operator Swagger pages."""
    for url in ("/openapi.json", "/docs", "/redoc"):
        assert client.get(url).status_code == 401, url
        assert client.get(url, auth=("admin", "not-the-password")).status_code == 401, url
        # A signed-in user's bearer token is not a docs password either.
        bearer = {"Authorization": "Bearer some-signed-in-user-token"}
        assert client.get(url, headers=bearer).status_code == 401, url


# ── Document filtering ──────────────────────────────────────────────────────


def test_openapi_document_shape(client):
    document = client.get(OPENAPI_URL).json()
    assert document["openapi"].startswith("3.")
    assert document["info"]["title"]
    assert document["paths"]
    for path, item in document["paths"].items():
        assert path.startswith("/api/v1/") or path in PUBLIC_PROBE_PATHS, path
        assert HTTP_METHODS & set(item), path


def test_openapi_document_lists_customer_endpoints(client):
    paths = client.get(OPENAPI_URL).json()["paths"]
    for expected in (
        "/api/v1/methodology",
        "/api/v1/connectors",
        "/api/v1/reference/openapi",
        "/api/v1/reference/status",
        "/health",
    ):
        assert expected in paths, expected


def test_openapi_document_hides_internal_paths(client):
    paths = client.get(OPENAPI_URL).json()["paths"]
    assert paths

    for path in paths:
        segments = {segment.lower() for segment in path.split("/") if segment}
        assert "debug" not in segments, path
        assert "admin" not in segments, path
        assert "internal" not in segments, path
        assert "webhook" not in segments and "webhooks" not in segments, path
        for prefix in DENIED_PATH_PREFIXES:
            assert not path.startswith(prefix), path

    # Named explicitly: these exist on the service and must never be listed.
    for hidden in (
        "/debug/ip",
        "/api/debug/build-info",
        "/internal/governance/validate",
        "/openapi.json",
        "/docs",
        "/api/v1/pilot-leads",
        "/api/v1/connectors/webhook/{connector_type}",
        "/api/v1/telemetry/webhook/event",
        "/api/v1/telemetry/webhook/health",
        "/api/v1/integrations/siem/event",
        "/api/v1/observability/metrics",
        "/health/cors",
        "/health/llm",
    ):
        assert hidden not in paths, hidden


def test_openapi_document_tags_are_safe_and_deduplicated(client):
    paths = client.get(OPENAPI_URL).json()["paths"]
    for path, item in paths.items():
        for method, operation in item.items():
            if method not in HTTP_METHODS:
                continue
            tags = [tag.lower() for tag in operation.get("tags", [])]
            assert len(tags) == len(set(tags)), (path, tags)
            assert not set(tags) & api_reference.DENIED_TAGS, (path, tags)


def test_openapi_document_references_resolve(client):
    """Every $ref must point at a schema that survived the filter."""
    document = client.get(OPENAPI_URL).json()
    schemas = document.get("components", {}).get("schemas", {})
    found = set()
    api_reference._collect_refs(document["paths"], found)
    api_reference._collect_refs(schemas, found)
    assert found, "expected at least one schema reference"
    assert found <= set(schemas), sorted(found - set(schemas))


def test_openapi_document_is_cached(client):
    with patch.object(
        api_reference, "build_reference_document", wraps=api_reference.build_reference_document
    ) as build:
        first = client.get(OPENAPI_URL).json()
        second = client.get(OPENAPI_URL).json()
    assert first == second
    assert build.call_count == 1


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/api/v1/methodology", True),
        ("/api/v1/connectors/{connector_id}/sync", True),
        ("/health", True),
        ("/health/system", True),
        ("/health/cors", False),
        ("/health/llm", False),
        ("/", False),
        ("/docs", False),
        ("/openapi.json", False),
        ("/debug/ip", False),
        ("/api/debug/build-info", False),
        ("/internal/governance/validate", False),
        ("/api/orgs", False),
        ("/api/v1/admin/users", False),
        ("/api/v1/orgs/{org_id}/admin/reset", False),
        ("/api/v1/debug/state", False),
        ("/api/v1/internal/seed", False),
        ("/api/v1/demo/seed", False),
        ("/api/v1/pilot-leads", False),
        ("/api/v1/pilot-leads/admin", False),
        ("/api/v1/billing/webhook", False),
        ("/api/v1/billing/webhooks/stripe", False),
        ("/api/v1/connectors/webhook/{connector_type}", False),
        ("/api/v1/telemetry/webhook/event", False),
        ("/api/v1/integrations/siem/event", False),
        ("/api/v1/observability/metrics", False),
    ],
)
def test_is_customer_safe_path(path, expected):
    assert is_customer_safe_path(path) is expected


def test_filter_drops_denied_operations_and_orphan_schemas():
    def op(tag, schema=None):
        operation = {"tags": [tag, tag], "responses": {"200": {"description": "ok"}}}
        if schema:
            operation["responses"]["200"]["content"] = {
                "application/json": {"schema": {"$ref": f"#/components/schemas/{schema}"}}
            }
        return operation

    document = {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": "1"},
        "paths": {
            "/api/v1/things": {"get": op("things", "Thing")},
            "/api/v1/mixed": {"get": op("things"), "post": op("admin", "AdminOnly")},
            "/api/v1/admin/users": {"get": op("things", "AdminOnly")},
            "/api/v1/billing/webhook": {"post": op("billing", "WebhookPayload")},
            "/debug/ip": {"get": op("things")},
            "/api/orgs": {"get": op("organizations")},
        },
        "components": {
            "schemas": {
                "Thing": {
                    "type": "object",
                    "properties": {"part": {"$ref": "#/components/schemas/Part"}},
                },
                "Part": {"type": "object"},
                "AdminOnly": {"type": "object"},
                "WebhookPayload": {"type": "object"},
            },
            "securitySchemes": {"HTTPBearer": {"type": "http", "scheme": "bearer"}},
        },
    }

    filtered = filter_openapi_document(document)

    assert set(filtered["paths"]) == {"/api/v1/things", "/api/v1/mixed"}
    assert set(filtered["paths"]["/api/v1/mixed"]) == {"get"}
    assert filtered["paths"]["/api/v1/things"]["get"]["tags"] == ["things"]
    assert set(filtered["components"]["schemas"]) == {"Thing", "Part"}
    assert "securitySchemes" in filtered["components"]
    # The input is left untouched.
    assert "/debug/ip" in document["paths"]
    assert "AdminOnly" in document["components"]["schemas"]


# ── Status ──────────────────────────────────────────────────────────────────


def test_status_shape(client):
    response = client.get(STATUS_URL)
    assert response.status_code == 200
    body = response.json()

    assert set(body) == {
        "api_version",
        "build",
        "environment",
        "server_time",
        "demo_mode",
        "read_only",
        "endpoint_count",
        "checks",
    }
    assert body["api_version"]
    assert body["environment"]
    assert body["server_time"].endswith("+00:00")
    assert body["endpoint_count"] > 0

    assert [check["id"] for check in body["checks"]] == [
        "api",
        "data_store",
        "narratives",
        "connectors",
    ]
    for check in body["checks"]:
        assert set(check) == {"id", "label", "ok", "detail"}
        assert isinstance(check["ok"], bool)
        assert check["label"] and check["detail"]

    assert body["checks"][0]["ok"] is True


def test_status_failure_reports_no_internal_detail(client):
    marker = "db-7.internal.example:5432 password=hunter2"
    with patch("app.db.firestore.is_firestore_available", side_effect=RuntimeError(marker)):
        response = client.get(STATUS_URL)

    assert response.status_code == 200
    body = response.json()
    data_store = next(check for check in body["checks"] if check["id"] == "data_store")
    assert data_store["ok"] is False

    text = json.dumps(body)
    assert marker not in text
    assert "hunter2" not in text
    assert "Traceback" not in text


def test_status_contains_no_secret_looking_fields(client):
    text = json.dumps(client.get(STATUS_URL).json()).lower()
    for word in ("password", "secret", "api_key", "token", "http://", "https://"):
        assert word not in text, word
