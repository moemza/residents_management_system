"""
Integration tests for Search Resident page user stories (US-SR-01 – US-SR-08).
"""
from .conftest import RESIDENT_PAYLOAD


def _create(client, **overrides):
    return client.post("/api/residents", json={**RESIDENT_PAYLOAD, **overrides}).json()


# ── US-SR-01 / US-SR-02: Search by name ──────────────────────────────────────

def test_us_sr02_search_by_first_name(client):
    """Partial first-name match returns the resident."""
    _create(client)
    response = client.get("/api/search?query=Mph&search_type=name")
    assert response.status_code == 200
    assert any(r["first_name"] == "Mpho" for r in response.json())


def test_us_sr02_search_by_last_name(client):
    """Partial last-name match returns the resident."""
    _create(client)
    response = client.get("/api/search?query=Mogow&search_type=name")
    assert response.status_code == 200
    assert any(r["last_name"] == "Mogowane" for r in response.json())


def test_us_sr02_name_search_is_case_insensitive(client):
    """Name search is case-insensitive."""
    _create(client)
    response = client.get("/api/search?query=mpho&search_type=name")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_us_sr02_name_search_no_match_returns_empty(client):
    """Name search with no match returns an empty list, not an error."""
    _create(client)
    response = client.get("/api/search?query=Zzzzz&search_type=name")
    assert response.status_code == 200
    assert response.json() == []


# ── US-SR-03: Search by village ──────────────────────────────────────────────

def test_us_sr03_search_by_village(client):
    """Village search returns residents from that village."""
    _create(client)
    response = client.get("/api/search?query=Village+A&search_type=village")
    assert response.status_code == 200
    assert all(r["village"] == "Village A" for r in response.json())


def test_us_sr03_village_search_excludes_other_villages(client):
    """Village search does not return residents from other villages."""
    _create(client, village="Village A")
    _create(client, village="Village B")
    response = client.get("/api/search?query=Village+A&search_type=village")
    assert all(r["village"] == "Village A" for r in response.json())


# ── US-SR-04: Search by qualification field ──────────────────────────────────

def test_us_sr04_search_by_qualification(client):
    """Qualification search returns residents with a matching qualification name."""
    _create(client)
    response = client.get("/api/search?query=Software+Engineering&search_type=qualification")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_us_sr04_qualification_search_no_match(client):
    """Qualification search with no match returns empty list."""
    _create(client)
    response = client.get("/api/search?query=Underwater+Basket+Weaving&search_type=qualification")
    assert response.status_code == 200
    assert response.json() == []


# ── US-SR-05: View search results ────────────────────────────────────────────

def test_us_sr05_results_contain_required_fields(client):
    """Each search result contains id, first_name, last_name, and village."""
    _create(client)
    response = client.get("/api/search?query=Mpho&search_type=name")
    for result in response.json():
        for field in ("id", "first_name", "last_name", "village"):
            assert field in result


# ── US-SR-06: Handle no results ──────────────────────────────────────────────

def test_us_sr06_no_results_returns_empty_list_not_error(client):
    """No-match search returns 200 with an empty list."""
    response = client.get("/api/search?query=NoSuchPerson&search_type=name")
    assert response.status_code == 200
    assert response.json() == []


# ── US-SR-07: Validate empty search ──────────────────────────────────────────

def test_us_sr07_empty_query_returns_empty_list(client):
    """Empty query string returns an empty list without hitting the DB."""
    _create(client)
    response = client.get("/api/search?query=&search_type=name")
    assert response.status_code == 200
    assert response.json() == []


def test_us_sr07_whitespace_only_query_returns_empty_list(client):
    """Whitespace-only query is treated as empty."""
    _create(client)
    response = client.get("/api/search?query=   &search_type=name")
    assert response.status_code == 200
    assert response.json() == []


# ── US-SR-08: Handle search errors / unknown type ────────────────────────────

def test_us_sr08_unknown_search_type_returns_empty_list(client):
    """An unrecognised search_type returns an empty list, not a 500."""
    _create(client)
    response = client.get("/api/search?query=Mpho&search_type=unknown")
    assert response.status_code == 200
    assert response.json() == []


# ── Search by skill ───────────────────────────────────────────────────────────

def test_search_by_skill(client):
    """Skill search returns residents who have that skill."""
    _create(client)
    response = client.get("/api/search?query=Python&search_type=skill")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_search_by_skill_no_match(client):
    """Skill search with no match returns empty list."""
    _create(client)
    response = client.get("/api/search?query=COBOL&search_type=skill")
    assert response.status_code == 200
    assert response.json() == []
