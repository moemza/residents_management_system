from fastapi.testclient import TestClient
from app.main import app
from app.qualifications import get_all_qualifications

client = TestClient(app)

def test_get_qualifications():
    response = client.get("/qualifications/")
    assert response.status_code == 200

    data = response.json()
    expected = get_all_qualifications()
    
    # Check keys exist
    for key in ["types", "fields", "levels", "names"]:
        assert key in data

    # Check some actual values from qualifications.py
    assert "Information Technology" in data["fields"]
    assert "Certificate" in data["types"]
    assert "Networking" in data["names"]["Information Technology"]
    assert "NQF Level 5 (Higher Certificate)" in data["levels"]
    assert data == expected 
    