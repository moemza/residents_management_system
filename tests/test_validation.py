def test_missing_required_fields_returns_422(client):
    response = client.post("/api/residents", json={"first_name": "Only"})
    assert response.status_code == 422


def test_invalid_email_returns_422(client):
    payload = {
        "first_name": "Test", "last_name": "User", "dob": "1990-01-01",
        "gender": "Male", "village": "Village A", "cellphone_no": "0821234567",
        "email": "not-an-email",
        "qualifications": [], "experiences": [], "skills": [],
    }
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 422


def test_invalid_date_returns_422(client):
    payload = {
        "first_name": "Test", "last_name": "User", "dob": "not-a-date",
        "gender": "Male", "village": "Village A", "cellphone_no": "0821234567",
        "qualifications": [], "experiences": [], "skills": [],
    }
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 422


def test_valid_resident_without_optional_fields(client):
    payload = {
        "first_name": "Test", "last_name": "User", "dob": "1995-06-15",
        "gender": "Female", "village": "Village B", "cellphone_no": "0711112222",
        "qualifications": [], "experiences": [], "skills": [],
    }
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201


def test_search_empty_query_returns_empty_list(client):
    response = client.get("/api/search?query=&search_type=name")
    assert response.status_code == 200
    assert response.json() == []
