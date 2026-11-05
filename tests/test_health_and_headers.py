"""Health endpoint, security headers, and SPA fallback tests."""

from .conftest import RESIDENT_PAYLOAD


def test_health_reports_database_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_security_headers_are_present(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "camera=()" in response.headers["Permissions-Policy"]
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_api_responses_also_receive_security_headers(client):
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 201
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_unknown_api_route_returns_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_oversized_request_body_is_rejected(client, monkeypatch):
    monkeypatch.setenv("RESIDENTS_MAX_REQUEST_BYTES", "10")
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large"}


def test_hsts_is_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv("RESIDENTS_HSTS", raising=False)
    response = client.get("/health")
    assert "Strict-Transport-Security" not in response.headers


def test_hsts_can_be_enabled_for_https_deployments(client, monkeypatch):
    monkeypatch.setenv("RESIDENTS_HSTS", "true")
    response = client.get("/health")
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]


def test_openapi_documentation_is_available(client):
    docs = client.get("/docs")
    assert docs.status_code == 200
    # Swagger UI needs its own CDN assets and inline bootstrap script.
    assert "Content-Security-Policy" not in docs.headers

    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert schema.json()["info"]["title"] == "Residents Management API"
