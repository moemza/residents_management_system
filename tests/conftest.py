import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite:///./database/test_residents.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


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
        {
            "institution": "UNISA",
            "name": "Software Engineering",
            "type": "Degree",
            "level": "NQF Level 7 (Bachelor's Degree / Advanced Diploma)",
            "year": "2015",
        }
    ],
    "experiences": [{"company": "Acme Corp", "position": "Developer", "years": "3"}],
    "skills": [{"name": "Python"}, {"name": "FastAPI"}],
}
