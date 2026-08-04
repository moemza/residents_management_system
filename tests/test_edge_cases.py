"""
Edge case tests — ensure the API handles boundary conditions and bad input
without crashing (no 500s).
"""
from .conftest import RESIDENT_PAYLOAD


def _create(client, **overrides):
    return client.post("/api/residents", json={**RESIDENT_PAYLOAD, **overrides}).json()


# ── Empty-string optional fields (real frontend behaviour) ────────────────────

def test_empty_string_email_treated_as_null(client):
    """Frontend sends email='' — must be accepted and stored as null, not 422."""
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "email": ""})
    assert response.status_code == 201
    assert response.json()["email"] is None


def test_empty_string_cellphone2_treated_as_null(client):
    """Frontend sends cellphone_no2='' — must be accepted and stored as null."""
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "cellphone_no2": ""})
    assert response.status_code == 201
    assert response.json()["cellphone_no2"] is None


def test_empty_string_email_on_update_treated_as_null(client):
    """PUT with email='' must not 422."""
    resident = _create(client)
    response = client.put(f"/api/residents/{resident['id']}", json={**RESIDENT_PAYLOAD, "email": ""})
    assert response.status_code == 200
    assert response.json()["email"] is None


# ── Whitespace-only required fields ──────────────────────────────────────────

def test_whitespace_only_first_name_rejected(client):
    """Whitespace-only first_name must be rejected — sanitizer strips it to ''."""
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "first_name": "   "})
    assert response.status_code == 422


def test_whitespace_only_cellphone_rejected(client):
    """Whitespace-only cellphone_no must be rejected."""
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "cellphone_no": "   "})
    assert response.status_code == 422


# ── XSS / injection in every string field ────────────────────────────────────

def test_xss_in_last_name_sanitized(client):
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "last_name": "<img src=x onerror=alert(1)>"})
    assert response.status_code == 201
    assert "<img" not in response.json()["last_name"]


def test_xss_in_village_sanitized(client):
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "village": "<script>bad()</script>"})
    assert response.status_code == 201
    assert "<script>" not in response.json()["village"]


def test_xss_in_skill_name_sanitized(client):
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "skills": [{"name": "<b>hack</b>"}]})
    assert response.status_code == 201
    assert "<b>" not in response.json()["skills"][0]["name"]


def test_xss_in_search_query_does_not_crash(client):
    """XSS payload in search query must return 200, not 500."""
    response = client.get("/api/search?query=<script>alert(1)</script>&search_type=name")
    assert response.status_code == 200


# ── Boundary values ───────────────────────────────────────────────────────────

def test_dob_today_is_accepted(client):
    """DOB equal to today is valid (not in the future)."""
    from datetime import date
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "dob": date.today().isoformat()})
    assert response.status_code == 201


def test_very_old_dob_accepted(client):
    """Extremely old DOB (1900) should not crash the API."""
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "dob": "1900-01-01"})
    assert response.status_code == 201


def test_resident_id_zero_returns_404(client):
    """ID 0 is not a valid resident — must return 404, not 500."""
    assert client.get("/api/residents/0").status_code == 404


def test_resident_id_negative_returns_422_or_404(client):
    """Negative ID must not crash — expect 404 or 422."""
    assert client.get("/api/residents/-1").status_code in (404, 422)


def test_resident_id_string_returns_422(client):
    """Non-integer ID must return 422, not 500."""
    assert client.get("/api/residents/abc").status_code == 422


# ── Malformed request bodies ──────────────────────────────────────────────────

def test_post_empty_body_returns_422(client):
    """Empty body must return 422, not 500."""
    assert client.post("/api/residents", json={}).status_code == 422


def test_post_null_body_returns_422(client):
    """Null JSON body must return 422, not 500."""
    assert client.post("/api/residents", content=b"null", headers={"Content-Type": "application/json"}).status_code == 422


def test_post_wrong_type_for_dob_returns_422(client):
    """Sending an integer for dob must return 422."""
    assert client.post("/api/residents", json={**RESIDENT_PAYLOAD, "dob": 19900101}).status_code == 422


def test_post_wrong_type_for_skills_returns_422(client):
    """Sending a string instead of a list for skills must return 422."""
    assert client.post("/api/residents", json={**RESIDENT_PAYLOAD, "skills": "Python"}).status_code == 422


# ── Large inputs ──────────────────────────────────────────────────────────────

def test_very_long_first_name_accepted(client):
    """A very long name should be stored without crashing."""
    long_name = "A" * 500
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "first_name": long_name})
    assert response.status_code == 201
    assert response.json()["first_name"] == long_name


def test_many_skills_accepted(client):
    """Submitting 50 skills at once should not crash."""
    skills = [{"name": f"Skill {i}"} for i in range(50)]
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, "skills": skills})
    assert response.status_code == 201
    assert len(response.json()["skills"]) == 50


# ── Duplicate residents ───────────────────────────────────────────────────────

def test_duplicate_resident_allowed(client):
    """The API does not enforce uniqueness — two identical residents can be created."""
    r1 = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    r2 = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


# ── Delete then operate ───────────────────────────────────────────────────────

def test_update_after_delete_returns_404(client):
    """PUT on a deleted resident must return 404, not 500."""
    resident = _create(client)
    client.delete(f"/api/residents/{resident['id']}")
    assert client.put(f"/api/residents/{resident['id']}", json=RESIDENT_PAYLOAD).status_code == 404


def test_delete_already_deleted_returns_404(client):
    """Deleting the same resident twice must return 404 on the second call."""
    resident = _create(client)
    client.delete(f"/api/residents/{resident['id']}")
    assert client.delete(f"/api/residents/{resident['id']}").status_code == 404


# ── Search edge cases ─────────────────────────────────────────────────────────

def test_search_with_special_characters_does_not_crash(client):
    """SQL special characters in search query must not crash the API."""
    for term in ["%", "_", "'", '"', "\\", "--", ";"]:
        response = client.get(f"/api/search?query={term}&search_type=name")
        assert response.status_code == 200, f"Crashed on query: {term!r}"


def test_search_very_long_query_does_not_crash(client):
    """A very long search query must not crash the API."""
    long_query = "A" * 1000
    assert client.get(f"/api/search?query={long_query}&search_type=name").status_code == 200
