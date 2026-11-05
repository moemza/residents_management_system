from .conftest import RESIDENT_PAYLOAD


def test_create_resident(client):
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Mpho"
    assert data["last_name"] == "Mogowane"
    assert data["email"] == "mpho@example.com"
    assert len(data["qualifications"]) == 1
    assert len(data["skills"]) == 2


def test_get_resident(client):
    created = client.post("/api/residents", json=RESIDENT_PAYLOAD).json()
    response = client.get(f"/api/residents/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_list_residents(client):
    client.post("/api/residents", json=RESIDENT_PAYLOAD)
    response = client.get("/api/residents")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_update_resident(client):
    created = client.post("/api/residents", json=RESIDENT_PAYLOAD).json()
    updated_payload = {**RESIDENT_PAYLOAD, "cellphone_no": "0839999999", "skills": [{"name": "Django"}]}
    response = client.put(f"/api/residents/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cellphone_no"] == "0839999999"
    assert data["skills"][0]["name"] == "Django"


def test_delete_resident(client):
    created = client.post("/api/residents", json=RESIDENT_PAYLOAD).json()
    response = client.delete(f"/api/residents/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/residents/{created['id']}").status_code == 404


def test_get_nonexistent_resident(client):
    response = client.get("/api/residents/99999")
    assert response.status_code == 404
