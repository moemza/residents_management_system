from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_app_root_redirect():
    response = client.get("/")
    assert response.status_code == 200 or response.status_code == 307  # Redirect
    if response.status_code == 307:
        assert response.headers["location"] == "/form"