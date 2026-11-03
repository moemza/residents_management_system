import atexit
import os
import pathlib
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure the application before importing it. Tests must never create,
# copy, or rotate the configured application database or its backups.
TEST_DB_DIR = pathlib.Path(tempfile.mkdtemp(prefix="residents-test-"))
TEST_DB_PATH = TEST_DB_DIR / "test_residents.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["RESIDENTS_DB_PATH"] = str(TEST_DB_PATH)
os.environ["RESIDENTS_BACKUP_DIR"] = str(TEST_DB_DIR / "backups")
os.environ["RESIDENTS_BACKUP_ENABLED"] = "false"
os.environ["RESIDENTS_COOKIE_SECURE"] = "false"
# Rate limiting is disabled for the suite; dedicated tests enable it explicitly.
os.environ["RESIDENTS_RATE_LIMIT_PER_MINUTE"] = "0"
# The integrity check is exercised directly; skipping it per test keeps the
# suite fast without weakening the production default.
os.environ["RESIDENTS_DB_INTEGRITY_CHECK"] = "false"

atexit.register(shutil.rmtree, TEST_DB_DIR, ignore_errors=True)

from app.main import app  # noqa: E402  (must follow test environment setup)
from app.database import Base, get_db  # noqa: E402
from app.auth import hash_password  # noqa: E402
from app.models import AdminUser  # noqa: E402
from app.rate_limit import limiter  # noqa: E402

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def anonymous_client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    limiter.reset()
    with TestingSession() as db:
        db.add(
            AdminUser(
                username="test-admin",
                password_hash=hash_password("test-only-password-123"),
                role="admin",
            )
        )
        db.commit()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(anonymous_client):
    response = anonymous_client.post(
        "/api/auth/login",
        json={"username": "test-admin", "password": "test-only-password-123"},
    )
    assert response.status_code == 200
    anonymous_client.headers.update({"X-CSRF-Token": response.json()["csrf_token"]})
    return anonymous_client


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
