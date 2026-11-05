"""Combined resident filtering, deterministic sorting, and page-boundary tests."""

from .conftest import RESIDENT_PAYLOAD


def _create(client, *, first_name, last_name, village, qualifications=None, skills=None):
    payload = {
        **RESIDENT_PAYLOAD,
        "first_name": first_name,
        "last_name": last_name,
        "village": village,
        "qualifications": qualifications if qualifications is not None else [],
        "skills": skills if skills is not None else [],
    }
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _qualification(name):
    return {
        "institution": "Synthetic College",
        "name": name,
        "type": "Certificate",
        "level": "Level 4",
        "year": "2022",
    }


def test_combined_filters_use_and_semantics_and_distinct_totals(client):
    matching = _create(
        client,
        first_name="Mpho",
        last_name="Dube",
        village="North Ward",
        qualifications=[_qualification("Computer Science"), _qualification("Web Development")],
        skills=[{"name": "Python"}, {"name": "Python"}],
    )
    _create(
        client,
        first_name="Mpho",
        last_name="Other",
        village="South Ward",
        qualifications=[_qualification("Computer Science")],
        skills=[{"name": "Python"}],
    )
    _create(
        client,
        first_name="Other",
        last_name="Someone",
        village="North Ward",
        qualifications=[_qualification("Computer Science")],
        skills=[{"name": "Python"}],
    )

    response = client.get(
        "/api/residents",
        params={
            "name": "MPH",
            "village": "north",
            "qualification": "Information Technology",
            "skill": "pyth",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "1"
    assert [resident["id"] for resident in response.json()] == [matching["id"]]


def test_filters_match_names_villages_qualification_names_and_skills(client):
    by_last = _create(
        client,
        first_name="Thato",
        last_name="Mogowane",
        village="Upper Makhado",
        qualifications=[_qualification("Software Engineering")],
        skills=[{"name": "Data Analysis"}],
    )
    _create(
        client,
        first_name="Mogowane",
        last_name="Other",
        village="Lower Makhado",
        qualifications=[_qualification("Software Engineering")],
        skills=[{"name": "Data Analysis"}],
    )

    response = client.get(
        "/api/residents?name=gow&village=upper&qualification=software+engineering&skill=analysis"
    )
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "1"
    assert response.json()[0]["id"] == by_last["id"]


def test_sorting_is_stable_and_resident_id_breaks_name_ties(client):
    first = _create(client, first_name="Alex", last_name="Same", village="V1")
    second = _create(client, first_name="Alex", last_name="Same", village="V2")
    third = _create(client, first_name="Bea", last_name="Same", village="V3")

    ascending = client.get("/api/residents?sort_by=first_name&sort_order=asc")
    descending = client.get("/api/residents?sort_by=first_name&sort_order=desc")

    assert [row["id"] for row in ascending.json()] == [first["id"], second["id"], third["id"]]
    assert [row["id"] for row in descending.json()] == [third["id"], first["id"], second["id"]]


def test_pagination_reports_filtered_total_and_empty_page(client):
    for name in ("Mpho One", "Mpho Two", "Mpho Three"):
        _create(client, first_name=name, last_name="Resident", village="Village A")

    past_end = client.get("/api/residents?name=mpho&limit=2&offset=8")
    no_match = client.get("/api/residents?name=no-such-resident")

    assert past_end.status_code == 200
    assert past_end.json() == []
    assert past_end.headers["X-Total-Count"] == "3"
    assert no_match.json() == []
    assert no_match.headers["X-Total-Count"] == "0"


def test_filter_wildcards_are_matched_literally(client):
    resident = _create(client, first_name="100% Match", last_name="Resident", village="Village A")

    literal_percent = client.get("/api/residents?name=%25")
    wildcard_underscore = client.get("/api/residents?name=_")

    assert [row["id"] for row in literal_percent.json()] == [resident["id"]]
    assert wildcard_underscore.json() == []


def test_invalid_filter_and_sort_parameters_are_rejected(client):
    assert client.get("/api/residents?sort_by=cellphone_no").status_code == 422
    assert client.get("/api/residents?sort_order=random").status_code == 422
    assert client.get(f"/api/residents?name={'x' * 201}").status_code == 422
    assert client.get("/api/residents?limit=501").status_code == 422


def test_filters_and_reference_data_remain_admin_only(anonymous_client):
    assert anonymous_client.get("/api/residents?name=private").status_code == 401
    assert anonymous_client.get("/api/villages").status_code == 401
    assert anonymous_client.get("/api/qualifications").status_code == 401
