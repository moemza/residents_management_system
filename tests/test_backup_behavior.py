"""Pre-write backup failure behaviour."""

from app import database
from .conftest import RESIDENT_PAYLOAD


def test_backup_failure_aborts_write_when_required(client, monkeypatch):
    monkeypatch.setattr(database, "backup_database", lambda: False)
    monkeypatch.setattr(database, "BACKUP_ENABLED", True)
    monkeypatch.setattr(database, "BACKUP_REQUIRED", True)

    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database backup failed; the write was aborted"
    }
    assert client.get("/api/residents").json() == []


def test_backup_failure_is_best_effort_by_default(client, monkeypatch):
    monkeypatch.setattr(database, "backup_database", lambda: False)
    monkeypatch.setattr(database, "BACKUP_ENABLED", True)
    monkeypatch.setattr(database, "BACKUP_REQUIRED", False)

    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 201


def test_required_backup_is_ignored_when_backups_are_disabled(client, monkeypatch):
    monkeypatch.setattr(database, "backup_database", lambda: False)
    monkeypatch.setattr(database, "BACKUP_ENABLED", False)
    monkeypatch.setattr(database, "BACKUP_REQUIRED", True)

    response = client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert response.status_code == 201
