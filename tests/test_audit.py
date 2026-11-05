"""Audit-trail tests using synthetic residents only."""

from .conftest import RESIDENT_PAYLOAD


def _create(client, **overrides):
    response = client.post("/api/residents", json={**RESIDENT_PAYLOAD, **overrides})
    assert response.status_code == 201
    return response.json()


def _audit(client, **params):
    response = client.get("/api/audit", params=params)
    assert response.status_code == 200
    return response


def test_create_writes_non_pii_audit_event(client):
    resident = _create(client)
    response = _audit(client)

    assert response.headers["x-total-count"] == "1"
    event = response.json()[0]
    assert event["action"] == "create"
    assert event["resident_id"] == resident["id"]
    assert event["actor"] == "test-admin"
    assert event["request_id"]
    assert event["detail"] is None
    assert "Mpho" not in str(event)


def test_update_records_changed_field_names_not_values(client):
    resident = _create(client)
    response = client.put(
        f"/api/residents/{resident['id']}",
        json={
            **RESIDENT_PAYLOAD,
            "email": "changed@example.com",
            "cellphone_no": "0839999999",
        },
    )
    assert response.status_code == 200

    event = _audit(client, action="update").json()[0]
    assert event["resident_id"] == resident["id"]
    assert "email" in event["detail"]
    assert "cellphone_no" in event["detail"]
    assert "changed@example.com" not in event["detail"]
    assert "0839999999" not in event["detail"]


def test_delete_event_survives_resident_deletion(client):
    resident = _create(client)
    assert client.delete(f"/api/residents/{resident['id']}").status_code == 204

    response = _audit(client, action="delete")
    assert response.headers["x-total-count"] == "1"
    event = response.json()[0]
    assert event["resident_id"] == resident["id"]
    assert event["action"] == "delete"


def test_audit_filters_and_paginates(client):
    first = _create(client, first_name="One")
    second = _create(client, first_name="Two")
    _create(client, first_name="Three")

    by_resident = _audit(client, resident_id=first["id"])
    assert by_resident.headers["x-total-count"] == "1"
    assert by_resident.json()[0]["resident_id"] == first["id"]

    page = _audit(client, limit=1, offset=1)
    assert page.headers["x-total-count"] == "3"
    assert len(page.json()) == 1
    assert page.json()[0]["resident_id"] == second["id"]

    assert _audit(client, action="create").headers["x-total-count"] == "3"


def test_audit_endpoint_requires_an_admin_session(anonymous_client):
    assert anonymous_client.get("/api/audit").status_code == 401


def test_admin_username_is_recorded_without_credentials(client):
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 201

    event = client.get("/api/audit").json()[0]
    assert event["actor"] == "test-admin"
    assert "test-only-password-123" not in str(event)
