"""Qualification field search and LIKE escaping tests."""

from .conftest import RESIDENT_PAYLOAD


def _create(client, qualification_name="Software Engineering"):
    payload = {
        **RESIDENT_PAYLOAD,
        "qualifications": [
            {
                "institution": "Synthetic University",
                "name": qualification_name,
                "type": "Degree",
                "level": "NQF Level 7 (Bachelor's Degree / Advanced Diploma)",
                "year": "2020",
            }
        ],
    }
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201
    return response.json()


def test_qualification_field_maps_to_known_names(client):
    _create(client)
    response = client.get(
        "/api/search?query=Information+Technology&search_type=qualification"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_qualification_name_search_still_works(client):
    _create(client)
    response = client.get(
        "/api/search?query=Software+Engineering&search_type=qualification"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_unknown_qualification_field_returns_empty(client):
    _create(client)
    response = client.get(
        "/api/search?query=Underwater+Basket+Weaving&search_type=qualification"
    )
    assert response.status_code == 200
    assert response.json() == []


def test_like_wildcards_are_treated_literally(client):
    _create(client)
    for term in ("%", "_", "%%", "__"):
        response = client.get(f"/api/search?query={term}&search_type=name")
        assert response.status_code == 200
        assert response.json() == [], f"Wildcard {term!r} matched unexpectedly"
