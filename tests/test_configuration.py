import pytest

from app import auth, database
from app.main import _cors_origins


def test_test_environment_uses_isolated_database():
    """Tests must never use the repository's configured application database."""
    assert database.BACKUP_ENABLED is False
    assert database.DB_PATH != database.DEFAULT_DB_PATH
    assert database.DB_PATH.name == "test_residents.db"
    assert "residents-test-" in str(database.DB_PATH)
    assert database.BACKUP_DIR.name == "backups"
    assert str(database.DB_PATH) in database.SQLALCHEMY_DATABASE_URL


def test_test_environment_uses_insecure_cookies_only_for_local_tests():
    """The test client uses HTTP, unlike production's HTTPS-only cookie default."""
    assert auth.cookie_secure() is False


def test_cors_origins_default_to_local_vite(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert _cors_origins() == ["http://localhost:5173"]


def test_cors_origins_accept_comma_separated_values(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://one.example, https://two.example")
    assert _cors_origins() == ["https://one.example", "https://two.example"]


def test_cors_origins_reject_wildcard_with_credentialed_sessions(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://trusted.example, *")
    with pytest.raises(ValueError, match="explicit trusted origins"):
        _cors_origins()
