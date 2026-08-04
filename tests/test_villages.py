from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_villages_returns_list():
    response = client.get("/api/villages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_villages_are_strings():
    response = client.get("/api/villages")
    for village in response.json():
        assert isinstance(village, str)
