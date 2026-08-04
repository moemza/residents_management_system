import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Use an in-memory SQLite DB for tests
TEST_DB_URL = "sqlite:///./database/test_residents.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


client = TestClient(app)

RESIDENT_PAYLOAD = {
    "first_name": "Mpho",
    "last_name": "Mogowane",
    "dob": "1990-01-01",
    "gender": "Male",
    "village": "Village A",
    "cellphone_no": "0821234567",
    "cellphone_no2": None,
    "email": "mpho@example.com",
    "qualifications": [
        {"institution": "UNISA", "name": "Software Engineering", "type": "Degree", "level": "NQF Level 7 (Bachelor's Degree / Advanced Diploma)", "year": "2015"}
    ],
    "experiences": [
        {"company": "Acme Corp", "position": "Developer", "years": "3"}
    ],
    "skills": [
        {"name": "Python"}, {"name": "FastAPI"}
    ],
}


def test_create_resident():
    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Mpho"
    assert data["last_name"] == "Mogowane"
    assert data["email"] == "mpho@example.com"
    assert len(data["qualifications"]) == 1
    assert len(data["skills"]) == 2


def test_get_resident():
    created = client.post("/api/residents", json=RESIDENT_PAYLOAD).json()
    response = client.get(f"/api/residents/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_list_residents():
    client.post("/api/residents", json=RESIDENT_PAYLOAD)
    response = client.get("/api/residents")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_update_resident():
    created = client.post("/api/residents", json=RESIDENT_PAYLOAD).json()
    updated_payload = {**RESIDENT_PAYLOAD, "cellphone_no": "0839999999", "skills": [{"name": "Django"}]}
    response = client.put(f"/api/residents/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cellphone_no"] == "0839999999"
    assert data["skills"][0]["name"] == "Django"


def test_delete_resident():
    created = client.post("/api/residents", json=RESIDENT_PAYLOAD).json()
    response = client.delete(f"/api/residents/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/residents/{created['id']}").status_code == 404


def test_get_nonexistent_resident():
    response = client.get("/api/residents/99999")
    assert response.status_code == 404
