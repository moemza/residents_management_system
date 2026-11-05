"""Pagination contract tests for resident listing and search."""

from .conftest import RESIDENT_PAYLOAD


def _create(client, first_name):
    payload = {**RESIDENT_PAYLOAD, "first_name": first_name}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201
    return response.json()


def test_list_residents_reports_total_and_default_page(client):
    for name in ("One", "Two", "Three"):
        _create(client, name)

    response = client.get("/api/residents")
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "3"
    assert len(response.json()) == 3


def test_list_residents_honours_limit_and_offset(client):
    ids = [_create(client, name)["id"] for name in ("One", "Two", "Three")]

    response = client.get("/api/residents?limit=2&offset=1")
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "3"
    assert [resident["id"] for resident in response.json()] == ids[1:]


def test_list_residents_rejects_invalid_pagination(client):
    assert client.get("/api/residents?limit=0").status_code == 422
    assert client.get("/api/residents?limit=501").status_code == 422
    assert client.get("/api/residents?offset=-1").status_code == 422


def test_search_reports_total_and_honours_pagination(client):
    for name in ("Mpho One", "Mpho Two", "Mpho Three"):
        _create(client, name)

    response = client.get("/api/search?query=Mpho&search_type=name&limit=2&offset=0")
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "3"
    assert len(response.json()) == 2

    second_page = client.get("/api/search?query=Mpho&search_type=name&limit=2&offset=2")
    assert second_page.status_code == 200
    assert second_page.headers["X-Total-Count"] == "3"
    assert len(second_page.json()) == 1


def test_empty_search_reports_zero_total(client):
    response = client.get("/api/search?query=&search_type=name")
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "0"
