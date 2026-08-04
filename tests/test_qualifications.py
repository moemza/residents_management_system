from fastapi.testclient import TestClient
from app.main import app
from app.qualifications import get_all_qualifications

client = TestClient(app)


def test_get_qualifications_returns_all_keys():
    response = client.get("/api/qualifications")
    assert response.status_code == 200
    data = response.json()
    for key in ("types", "fields", "levels", "names"):
        assert key in data


def test_qualifications_content():
    response = client.get("/api/qualifications")
    data = response.json()
    assert "Information Technology" in data["fields"]
    assert "Certificate" in data["types"]
    assert "NQF Level 5 (Higher Certificate)" in data["levels"]
    assert "Networking" in data["names"]["Information Technology"]


def test_qualifications_matches_source():
    response = client.get("/api/qualifications")
    assert response.json() == get_all_qualifications()
