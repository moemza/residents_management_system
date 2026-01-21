from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_villages():
    response = client.get("/villages/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "id" in data[0]
    assert "name" in data[0]
