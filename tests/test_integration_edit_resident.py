"""
Integration tests for Edit Resident page user stories (US-ER-01 – US-ER-06).
"""
from .conftest import RESIDENT_PAYLOAD


def _create(client):
    return client.post("/api/residents", json=RESIDENT_PAYLOAD).json()


# ── US-ER-01: Pre-populate form with existing data ───────────────────────────

def test_user_er01_get_resident_returns_all_fields(client):
    """GET /api/residents/{id} returns every field the edit form needs."""
    resident = _create(client)
    response = client.get(f"/api/residents/{resident['id']}")
    assert response.status_code == 200
    data = response.json()
    for field in ("first_name", "last_name", "dob", "gender", "village",
                  "cellphone_no", "email", "qualifications", "experiences", "skills"):
        assert field in data


def test_user_er01_unknown_resident_returns_404(client):
    """GET /api/residents/{id} for a missing resident returns 404."""
    response = client.get("/api/residents/99999")
    assert response.status_code == 404


# ── US-ER-02: Read-only identity fields are still submitted ──────────────────

def test_user_er02_identity_fields_preserved_on_update(client):
    """PUT payload includes identity fields; they are stored unchanged."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "cellphone_no": "0839999999"}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Mpho"
    assert data["last_name"] == "Mogowane"
    assert data["dob"] == "1990-01-01"
    assert data["gender"] == "Male"
    assert data["village"] == "Village A"


# ── US-ER-03: Edit contact details ───────────────────────────────────────────

def test_user_er03_update_primary_cellphone(client):
    """Primary cellphone can be updated."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "cellphone_no": "0839999999"}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert response.json()["cellphone_no"] == "0839999999"


def test_user_er03_primary_cellphone_still_required_on_update(client):
    """PUT without primary cellphone returns 422."""
    resident = _create(client)
    payload = {k: v for k, v in RESIDENT_PAYLOAD.items() if k != "cellphone_no"}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert response.status_code == 422


def test_user_er03_update_email(client):
    """Email can be updated to a new valid address."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "email": "new@example.com"}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert response.json()["email"] == "new@example.com"


def test_user_er03_invalid_email_rejected_on_update(client):
    """Invalid email on PUT returns 422."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "email": "bad-email"}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert response.status_code == 422


# ── US-ER-04: Edit existing records ─────────────────────────────────────────

def test_user_er04_update_qualification(client):
    """An existing qualification can be replaced with updated values."""
    resident = _create(client)
    updated_qual = [{
        "institution": "UJ",
        "name": "Data Science",
        "type": "Degree",
        "level": "NQF Level 7 (Bachelor's Degree / Advanced Diploma)",
        "year": "2020",
    }]
    payload = {**RESIDENT_PAYLOAD, "qualifications": updated_qual}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    quals = response.json()["qualifications"]
    assert len(quals) == 1
    assert quals[0]["institution"] == "UJ"
    assert quals[0]["name"] == "Data Science"


def test_user_er04_update_experience(client):
    """An existing experience entry can be replaced."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "experiences": [{"company": "NewCo", "position": "Lead", "years": "5"}]}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    exps = response.json()["experiences"]
    assert exps[0]["company"] == "NewCo"


# ── US-ER-05: Add and remove rows ────────────────────────────────────────────

def test_user_er05_add_extra_skill_on_update(client):
    """Additional skills can be added during an update."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "skills": [{"name": "Python"}, {"name": "FastAPI"}, {"name": "Django"}]}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert len(response.json()["skills"]) == 3


def test_user_er05_remove_all_skills_on_update(client):
    """All skills can be removed — full replacement semantics."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "skills": []}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert response.json()["skills"] == []


def test_user_er05_remove_all_qualifications_on_update(client):
    """All qualifications can be removed."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "qualifications": []}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert response.json()["qualifications"] == []


# ── US-ER-06: Submit changes ─────────────────────────────────────────────────

def test_user_er06_successful_update_returns_200(client):
    """PUT /api/residents/{id} returns 200 with the updated resident."""
    resident = _create(client)
    payload = {**RESIDENT_PAYLOAD, "cellphone_no": "0711112222"}
    response = client.put(f"/api/residents/{resident['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["cellphone_no"] == "0711112222"


def test_user_er06_update_nonexistent_resident_returns_404(client):
    """PUT on a missing resident returns 404."""
    response = client.put("/api/residents/99999", json=RESIDENT_PAYLOAD)
    assert response.status_code == 404


def test_user_er06_delete_resident(client):
    """DELETE /api/residents/{id} removes the resident (204 then 404)."""
    resident = _create(client)
    assert client.delete(f"/api/residents/{resident['id']}").status_code == 204
    assert client.get(f"/api/residents/{resident['id']}").status_code == 404
