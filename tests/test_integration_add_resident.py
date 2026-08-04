"""
Integration tests for Add Resident page user stories (US-01 – US-07).
"""
from datetime import date, timedelta
from .conftest import RESIDENT_PAYLOAD


# ── US-01: Capture basic personal information ─────────────────────────────────

def test_us01_required_fields_missing_returns_422(client):
    """First name, last name, dob, gender are required."""
    response = client.post("/api/residents", json={})
    assert response.status_code == 422


def test_us01_future_dob_rejected(client):
    """Date of birth cannot be a future date — API must reject it."""
    future = (date.today() + timedelta(days=1)).isoformat()
    payload = {**RESIDENT_PAYLOAD, "dob": future}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 422


def test_us01_valid_personal_details_accepted(client):
    """Valid personal details are accepted and persisted."""
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Mpho"
    assert data["last_name"] == "Mogowane"
    assert data["gender"] == "Male"
    assert data["dob"] == "1990-01-01"


# ── US-02: Assign resident to a village ──────────────────────────────────────

def test_us02_villages_endpoint_returns_list(client):
    """GET /api/villages returns a non-empty list for the village dropdown."""
    response = client.get("/api/villages")
    assert response.status_code == 200
    villages = response.json()
    assert isinstance(villages, list)
    assert len(villages) > 0


def test_us02_village_required(client):
    """Village is required — omitting it returns 422."""
    payload = {k: v for k, v in RESIDENT_PAYLOAD.items() if k != "village"}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 422


def test_us02_resident_saved_with_village(client):
    """Resident is saved with the selected village."""
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.json()["village"] == "Village A"


# ── US-03: Capture contact details ───────────────────────────────────────────

def test_us03_primary_cellphone_required(client):
    """Primary cellphone is required."""
    payload = {k: v for k, v in RESIDENT_PAYLOAD.items() if k != "cellphone_no"}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 422


def test_us03_secondary_cellphone_optional(client):
    """Resident can be created without a secondary cellphone."""
    payload = {**RESIDENT_PAYLOAD, "cellphone_no2": None}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201
    assert response.json()["cellphone_no2"] is None


def test_us03_email_optional(client):
    """Email is optional — omitting it is valid."""
    payload = {**RESIDENT_PAYLOAD, "email": None}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201


def test_us03_invalid_email_rejected(client):
    """Invalid email format returns 422."""
    payload = {**RESIDENT_PAYLOAD, "email": "not-an-email"}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 422


def test_us03_valid_email_accepted(client):
    """Valid email is stored correctly."""
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.json()["email"] == "mpho@example.com"


# ── US-04: Add education records ─────────────────────────────────────────────

def test_us04_qualifications_endpoint_returns_required_keys(client):
    """GET /api/qualifications returns types, fields, levels, names."""
    response = client.get("/api/qualifications")
    assert response.status_code == 200
    for key in ("types", "fields", "levels", "names"):
        assert key in response.json()


def test_us04_resident_saved_with_qualifications(client):
    """Qualifications are persisted and returned with the resident."""
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    quals = response.json()["qualifications"]
    assert len(quals) == 1
    assert quals[0]["institution"] == "UNISA"
    assert quals[0]["name"] == "Software Engineering"


def test_us04_resident_saved_without_qualifications(client):
    """Qualifications list can be empty."""
    payload = {**RESIDENT_PAYLOAD, "qualifications": []}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201
    assert response.json()["qualifications"] == []


# ── US-05: Add work experience records ───────────────────────────────────────

def test_us05_resident_saved_with_experience(client):
    """Work experience entries are persisted and returned."""
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    exps = response.json()["experiences"]
    assert len(exps) == 1
    assert exps[0]["company"] == "Acme Corp"
    assert exps[0]["position"] == "Developer"


def test_us05_resident_saved_without_experience(client):
    """Experience list can be empty."""
    payload = {**RESIDENT_PAYLOAD, "experiences": []}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201
    assert response.json()["experiences"] == []


# ── US-06: Add skills ────────────────────────────────────────────────────────

def test_us06_resident_saved_with_skills(client):
    """Skills are persisted and returned."""
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    skills = response.json()["skills"]
    assert len(skills) == 2
    names = {s["name"] for s in skills}
    assert names == {"Python", "FastAPI"}


def test_us06_resident_saved_without_skills(client):
    """Skills list can be empty."""
    payload = {**RESIDENT_PAYLOAD, "skills": []}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201
    assert response.json()["skills"] == []


# ── US-07: Submit the form ───────────────────────────────────────────────────

def test_us07_successful_create_returns_201_with_id(client):
    """POST /api/residents returns 201 and the created resident with an id."""
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert isinstance(data["id"], int)


def test_us07_created_resident_retrievable(client):
    """After creation the resident can be fetched by id (redirect target works)."""
    created_id = client.post("/api/residents", json=RESIDENT_PAYLOAD).json()["id"]
    response = client.get(f"/api/residents/{created_id}")
    assert response.status_code == 200
    assert response.json()["id"] == created_id


def test_us07_xss_input_is_sanitized(client):
    """String inputs containing HTML are escaped before persistence."""
    payload = {**RESIDENT_PAYLOAD, "first_name": "<script>alert(1)</script>"}
    response = client.post("/api/residents", json=payload)
    assert response.status_code == 201
    assert "<script>" not in response.json()["first_name"]
