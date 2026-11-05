"""Request correlation, cache, CORS, and rate-limiting tests."""

from app.rate_limit import RateLimiter, limiter


def test_request_id_is_generated(client):
    response = client.get("/api/residents")
    request_id = response.headers["x-request-id"]
    assert len(request_id) == 32
    assert all(character.isalnum() for character in request_id)


def test_valid_request_id_is_reused(client):
    response = client.get(
        "/api/residents", headers={"X-Request-ID": "support-case-123"}
    )
    assert response.headers["x-request-id"] == "support-case-123"


def test_invalid_request_id_is_replaced(client):
    response = client.get(
        "/api/residents", headers={"X-Request-ID": "not a valid id!"}
    )
    assert response.headers["x-request-id"] != "not a valid id!"


def test_non_ascii_request_id_is_replaced():
    from types import SimpleNamespace

    from app.main import _request_id

    generated = _request_id(SimpleNamespace(headers={"x-request-id": "identifié"}))
    assert generated != "identifié"
    assert len(generated) == 32
    assert generated.isascii()


def test_api_and_health_responses_are_not_cached(client):
    api_response = client.get("/api/residents")
    assert api_response.headers["cache-control"] == "no-store"

    health_response = client.get("/health")
    assert health_response.headers["cache-control"] == "no-store"


def test_extended_security_headers_are_present(client):
    response = client.get("/health")
    assert response.headers["cross-origin-opener-policy"] == "same-origin"
    assert response.headers["cross-origin-resource-policy"] == "same-origin"
    assert response.headers["x-permitted-cross-domain-policies"] == "none"


def test_cors_exposes_total_count_to_allowed_origin(client):
    response = client.get(
        "/api/residents", headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 200
    assert "x-total-count" in response.headers["access-control-expose-headers"].lower()


def test_cors_does_not_allow_unknown_origin(client):
    response = client.get(
        "/api/residents", headers={"Origin": "https://untrusted.example"}
    )
    assert "access-control-allow-origin" not in response.headers


def test_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    limiter.reset()
    monkeypatch.setenv("RESIDENTS_RATE_LIMIT_PER_MINUTE", "2")
    try:
        assert client.get("/api/residents").status_code == 200
        assert client.get("/api/residents").status_code == 200
        response = client.get("/api/residents")
        assert response.status_code == 429
        assert response.json() == {"detail": "Too many requests"}
        assert int(response.headers["retry-after"]) >= 1
        assert response.headers["x-request-id"]
    finally:
        limiter.reset()


def test_health_is_not_rate_limited(client, monkeypatch):
    limiter.reset()
    monkeypatch.setenv("RESIDENTS_RATE_LIMIT_PER_MINUTE", "1")
    try:
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 200
    finally:
        limiter.reset()


def test_forwarded_for_is_ignored_unless_proxy_is_trusted(client, monkeypatch):
    limiter.reset()
    monkeypatch.setenv("RESIDENTS_RATE_LIMIT_PER_MINUTE", "1")
    monkeypatch.delenv("RESIDENTS_TRUST_PROXY", raising=False)
    try:
        assert client.get(
            "/api/residents", headers={"X-Forwarded-For": "198.51.100.1"}
        ).status_code == 200
        assert client.get(
            "/api/residents", headers={"X-Forwarded-For": "198.51.100.2"}
        ).status_code == 429
    finally:
        limiter.reset()


def test_forwarded_for_is_used_when_proxy_is_trusted(client, monkeypatch):
    limiter.reset()
    monkeypatch.setenv("RESIDENTS_RATE_LIMIT_PER_MINUTE", "1")
    monkeypatch.setenv("RESIDENTS_TRUST_PROXY", "true")
    try:
        assert client.get(
            "/api/residents", headers={"X-Forwarded-For": "198.51.100.1"}
        ).status_code == 200
        assert client.get(
            "/api/residents", headers={"X-Forwarded-For": "198.51.100.2"}
        ).status_code == 200
    finally:
        limiter.reset()


def test_invalid_content_length_is_rejected(client):
    response = client.get("/api/residents", headers={"Content-Length": "invalid"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Content-Length header"}


def test_rate_limiter_bounds_tracked_keys():
    local_limiter = RateLimiter(max_keys=3)
    for index in range(10):
        local_limiter.check(f"client-{index}", limit=10)
    assert local_limiter.tracked_keys <= 3
