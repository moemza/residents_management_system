import json
import os
from fastapi.testclient import TestClient
from main import app, DATA_FILE

client = TestClient(app)

def test_form_submission_creates_resident():
    payload = {
        "full_name": "Mpho Mogowane",
        "national_id": "9001015009087",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "village_id": 1,
        "stand_number": "12A",
        "contact_number_1": "0821234567",
        "contact_number_2": "",
        "email": "mpho@example.com",
        "skills": "Python, FastAPI",
        "qualification_type": "Certificate",
        "qualification_field": "Information Technology",
        "qualification_level": "NQF Level 6 (Advanced Certificate / Diploma)",
        "qualification_name": "Software Engineering"
    }

    # Remove the data file first to ensure clean test
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

    response = client.post("/residents/form", data=payload, follow_redirects=False)
    assert response.status_code == 303  # Redirect after successful submission

    # Check that resident was saved in JSON file
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        assert len(data["residents"]) == 1
        assert data["residents"][0]["full_name"] == "Mpho Mogowane"
        assert data["residents"][0]["email"] == "mpho@example.com"
