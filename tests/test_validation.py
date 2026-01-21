from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_required_fields_missing():
    payload = {
        "full_name": "",
        "national_id": "",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "village_id": 1,
        "stand_number": "12A",
        "contact_number_1": "0821234567",
        "qualification_type": "Certificate",
        "qualification_field": "Information Technology",
        "qualification_level": "NQF Level 6 (Advanced Certificate / Diploma)",
        "qualification_name": "Software Engineering"
    }

    response = client.post("/residents/form", data=payload, follow_redirects=False)
    # Should redirect anyway, but data should not be stored if validation fails
    # You can improve this by adding Pydantic validation to form submission
    assert response.status_code == 303
    