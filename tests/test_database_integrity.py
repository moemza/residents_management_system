"""Database integrity tests: indexes, foreign-key enforcement, backups."""

import sqlite3

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app import database
from app.models import Qualification
from .conftest import TestingSession, engine


def test_foreign_key_pragma_is_enabled(client):
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_search_and_foreign_key_indexes_exist(client):
    inspector = inspect(engine)
    resident_indexes = {index["name"] for index in inspector.get_indexes("residents")}
    assert {
        "ix_residents_first_name",
        "ix_residents_last_name",
        "ix_residents_village",
    } <= resident_indexes

    qualification_indexes = {
        index["name"] for index in inspector.get_indexes("qualifications")
    }
    assert {"ix_qualifications_name", "ix_qualifications_resident_id"} <= qualification_indexes

    skill_indexes = {index["name"] for index in inspector.get_indexes("skills")}
    assert {"ix_skills_name", "ix_skills_resident_id"} <= skill_indexes


def test_orphan_child_row_is_rejected(client):
    session = TestingSession()
    try:
        session.add(
            Qualification(
                institution="Synthetic",
                name="Synthetic",
                type="Degree",
                level="NQF Level 7",
                year="2020",
                resident_id=999999,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


def test_backup_is_readable_and_integrity_checked(tmp_path, monkeypatch):
    source = tmp_path / "residents.db"
    backup_dir = tmp_path / "backups"
    connection = sqlite3.connect(source)
    connection.execute("CREATE TABLE probe (value TEXT)")
    connection.execute("INSERT INTO probe VALUES ('synthetic-only')")
    connection.commit()
    connection.close()

    monkeypatch.setattr(database, "DB_PATH", source)
    monkeypatch.setattr(database, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(database, "BACKUP_ENABLED", True)

    assert database.backup_database() is True
    backup_file = next(backup_dir.glob("residents_backup_*.db"))

    backup_connection = sqlite3.connect(backup_file)
    try:
        assert backup_connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert backup_connection.execute("SELECT value FROM probe").fetchone()[0] == "synthetic-only"
    finally:
        backup_connection.close()


def test_integrity_check_accepts_a_valid_database(tmp_path, monkeypatch):
    database_file = tmp_path / "residents.db"
    connection = sqlite3.connect(database_file)
    connection.execute("CREATE TABLE probe (value TEXT)")
    connection.commit()
    connection.close()

    monkeypatch.setattr(database, "DB_PATH", database_file)
    assert database.verify_database_integrity() is True


def test_integrity_check_rejects_a_corrupt_database(tmp_path, monkeypatch):
    database_file = tmp_path / "residents.db"
    database_file.write_text("this is not a sqlite database", encoding="utf-8")

    monkeypatch.setattr(database, "DB_PATH", database_file)
    assert database.verify_database_integrity() is False


def test_integrity_check_treats_a_missing_database_as_healthy(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "missing.db")
    assert database.verify_database_integrity() is True


def test_invalid_source_is_not_reported_as_a_backup(tmp_path, monkeypatch):
    source = tmp_path / "residents.db"
    source.write_text("not a sqlite database", encoding="utf-8")
    backup_dir = tmp_path / "backups"

    monkeypatch.setattr(database, "DB_PATH", source)
    monkeypatch.setattr(database, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(database, "BACKUP_ENABLED", True)

    assert database.backup_database() is False
    assert list(backup_dir.glob("residents_backup_*.db")) == []
