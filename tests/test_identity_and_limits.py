"""Identity-field immutability and validation-limit tests."""

from .conftest import RESIDENT_PAYLOAD


def _create(client, **overrides):
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, **overrides})
    assert response.status_code == 201
    return response.json()


def test_identity_change_returns_409(client):
    resident = _create(client)
    response = client.put(
        f"/api/residents/{resident['id']}",
        json={**RESIDENT_PAYLOAD, "first_name": "Changed"},
    )
    assert response.status_code == 409
    assert "first_name" in response.json()["detail"]


def test_multiple_identity_changes_are_reported(client):
    resident = _create(client)
    response = client.put(
        f"/api/residents/{resident['id']}",
        json={
            **RESIDENT_PAYLOAD,
            "first_name": "Changed",
            "village": "Village B",
            "gender": "Female",
        },
    )
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "first_name" in detail
    assert "village" in detail
    assert "gender" in detail


def test_contact_and_child_updates_are_allowed(client):
    resident = _create(client)
    response = client.put(
        f"/api/residents/{resident['id']}",
        json={
            **RESIDENT_PAYLOAD,
            "cellphone_no": "0839999999",
            "email": "new@example.com",
            "skills": [{"name": "Django"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["cellphone_no"] == "0839999999"
    assert response.json()["skills"][0]["name"] == "Django"


def test_identity_fields_at_exact_limit_are_accepted(client):
    name = "A" * 100
    resident = _create(client, first_name=name)
    assert resident["first_name"] == name


def test_fields_above_limit_are_rejected(client):
    assert client.post(
        "/api/residents", json={**RESIDENT_PAYLOAD, "first_name": "A" * 101}
    ).status_code == 422
    assert client.post(
        "/api/residents", json={**RESIDENT_PAYLOAD, "cellphone_no": "1" * 31}
    ).status_code == 422


def test_blank_child_rows_are_rejected(client):
    assert client.post(
        "/api/residents",
        json={**RESIDENT_PAYLOAD, "qualifications": [{"institution": "", "name": "X", "type": "Y", "level": "Z", "year": "2020"}]},
    ).status_code == 422
    assert client.post(
        "/api/residents",
        json={**RESIDENT_PAYLOAD, "experiences": [{"company": "   ", "position": "X", "years": "1"}]},
    ).status_code == 422
    assert client.post(
        "/api/residents",
        json={**RESIDENT_PAYLOAD, "skills": [{"name": ""}]},
    ).status_code == 422


def test_too_many_child_rows_are_rejected(client):
    skills = [{"name": f"Skill {index}"} for index in range(51)]
    assert client.post(
        "/api/residents", json={**RESIDENT_PAYLOAD, "skills": skills}
    ).status_code == 422


def test_markup_in_child_rows_is_rejected(client):
    assert client.post(
        "/api/residents",
        json={**RESIDENT_PAYLOAD, "skills": [{"name": "<script>alert(1)</script>"}]},
    ).status_code == 422
