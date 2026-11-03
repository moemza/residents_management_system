import sqlite3
from datetime import datetime

from app import database


def _create_synthetic_db(path):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE probe (value TEXT)")
    connection.execute("INSERT INTO probe VALUES ('synthetic-only')")
    connection.commit()
    connection.close()


def test_backup_disabled_creates_no_files(tmp_path, monkeypatch):
    source = tmp_path / "residents.db"
    backup_dir = tmp_path / "backups"
    _create_synthetic_db(source)

    monkeypatch.setattr(database, "DB_PATH", source)
    monkeypatch.setattr(database, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(database, "BACKUP_ENABLED", False)

    assert database.backup_database() is False
    assert not backup_dir.exists()


def test_backup_filename_does_not_overwrite_existing(tmp_path, monkeypatch):
    class FixedDateTime:
        @classmethod
        def now(cls):
            return datetime(2026, 1, 1, 0, 0, 0, 0)

    monkeypatch.setattr(database, "datetime", FixedDateTime)
    existing = tmp_path / "residents_backup_20260101_000000_000000.db"
    existing.write_bytes(b"synthetic")

    candidate = database._next_backup_path(tmp_path)

    assert candidate.name == "residents_backup_20260101_000000_000000_01.db"
    assert candidate != existing


def test_backup_retention_keeps_latest_ten(tmp_path, monkeypatch):
    source = tmp_path / "residents.db"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    _create_synthetic_db(source)

    # Synthetic older backups, named in the same sortable format.
    for index in range(12):
        (backup_dir / f"residents_backup_20200101_000000_{index:06d}.db").write_bytes(b"synthetic")

    monkeypatch.setattr(database, "DB_PATH", source)
    monkeypatch.setattr(database, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(database, "BACKUP_ENABLED", True)

    assert database.backup_database() is True

    backups = sorted(backup_dir.glob("residents_backup_*.db"))
    assert len(backups) == 10
    assert backups[-1].name.startswith("residents_backup_")
    assert backups[-1].stat().st_size == source.stat().st_size


def test_backup_retention_is_configurable(tmp_path, monkeypatch):
    source = tmp_path / "residents.db"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    _create_synthetic_db(source)

    for index in range(4):
        (backup_dir / f"residents_backup_20200101_000000_{index:06d}.db").write_bytes(b"synthetic")

    monkeypatch.setattr(database, "DB_PATH", source)
    monkeypatch.setattr(database, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(database, "BACKUP_ENABLED", True)
    monkeypatch.setattr(database, "BACKUP_RETENTION", 2)

    assert database.backup_database() is True
    assert len(list(backup_dir.glob("residents_backup_*.db"))) == 2
